"""
The sandbox for code that MIA did not write (ui/REQUIREMENTS_CORE.md 12.2, HC2): model-written verification scripts and, later, anything else that has to run.

The wall (what keeps a hostile script away from the machine) is made of operating system features, not of Python:
  - bubblewrap: new user, pid, ipc, uts, cgroup and **network** namespaces; the script sees only the Python standard library (read-only), an empty temporary directory of limited size
    and its own input; no home directory, no /etc, no project files, no environment, no network (not even this machine's localhost: it has an empty network of its own);
  - a seccomp filter: no new processes (fork, vfork, clone without CLONE_THREAD, clone3), no ptrace, no mount, no io_uring, no bpf, no kernel modules, no keyring ... ;
  - resource limits inside (address space, CPU time, file size, open files) and a wall-clock timeout from outside that kills the whole sandbox;
  - output caps: what the script prints, the size of the result and of files.
On top of the wall come two convenience layers that give clear messages: an AST policy (check_script: allowed imports, no open/eval/exec, no dunder tricks) and a restricted namespace
in the runner. They are NOT the boundary and can be bypassed; the wall holds anyway (tests/test_sandbox.py tests the wall with the policy switched off).

If no working sandbox exists (no bubblewrap, user namespaces forbidden), `available` is False and run() refuses: the feature is off, never weakened.
"""
import ast
import hashlib
import json
import os
import platform
import secrets
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
MARK = "\x01MIA\x01"
REQUEST = b"\x01MIA-REQ\x01"
ANSWER = b"\x01MIA-RES\x01"
MAX_REQUEST_LINE = 8192
MAX_SCRIPT_CHARS = 8000

ALLOWED_MODULES = ("math", "statistics", "fractions", "decimal", "datetime", "calendar", "re", "json", "itertools", "collections", "string", "functools", "operator", "heapq",
                   "bisect", "textwrap", "unicodedata", "csv", "base64", "hashlib", "html", "urllib.parse", "typing", "copy", "numbers", "enum")
FORBIDDEN_NAMES = {"open", "exec", "eval", "compile", "__import__", "input", "breakpoint", "globals", "locals", "vars", "getattr", "setattr", "delattr", "help", "exit", "quit",
                   "memoryview", "__builtins__", "__loader__", "__spec__"}
READ_ONLY_NAMES = {"data", "web"}          # the input of the script: a script that retypes it (and the claim's numbers with it) does not check the real data
FORBIDDEN_ATTRIBUTES = {"gi_frame", "gi_code", "cr_frame", "cr_code", "ag_frame", "ag_code", "f_globals", "f_locals", "f_builtins", "f_back", "f_code", "tb_frame", "tb_next",
                        "func_globals", "mro"}


class SandboxUnavailable(Exception):
    pass


SCRIPT_GUIDE = """Write a short Python script. It has these names: `data` (the input, parsed JSON; read it, never retype, reassign or change it) and, only if web access was granted, `web` (`web.get(url)` returns the page text, `web.search(query)` returns results).
Allowed imports: %s. There is no file access, no network, no other module. The script must set `result` to JSON data. For a check, `result` is
{"holds": true or false, "values": {the numbers and facts the script used}, "explanation": "one sentence"}. Print nothing else that matters.""" % ", ".join(ALLOWED_MODULES)


# --- the policy: clear messages before anything runs (not the boundary) -----------------------------------------------------------

