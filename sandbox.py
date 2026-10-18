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
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
MARK = "\x01MIA\x01"
MAX_SCRIPT_CHARS = 8000

ALLOWED_MODULES = ("math", "statistics", "fractions", "decimal", "datetime", "calendar", "re", "json", "itertools", "collections", "string", "functools", "operator", "heapq",
                   "bisect", "textwrap", "unicodedata", "csv", "base64", "hashlib", "html", "urllib.parse", "typing", "copy", "numbers", "enum")
FORBIDDEN_NAMES = {"open", "exec", "eval", "compile", "__import__", "input", "breakpoint", "globals", "locals", "vars", "getattr", "setattr", "delattr", "help", "exit", "quit",
                   "memoryview", "__builtins__", "__loader__", "__spec__"}
FORBIDDEN_ATTRIBUTES = {"gi_frame", "gi_code", "cr_frame", "cr_code", "ag_frame", "ag_code", "f_globals", "f_locals", "f_builtins", "f_back", "f_code", "tb_frame", "tb_next",
                        "func_globals", "mro"}


class SandboxUnavailable(Exception):
    pass


SCRIPT_GUIDE = """Write a short Python script. It has these names: `data` (the input, parsed JSON) and, only if web access was granted, `web` (`web.get(url)` returns the page text, `web.search(query)` returns results).
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
    """status: ok | error (the script failed or reported an error) | timeout | crashed (killed: memory, CPU, a forbidden system call) | rejected (policy) | unavailable"""

    def __init__(self, status, result=None, stdout="", stderr="", error=None, seconds=0.0, exit_code=None, truncated=False, problems=None, script_hash=""):
        self.status, self.result, self.stdout, self.stderr, self.error = status, result, stdout, stderr, error
        self.seconds, self.exit_code, self.truncated, self.problems, self.script_hash = seconds, exit_code, truncated, problems or [], script_hash

    @property
    def ok(self):
        return self.status == "ok"

    def as_dict(self):
        return {"status": self.status, "result": self.result, "stdout": self.stdout, "stderr": self.stderr, "error": self.error, "seconds": round(self.seconds, 3),
                "truncated": self.truncated, "problems": self.problems, "script_hash": self.script_hash}


class Sandbox:
    def __init__(self, bwrap=None, python=None, tmp_root=None):
        self.bwrap = bwrap or shutil.which("bwrap")
        python = python or shutil.which("python3") or sys.executable
        self.python = os.path.realpath("/usr/bin/python3") if os.path.exists("/usr/bin/python3") else os.path.realpath(python)
        self.tmp_root = tmp_root
        self._available = None
        self.reason = ""

    # -- is there a wall? --
    @property
    def available(self):
        if self._available is None:
            self._available = self._probe()
        return self._available

    def _probe(self):
        if not self.bwrap:
            self.reason = "bubblewrap (bwrap) is not installed"
            return False
        if not os.path.exists(self.python):
            self.reason = "no system Python at %s" % self.python
            return False
        outcome = self.run("result = 6 * 7", timeout=15, policy=False)
        if outcome.ok and outcome.result == 42:
            return True
        self.reason = "the test run failed: %s %s" % (outcome.status, (outcome.stderr or json.dumps(outcome.error))[:300])
        return False

    def info(self):
        return {"available": self.available, "reason": self.reason, "bwrap": self.bwrap, "python": self.python, "seccomp": seccomp_program() is not None,
                "arch": platform.machine()}

    # -- one run --
    def run(self, code, data=None, timeout=10, memory_mb=512, cpu_seconds=None, max_output=65536, fsize_mb=4, tmp_mb=16, broker=None, policy=True, raw=False):
        """runs `code` in the sandbox with `data` as input; returns a SandboxResult. policy=False skips the AST check and raw=True gives the script the full Python builtins:
        both are for testing the wall, never for model-written code"""
        started = time.time()
        digest = hashlib.sha256(str(code).encode("utf-8", "replace")).hexdigest()[:16]
        if self._available is False and self.reason:
            return SandboxResult("unavailable", error={"message": self.reason}, script_hash=digest)
        if not self.bwrap or not os.path.exists(self.python):
            return SandboxResult("unavailable", error={"message": "no sandbox on this machine"}, script_hash=digest)
        if policy:
            problems = check_script(code, allow_web=broker is not None)
            if problems:
                return SandboxResult("rejected", problems=problems, script_hash=digest, error={"message": "; ".join(problems[:3])})
        try:
            payload = json.dumps(data if data is not None else {})
        except (TypeError, ValueError):
            return SandboxResult("rejected", problems=["the input data is not JSON"], script_hash=digest)
        work = tempfile.mkdtemp(prefix="mia-sandbox-", dir=self.tmp_root)
        outputs = tempfile.mkdtemp(prefix="mia-sandbox-out-", dir=self.tmp_root)          # what the sandbox writes to stdout and stderr: not visible inside
        try:
            return self._run(work, outputs, code, payload, timeout, memory_mb, cpu_seconds or timeout, max_output, fsize_mb, tmp_mb, broker, raw, started, digest)
        finally:
            shutil.rmtree(work, ignore_errors=True)
            shutil.rmtree(outputs, ignore_errors=True)

    def _run(self, work, outputs, code, payload, timeout, memory_mb, cpu_seconds, max_output, fsize_mb, tmp_mb, broker, raw, started, digest):
        for name, text in (("script.py", code), ("input.json", payload)):
            with open(os.path.join(work, name), "w", encoding="utf-8") as fp:
                fp.write(text)
        shutil.copy(os.path.join(HERE, "sandbox_runner.py"), os.path.join(work, "runner.py"))
        spec = {"memory_mb": memory_mb, "cpu_seconds": int(cpu_seconds) + 1, "fsize_mb": fsize_mb, "max_output": max_output, "raw": bool(raw),
                "allowed_modules": list(ALLOWED_MODULES), "broker": "/broker/sock" if broker is not None else None}
        command = [self.bwrap, "--unshare-all", "--die-with-parent", "--new-session", "--cap-drop", "ALL", "--clearenv",
                   "--setenv", "PATH", "/nonexistent", "--setenv", "LANG", "C.UTF-8", "--setenv", "PYTHONDONTWRITEBYTECODE", "1", "--setenv", "PYTHONHASHSEED", "0",
                   "--ro-bind", "/usr/lib", "/usr/lib", "--ro-bind", "/usr/lib64", "/usr/lib64", "--ro-bind", self.python, self.python,
                   "--symlink", "usr/lib", "/lib", "--symlink", "usr/lib64", "/lib64", "--proc", "/proc", "--dev", "/dev",
                   "--size", str(tmp_mb * 1024 * 1024), "--tmpfs", "/tmp", "--ro-bind", work, "/sandbox"]
        if broker is not None:
            command += ["--bind", broker.directory, "/broker"]
        command += ["--remount-ro", "/", "--chdir", "/tmp"]                       # all mount points exist: now the root itself is read-only
        pass_fds = ()
        read_end = None
        program = seccomp_program()
        if program is not None:
            read_end, write_end = os.pipe()
            os.write(write_end, program)
            os.close(write_end)
            command += ["--seccomp", str(read_end)]
            pass_fds = (read_end,)
        # -s -S -P: no user site, no site, no script directory on the path. (-I would also ignore PYTHONHASHSEED, and the environment is empty anyway.)
        command += [self.python, "-s", "-S", "-P", "/sandbox/runner.py", json.dumps(spec)]
        out_path, err_path = os.path.join(outputs, "stdout.txt"), os.path.join(outputs, "stderr.txt")
        status, exit_code = "ok", None
        try:
            with open(out_path, "wb") as out, open(err_path, "wb") as err:
                process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=out, stderr=err, pass_fds=pass_fds, start_new_session=True, cwd="/")
                try:
                    exit_code = process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    status = "timeout"
                    self._kill(process)
                    exit_code = process.wait()
        finally:
            if read_end is not None:
                os.close(read_end)
        stdout = self._read(out_path, max_output * 2 + 4096)
        stderr = self._read(err_path, 4000)
        seconds = time.time() - started
        envelope = None
        at = stdout.rfind(MARK)
        if at >= 0:
            try:
                envelope = json.loads(stdout[at + len(MARK):].strip().splitlines()[0])
            except (ValueError, IndexError):
                envelope = None
        if status == "timeout":
            return SandboxResult("timeout", stdout=stdout[:2000], stderr=stderr, seconds=seconds, exit_code=exit_code, script_hash=digest,
                                 error={"type": "Timeout", "message": "the script did not finish within %s seconds" % timeout, "line": None})
        if envelope is None:
            return SandboxResult("crashed", stdout=stdout[:2000], stderr=stderr, seconds=seconds, exit_code=exit_code, script_hash=digest,
                                 error={"type": "Crashed", "message": "the sandbox ended without an answer (exit code %s): memory, CPU time or a forbidden system call" % exit_code, "line": None})
        return SandboxResult(envelope["status"], envelope.get("result"), envelope.get("stdout", ""), stderr, envelope.get("error"), seconds, exit_code, envelope.get("truncated", False),
                             script_hash=digest)

    @staticmethod
    def _kill(process):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            process.kill()

    @staticmethod
    def _read(path, limit):
        try:
            with open(path, "rb") as fp:
                return fp.read(limit).decode("utf-8", errors="replace")
        except OSError:
            return ""