def check_script(code, allow_web=False):
    """problems of a script as a list of messages (empty = acceptable)"""
    if not isinstance(code, str) or not code.strip():
        return ["the script is empty"]
    if len(code) > MAX_SCRIPT_CHARS:
        return ["the script is longer than %d characters" % MAX_SCRIPT_CHARS]
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError, RecursionError, MemoryError) as exc:
        return ["the script is not valid Python: %s" % exc]
    problems = []
    nodes = list(ast.walk(tree))
    if len(nodes) > 4000:
        return ["the script is too complex"]
    for node in nodes:
        line = getattr(node, "lineno", "?")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in ALLOWED_MODULES and alias.name.partition(".")[0] not in ALLOWED_MODULES:
                    problems.append("line %s: importing '%s' is not allowed" % (line, alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.level or (node.module or "") not in ALLOWED_MODULES and (node.module or "").partition(".")[0] not in ALLOWED_MODULES:
                problems.append("line %s: importing from '%s' is not allowed" % (line, node.module))
        elif isinstance(node, ast.Name):
            if node.id in FORBIDDEN_NAMES or (node.id.startswith("__") and node.id.endswith("__")):
                problems.append("line %s: the name '%s' is not allowed" % (line, node.id))
            elif node.id == "web" and not allow_web:
                problems.append("line %s: web access is not enabled for this script" % line)
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("__") or node.attr in FORBIDDEN_ATTRIBUTES:
                problems.append("line %s: the attribute '%s' is not allowed" % (line, node.attr))
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            problems.append("line %s: global and nonlocal are not allowed" % line)
        if isinstance(node, (ast.Name, ast.Subscript, ast.Attribute)) and isinstance(getattr(node, "ctx", None), (ast.Store, ast.Del)):
            root = node
            while isinstance(root, (ast.Subscript, ast.Attribute)):
                root = root.value
            if isinstance(root, ast.Name) and root.id in READ_ONLY_NAMES:
                problems.append("line %s: `%s` is the input and must not be reassigned or changed: read from it" % (line, root.id))
    return sorted(set(problems), key=lambda p: (int(p.split()[1].rstrip(":")) if p.split()[1].rstrip(":").isdigit() else 0, p))[:20]


# --- the seccomp filter ------------------------------------------------------------------------------------------------------------

AUDIT_ARCH_X86_64 = 0xC000003E
CLONE_THREAD = 0x00010000
RET_ALLOW, RET_KILL_PROCESS = 0x7FFF0000, 0x80000000
EPERM, ENOSYS = 1, 38
# x86_64 system call numbers that a script never needs
DENIED_X86_64 = {"fork": 57, "vfork": 58, "ptrace": 101, "syslog": 103, "acct": 163, "mount": 165, "umount2": 166, "pivot_root": 155, "chroot": 161, "reboot": 169,
                 "swapon": 167, "swapoff": 168, "iopl": 172, "ioperm": 173, "init_module": 175, "delete_module": 176, "quotactl": 179, "lookup_dcookie": 212,
                 "kexec_load": 246, "add_key": 248, "request_key": 249, "keyctl": 250, "unshare": 272, "perf_event_open": 298, "name_to_handle_at": 303,
                 "open_by_handle_at": 304, "setns": 308, "process_vm_readv": 310, "process_vm_writev": 311, "kcmp": 312, "finit_module": 313, "kexec_file_load": 320,
                 "bpf": 321, "userfaultfd": 323, "io_uring_setup": 425, "io_uring_enter": 426, "io_uring_register": 427, "open_tree": 428, "move_mount": 429, "fsopen": 430,
                 "fsconfig": 431, "fsmount": 432, "fspick": 433, "pidfd_getfd": 438, "mount_setattr": 442}
CLONE, CLONE3 = 56, 435


def seccomp_program():
    """the classic BPF program as bytes (struct sock_filter[]), or None when this machine's architecture is not covered.
    Denied system calls return EPERM; clone is allowed only with CLONE_THREAD (threads yes, processes no); clone3 returns ENOSYS so that the C library falls back to clone;
    a different architecture (32-bit calls on a 64-bit kernel) kills the process."""
    if platform.machine() != "x86_64":
        return None
    LD, JEQ, JSET, RET = 0x20, 0x15, 0x45, 0x06
    program = []                   # entries: (code, jt label | None, jf label | None, k) with labels resolved below

    def emit(code, k=0, jt=None, jf=None, label=None):
        program.append({"code": code, "k": k, "jt": jt, "jf": jf, "label": label})

    emit(LD, 4)                                                            # architecture
    emit(JEQ, AUDIT_ARCH_X86_64, jt="ok_arch", jf="kill")
    emit(LD, 0, label="ok_arch")                                           # system call number
    for number in sorted(DENIED_X86_64.values()):
        emit(JEQ, number, jt="deny_perm", jf=None)
    emit(JEQ, CLONE3, jt="deny_nosys")
    emit(JEQ, CLONE, jt="check_clone")
    emit(RET, RET_ALLOW)
    emit(LD, 16, label="check_clone")                                      # flags: the low word of the first argument
    emit(JSET, CLONE_THREAD, jt="allow", jf="deny_perm")
    emit(RET, 0x00050000 | EPERM, label="deny_perm")
    emit(RET, 0x00050000 | ENOSYS, label="deny_nosys")
    emit(RET, RET_ALLOW, label="allow")
    emit(RET, RET_KILL_PROCESS, label="kill")
    positions = {item["label"]: i for i, item in enumerate(program) if item["label"]}
    out = b""
    for i, item in enumerate(program):
        def offset(label):
            if label is None:
                return 0
            distance = positions[label] - i - 1
            if not 0 <= distance <= 255:
                raise ValueError("jump too far")
            return distance
        out += struct.pack("HBBI", item["code"], offset(item["jt"]), offset(item["jf"]), item["k"])
    return out


# --- running ---------------------------------------------------------------------------------------------------------------------------

class SandboxResult:
    """status: ok | error (the script failed or reported an error) | timeout | crashed (killed: memory, CPU, a forbidden system call) | rejected (policy) | unavailable.
    backend / tier / degraded tell where it ran (see SandboxRouter)"""

    def __init__(self, status, result=None, stdout="", stderr="", error=None, seconds=0.0, exit_code=None, truncated=False, problems=None, script_hash="", backend="", tier="",
                 degraded=False):
        self.status, self.result, self.stdout, self.stderr, self.error = status, result, stdout, stderr, error
        self.seconds, self.exit_code, self.truncated, self.problems, self.script_hash = seconds, exit_code, truncated, problems or [], script_hash
        self.backend, self.tier, self.degraded = backend, tier, degraded

    @property
    def ok(self):
        return self.status == "ok"

    def as_dict(self):
        return {"status": self.status, "result": self.result, "stdout": self.stdout, "stderr": self.stderr, "error": self.error, "seconds": round(self.seconds, 3),
                "truncated": self.truncated, "problems": self.problems, "script_hash": self.script_hash, "backend": self.backend, "tier": self.tier, "degraded": self.degraded}


class _Backend:
    """what all backends share: the policy, the files of a run, the runner protocol and the reading of its answer. A backend supplies the command that builds the wall (_command)
    and a way to stop a run that does not end (_stop)."""
    name = ""

    def __init__(self, tmp_root=None):
        self.tmp_root = tmp_root
        self._available = None
        self.reason = ""

    @property
    def available(self):
        if self._available is None:
            self._available = self._probe()
        return self._available

    def _check_installation(self):
        """a reason string when this backend cannot work on this machine, else ''"""
        raise NotImplementedError

    def _probe(self):
        self.reason = self._check_installation()
        if self.reason:
            return False
        self._available = True                      # the test run below goes through run(), which checks this flag
        try:
            outcome = self.run("result = 6 * 7", timeout=60, policy=False)
        except OSError as exc:
            self.reason, self._available = "the test run could not start: %s" % exc, False
            return False
        if outcome.ok and outcome.result == 42:
            return True
        self.reason = "the test run failed: %s %s" % (outcome.status, (outcome.stderr or json.dumps(outcome.error))[:300])
        self._available = False
        return False

    def info(self):
        return {"backend": self.name, "available": self.available, "reason": self.reason, "arch": platform.machine()}

    def run(self, code, data=None, timeout=10, memory_mb=512, cpu_seconds=None, max_output=65536, fsize_mb=4, tmp_mb=16, broker=None, policy=True, raw=False):
        """runs `code` with `data` as input; returns a SandboxResult. policy=False skips the AST check and raw=True gives the script the full Python builtins:
        both are for testing the wall, never for model-written code"""
        started = time.time()
        digest = hashlib.sha256(str(code).encode("utf-8", "replace")).hexdigest()[:16]
        if self._available is False:
            return SandboxResult("unavailable", error={"message": self.reason or "no sandbox on this machine"}, script_hash=digest, backend=self.name)
        if policy:
            problems = check_script(code, allow_web=broker is not None)
            if problems:
                return SandboxResult("rejected", problems=problems, script_hash=digest, error={"message": "; ".join(problems[:3])}, backend=self.name)
        try:
            payload = json.dumps(data if data is not None else {})
        except (TypeError, ValueError):
            return SandboxResult("rejected", problems=["the input data is not JSON"], script_hash=digest, backend=self.name)
        work = tempfile.mkdtemp(prefix="mia-sandbox-", dir=self.tmp_root)
        outputs = tempfile.mkdtemp(prefix="mia-sandbox-out-", dir=self.tmp_root)          # what the sandbox writes to stdout and stderr: not visible inside
        try:
            return self._run(work, outputs, code, payload, timeout, memory_mb, cpu_seconds or timeout, max_output, fsize_mb, tmp_mb, broker, raw, started, digest)
        finally:
            shutil.rmtree(work, ignore_errors=True)
            shutil.rmtree(outputs, ignore_errors=True)

    def _command(self, work, spec, memory_mb, tmp_mb, broker):
        """(command list, extra file descriptors to pass, handle for _stop, cleanup callable)"""
        raise NotImplementedError

    def _stop(self, process, handle):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            process.kill()

    def _run(self, work, outputs, code, payload, timeout, memory_mb, cpu_seconds, max_output, fsize_mb, tmp_mb, broker, raw, started, digest):
        for name, text in (("script.py", code), ("input.json", payload)):
            with open(os.path.join(work, name), "w", encoding="utf-8") as fp:
                fp.write(text)
        shutil.copy(os.path.join(HERE, "sandbox_runner.py"), os.path.join(work, "runner.py"))
        spec = {"memory_mb": memory_mb, "cpu_seconds": int(cpu_seconds) + 1, "fsize_mb": fsize_mb, "max_output": max_output, "raw": bool(raw),
                "allowed_modules": list(ALLOWED_MODULES), "broker": broker is not None}
        command, pass_fds, handle, cleanup = self._command(work, spec, memory_mb, tmp_mb, broker)
        err_path = os.path.join(outputs, "stderr.txt")
        status, exit_code = "ok", None
        try:
            with open(err_path, "wb") as err:
                if broker is None:
                    out_path = os.path.join(outputs, "stdout.txt")
                    with open(out_path, "wb") as out:
                        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=out, stderr=err, pass_fds=pass_fds, start_new_session=True, cwd="/")
                        try:
                            exit_code = process.wait(timeout=timeout)
                        except subprocess.TimeoutExpired:
                            status = "timeout"
                            self._stop(process, handle)
                            exit_code = process.wait()
                    stdout = self._read(out_path, max_output * 2 + 4096)
                else:
                    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err, pass_fds=pass_fds, start_new_session=True, cwd="/")
                    captured, timed_out = self._serve(process, broker, started + timeout, max_output * 2 + 4096)
                    if timed_out:
                        status = "timeout"
                        self._stop(process, handle)
                    exit_code = process.wait()
                    stdout = captured.decode("utf-8", errors="replace")
        finally:
            cleanup()
        stderr = self._read(err_path, 4000)
        seconds = time.time() - started
        envelope = None
        at = stdout.rfind(MARK)
        if at >= 0:
            try:
                envelope = json.loads(stdout[at + len(MARK):].strip().splitlines()[0])
            except (ValueError, IndexError):
                envelope = None
        common = dict(stderr=stderr, seconds=seconds, exit_code=exit_code, script_hash=digest, backend=self.name)
        if status == "timeout":
            return SandboxResult("timeout", stdout=stdout[:2000], error={"type": "Timeout", "message": "the script did not finish within %s seconds" % timeout, "line": None}, **common)
        if envelope is None:
            return SandboxResult("crashed", stdout=stdout[:2000], **dict(common, error={"type": "Crashed", "line": None, "message": "the sandbox ended without an answer (exit code %s): "
                                                                                     "memory, CPU time or a forbidden system call" % exit_code}))
        return SandboxResult(envelope["status"], envelope.get("result"), envelope.get("stdout", ""), error=envelope.get("error"), truncated=envelope.get("truncated", False), **common)

    @staticmethod
    def _serve(process, broker, deadline, limit):
        """reads the standard output of a sandbox that has web access: request lines are answered by the broker on its standard input, everything else is kept (up to `limit`).
        Returns (what was kept, whether the deadline passed)"""
        import selectors
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        kept, buffer, skipping = bytearray(), b"", False

        def answer(request):
            try:
                process.stdin.write(ANSWER + json.dumps(request, ensure_ascii=False).encode("utf-8") + b"\n")
                process.stdin.flush()
            except (BrokenPipeError, OSError, ValueError):
                pass

        try:
            while True:
                remaining = deadline - time.time()
                if remaining <= 0:
                    return bytes(kept), True
                if not selector.select(min(remaining, 0.5)):
                    continue
                chunk = os.read(process.stdout.fileno(), 65536)
                if not chunk:
                    return bytes(kept), False
                buffer += chunk
                while True:
                    newline = buffer.find(b"\n")
                    if newline < 0:
                        if len(buffer) > MAX_REQUEST_LINE:                     # a line that never ends: whatever it was, it is not kept and not a request that will be served
                            if not skipping and buffer.startswith(REQUEST):
                                answer({"error": "the request is too long"})
                            skipping, buffer = True, b""
                        break
                    line, buffer = buffer[:newline], buffer[newline + 1:]
                    if skipping:
                        skipping = False                                       # the end of the overlong line
                        continue
                    if line.startswith(REQUEST):
                        answer(broker.handle_line(line[len(REQUEST):]))
                    elif len(kept) < limit:
                        kept += line[:limit - len(kept)] + b"\n"
        finally:
            selector.close()

    @staticmethod
    def _read(path, limit):
        try:
            with open(path, "rb") as fp:
                return fp.read(limit).decode("utf-8", errors="replace")
        except OSError:
            return ""


class BubblewrapSandbox(_Backend):
    """namespaces from bubblewrap, a seccomp filter, resource limits: about 65 ms per run, no image to keep, runs in the SELinux domain of the user"""
    name = "bubblewrap"

    def __init__(self, bwrap=None, python=None, tmp_root=None):
        super().__init__(tmp_root)
        self.bwrap = bwrap or shutil.which("bwrap")
        python = python or shutil.which("python3") or sys.executable
        self.python = os.path.realpath("/usr/bin/python3") if os.path.exists("/usr/bin/python3") else os.path.realpath(python)

    def _check_installation(self):
        if not self.bwrap or not os.access(self.bwrap, os.X_OK):
            return "bubblewrap (bwrap) is not installed"
        if not os.path.exists(self.python):
            return "no system Python at %s" % self.python
        return ""

    def info(self):
        return dict(super().info(), bwrap=self.bwrap, python=self.python, seccomp=seccomp_program() is not None)

    def _command(self, work, spec, memory_mb, tmp_mb, broker):
        command = [self.bwrap, "--unshare-all", "--die-with-parent", "--new-session", "--cap-drop", "ALL", "--clearenv",
                   "--setenv", "PATH", "/nonexistent", "--setenv", "LANG", "C.UTF-8", "--setenv", "PYTHONDONTWRITEBYTECODE", "1", "--setenv", "PYTHONHASHSEED", "0",
                   "--ro-bind", "/usr/lib", "/usr/lib", "--ro-bind", "/usr/lib64", "/usr/lib64", "--ro-bind", self.python, self.python,
                   "--symlink", "usr/lib", "/lib", "--symlink", "usr/lib64", "/lib64", "--proc", "/proc", "--dev", "/dev",
                   "--size", str(tmp_mb * 1024 * 1024), "--tmpfs", "/tmp", "--ro-bind", work, "/sandbox"]
        command += ["--remount-ro", "/", "--chdir", "/tmp"]                       # all mount points exist: now the root itself is read-only
        pass_fds, read_end = (), None
        program = seccomp_program()
        if program is not None:
            read_end, write_end = os.pipe()
            os.write(write_end, program)
            os.close(write_end)
            command += ["--seccomp", str(read_end)]
            pass_fds = (read_end,)
        # -s -S -P: no user site, no site, no script directory on the path. (-I would also ignore PYTHONHASHSEED, and the environment is empty anyway.)
        command += [self.python, "-s", "-S", "-P", "/sandbox/runner.py", json.dumps(spec)]

        def cleanup():
            if read_end is not None:
                os.close(read_end)
        return command, pass_fds, None, cleanup


DEFAULT_IMAGE = "localhost/mia-sandbox:1"
PODMAN_PROFILE_SOURCES = ("/etc/containers/seccomp.json", "/usr/share/containers/seccomp.json")
THREAD_ONLY = {"index": 0, "value": CLONE_THREAD, "valueTwo": CLONE_THREAD, "op": "SCMP_CMP_MASKED_EQ"}       # (flags & CLONE_THREAD) == CLONE_THREAD


def podman_seccomp_profile(source=None):
    """podman's own default profile, made stricter the same way as the bubblewrap filter: the system calls of DENIED_X86_64 and fork/vfork/clone/clone3 lose their permission,
    and clone comes back only with CLONE_THREAD (threads yes, processes no). Returns the profile dict, or None when the default profile cannot be found."""
    for path in ([source] if source else PODMAN_PROFILE_SOURCES):
        if path and os.path.exists(path):
            with open(path, encoding="utf-8") as fp:
                profile = json.load(fp)
            break
    else:
        return None
    removed = set(DENIED_X86_64) | {"fork", "vfork", "clone", "clone3"}
    groups = []
    for group in profile.get("syscalls", []):
        if group.get("action") == "SCMP_ACT_ALLOW":
            group = dict(group, names=[n for n in group.get("names", []) if n not in removed])
            if not group["names"]:
                continue
        groups.append(group)
    groups.append({"names": ["clone"], "action": "SCMP_ACT_ALLOW", "args": [THREAD_ONLY]})
    groups.append({"names": ["clone3"], "action": "SCMP_ACT_ERRNO", "errnoRet": ENOSYS})
    groups.append({"names": sorted(n for n in DENIED_X86_64 if n not in ("clone3",)) + ["fork", "vfork"], "action": "SCMP_ACT_ERRNO", "errnoRet": EPERM})
    profile["syscalls"] = groups
    return profile


class PodmanSandbox(_Backend):
    """a rootless podman container per run: no network, read-only root, no capabilities, no-new-privileges, a stricter seccomp profile, hard cgroup limits (memory, processes, cpu)
    and SELinux confinement (container_t with its own category label). About 1 s per run and an image to build (tools/sandbox/build_image.sh).
    One container per run, never a pod: containers of a pod share one network namespace."""
    name = "podman"

    def __init__(self, podman=None, image=DEFAULT_IMAGE, tmp_root=None, profile_source=None):
        super().__init__(tmp_root)
        self.podman = podman or shutil.which("podman")
        self.image = image
        self.profile_source = profile_source
        self._profile_dir = None

    def _check_installation(self):
        if not self.podman:
            return "podman is not installed"
        try:
            exists = subprocess.run([self.podman, "image", "exists", self.image], capture_output=True, timeout=30).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return "podman does not answer"
        if not exists:
            return "the image %s does not exist (build it with tools/sandbox/build_image.sh)" % self.image
        if podman_seccomp_profile(self.profile_source) is None:
            return "podman's default seccomp profile was not found, so the stricter profile cannot be made"
        return ""

    def info(self):
        return dict(super().info(), podman=self.podman, image=self.image)

    def _profile_path(self):
        if self._profile_dir is None:
            self._profile_dir = tempfile.mkdtemp(prefix="mia-seccomp-", dir=self.tmp_root)
            with open(os.path.join(self._profile_dir, "profile.json"), "w", encoding="utf-8") as fp:
                json.dump(podman_seccomp_profile(self.profile_source), fp)
        return os.path.join(self._profile_dir, "profile.json")

    def _command(self, work, spec, memory_mb, tmp_mb, broker):
        name = "mia-sbx-" + secrets.token_hex(5)
        command = [self.podman, "run", "--rm", "--name", name, "--pull=never", "--network=none", "--read-only", "--cap-drop=all", "--security-opt", "no-new-privileges",
                   "--security-opt", "seccomp=" + self._profile_path(), "--pids-limit=64", "--memory=%dm" % (memory_mb + 128), "--memory-swap=%dm" % (memory_mb + 128), "--cpus=1",
                   "--hostname", "sandbox", "--no-hosts", "--stop-timeout=0",
                   "--tmpfs", "/tmp:rw,size=%dm,noexec,nosuid,nodev" % tmp_mb, "-v", "%s:/sandbox:ro,Z" % work, "-w", "/tmp",
                   "--env", "LANG=C.UTF-8", "--env", "PYTHONDONTWRITEBYTECODE=1", "--env", "PYTHONHASHSEED=0"]
        if broker is not None:
            command.insert(2, "-i")                                      # the answers of the broker arrive on the standard input
        command += [self.image, "python3", "-s", "-S", "-P", "/sandbox/runner.py", json.dumps(spec)]
        return command, (), name, lambda: None

    def _stop(self, process, handle):
        try:
            subprocess.run([self.podman, "rm", "-f", "-t", "0", handle], capture_output=True, timeout=20)
        except (OSError, subprocess.TimeoutExpired):
            pass
        super()._stop(process, handle)


Sandbox = BubblewrapSandbox        # the first backend under its old name


# --- which backend for which operation ----------------------------------------------------------------------------------------------------

class Operation:
    """what is about to run, as far as it matters for the choice of the wall.
    kind:    compute (a pure calculation) | web_script (a script that gets web access through the broker) | parse (hostile documents)
    origin:  library (a pinned entry that is tested or trusted) | model (written by the model for this claim) | external (from outside: pasted, downloaded)
    tainted: the input comes from text of the web or of files nobody checked (prompt injection could have shaped the script)
    stakes:  normal | high"""

    def __init__(self, kind="compute", origin="model", tainted=False, stakes="normal"):
        self.kind, self.origin, self.tainted, self.stakes = kind, origin, bool(tainted), stakes

    def as_dict(self):
        return {"kind": self.kind, "origin": self.origin, "tainted": self.tainted, "stakes": self.stakes}


def required_tier(operation):
    """("standard" | "strong", [reasons]): the strong tier is for what is most exposed to hostile influence or matters most"""
    reasons = []
    if operation.kind in ("web_script", "parse"):
        reasons.append("the %s kind of operation reads outside data" % operation.kind)
    if operation.tainted:
        reasons.append("its input comes from unchecked web or file text")
    if operation.origin == "external":
        reasons.append("the code comes from outside")
    if operation.stakes == "high":
        reasons.append("the stakes are high")
    return ("strong" if reasons else "standard"), reasons


class SandboxRouter:
    """Chooses the backend per operation. standard: bubblewrap (fast: many small checks), podman if bubblewrap is missing. strong: podman only (SELinux, cgroups, own image).
    If the strong backend is missing the operation is refused (status unavailable), unless degrade=True, which runs it on bubblewrap and marks the result degraded.
    force: use only this backend for everything ('bubblewrap' or 'podman')."""

    def __init__(self, backends, degrade=False, force=None):
        self.backends = dict(backends)
        self.degrade, self.force = degrade, force

    def order(self, tier):
        if self.force in self.backends:
            return [self.force]
        if tier == "strong":
            return ["podman"] + (["bubblewrap"] if self.degrade else [])
        return ["bubblewrap", "podman"]

    def choose(self, operation=None):
        """(backend or None, tier, reasons): the first available backend in the order of the tier"""
        operation = operation or Operation()
        tier, reasons = required_tier(operation)
        for name in self.order(tier):
            backend = self.backends.get(name)
            if backend is not None and backend.available:
                if tier == "strong" and name != "podman" and not self.force:
                    reasons = reasons + ["degraded: the strong backend is not available"]
                return backend, tier, reasons
        return None, tier, reasons

    @property
    def available(self):
        """some backend works (used to switch the script checks on or off)"""
        return any(b.available for b in self.backends.values())

    def available_for(self, operation=None):
        return self.choose(operation)[0] is not None

    def info(self):
        return {"backends": {name: b.info() for name, b in self.backends.items()}, "degrade": self.degrade, "force": self.force}

    def run(self, code, data=None, operation=None, **kwargs):
        backend, tier, reasons = self.choose(operation)
        if backend is None:
            wanted = self.order(tier)
            detail = "; ".join("%s: %s" % (n, self.backends[n].reason or "not available") for n in wanted if n in self.backends) or "no backend configured"
            return SandboxResult("unavailable", error={"message": "no sandbox for a %s operation (%s). %s" % (tier, "; ".join(reasons) or "standard", detail)},
                                 script_hash=hashlib.sha256(str(code).encode("utf-8", "replace")).hexdigest()[:16], tier=tier)
        result = backend.run(code, data, **kwargs)
        result.tier = tier
        result.degraded = tier == "strong" and backend.name != "podman" and not self.force
        return result


def create_router(cfg=None, tmp_root=None):
    """a router from the configuration: sandbox_backend ('auto' | 'bubblewrap' | 'podman'), sandbox_degrade (false), sandbox_image"""
    cfg = cfg or {}
    force = cfg.get("sandbox_backend", "auto")
    return SandboxRouter({"bubblewrap": BubblewrapSandbox(tmp_root=tmp_root), "podman": PodmanSandbox(image=cfg.get("sandbox_image", DEFAULT_IMAGE), tmp_root=tmp_root)},
                         degrade=bool(cfg.get("sandbox_degrade", False)), force=force if force in ("bubblewrap", "podman") else None)
