"""
PDF to text, inside a wall (ui/REQUIREMENTS_RESEARCH.md RV34, 2d). A PDF is untrusted input and a PDF parser is a large program, so the converter (pdftotext of poppler) never runs in MIA's own
process or with MIA's rights. It runs under bubblewrap with the same kind of wall as the sandbox for scripts (sandbox.py): new user, pid, ipc, uts, cgroup and network namespaces (no network,
not even localhost), no home, no /etc, no project files, no environment, an empty temporary directory, only the input file, read-only; the seccomp filter of sandbox.py (no new processes, no
ptrace, no mount ...); limits for address space, CPU time and file size from prlimit; a wall-clock timeout from outside that kills the whole process group; a cap on the text.

  W1  if there is no bubblewrap or no pdftotext the feature is off (PdfUnavailable); it is never run without the wall
  W2  the input is copied to a private temporary directory and shown to the converter read-only; nothing it writes survives
  W3  the result is text only (UTF-8), cut at max_chars; the converter's messages are returned as warnings, never executed or trusted
"""
import os
import shutil
import signal
import subprocess
import tempfile
import time

try:
    from .sandbox import seccomp_program
except ImportError:  # used as plain script / in tests
    from sandbox import seccomp_program

MAX_INPUT_BYTES = 60 * 1024 * 1024


class PdfError(Exception):
    pass


class PdfUnavailable(PdfError):
    pass


def tools():
    """(bwrap, pdftotext, prlimit) paths or None"""
    return shutil.which("bwrap"), shutil.which("pdftotext"), shutil.which("prlimit")


def available():
    """(True, "") or (False, why not)"""
    bwrap, pdftotext, _ = tools()
    if not bwrap:
        return False, "bubblewrap (bwrap) is not installed"
    if not pdftotext:
        return False, "pdftotext (poppler-utils) is not installed"
    return True, ""


def wall(argv, input_name="input.pdf", memory_mb=1024, cpu_seconds=30, fsize_mb=8):
    """the command line that runs argv inside the wall; the input file is bound read-only to /tmp/<input_name>"""
    bwrap, _, prlimit = tools()
    command = []
    if prlimit:
        command += [prlimit, "--as=%d" % (memory_mb * 1024 * 1024), "--cpu=%d" % cpu_seconds, "--fsize=%d" % (fsize_mb * 1024 * 1024), "--nofile=64", "--core=0", "--"]
    command += [bwrap, "--unshare-all", "--die-with-parent", "--new-session", "--cap-drop", "ALL", "--clearenv", "--setenv", "PATH", "/usr/bin", "--setenv", "LANG", "C.UTF-8",
                "--ro-bind", "/usr", "/usr", "--symlink", "usr/lib", "/lib", "--symlink", "usr/lib64", "/lib64", "--symlink", "usr/bin", "/bin",
                "--proc", "/proc", "--dev", "/dev", "--size", str(16 * 1024 * 1024), "--tmpfs", "/tmp"]
    return command, input_name


def run_in_wall(argv, files, timeout=30, memory_mb=1024, cpu_seconds=30, max_output=8 * 1024 * 1024):
    """run argv in the wall with the given files bound read-only into /tmp: files = {name: path}. Returns (exit code or None on timeout, stdout bytes, stderr bytes, seconds)."""
    ok, why = available()
    if not ok:
        raise PdfUnavailable(why)
    command, _ = wall(argv, memory_mb=memory_mb, cpu_seconds=cpu_seconds)
    for name, path in files.items():
        command += ["--ro-bind", path, "/tmp/" + name]
    command += ["--remount-ro", "/", "--chdir", "/tmp"]
    program = seccomp_program()
    pass_fds, read_end = (), None
    if program is not None:
        read_end, write_end = os.pipe()
        os.write(write_end, program)
        os.close(write_end)
        command += ["--seccomp", str(read_end)]
        pass_fds = (read_end,)
    command += list(argv)
    started, deadline = time.monotonic(), time.monotonic() + timeout
    out, err = bytearray(), bytearray()
    try:
        with tempfile.TemporaryFile() as errfile:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=errfile, pass_fds=pass_fds, start_new_session=True, cwd="/")
            os.set_blocking(process.stdout.fileno(), False)
            timed_out = False
            while True:
                try:
                    chunk = process.stdout.read(65536)
                except BlockingIOError:
                    chunk = None
                if chunk:
                    out += chunk
                    if len(out) > max_output:
                        timed_out = True                                  # too much output counts like a runaway process
                        break
                    continue
                if chunk == b"" and process.poll() is not None:
                    break
                if time.monotonic() > deadline:
                    timed_out = True
                    break
                if chunk is None:
                    time.sleep(0.01)
            if timed_out:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    pass
            try:
                code = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                code = None
            code = None if timed_out else code
            process.stdout.close()
            errfile.seek(0)
            err = errfile.read(20000)
    finally:
        if read_end is not None:
            os.close(read_end)
    return code, bytes(out[:max_output]), bytes(err), round(time.monotonic() - started, 2)


def pdf_to_text(source, timeout=30, memory_mb=1024, max_pages=300, max_chars=3_000_000):
    """{"text", "pages_read", "truncated", "seconds", "warnings"} from a PDF (bytes or a path); raises PdfUnavailable (W1) or PdfError (not a PDF, too big, the converter failed or ran too long)"""
    ok, why = available()
    if not ok:
        raise PdfUnavailable(why)
    if isinstance(source, (bytes, bytearray)):
        data = source
    else:
        with open(source, "rb") as fp:
            data = fp.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES:
        raise PdfError("the PDF is larger than %d MB" % (MAX_INPUT_BYTES // 1024 // 1024))
    if not bytes(data[:1024]).lstrip().startswith(b"%PDF-"):
        raise PdfError("this is not a PDF (no %PDF header)")
    folder = tempfile.mkdtemp(prefix="mia-pdf-")
    try:
        os.chmod(folder, 0o700)
        path = os.path.join(folder, "input.pdf")
        with open(path, "wb") as fp:
            fp.write(data)
        os.chmod(path, 0o400)
        _, pdftotext, _ = tools()
        code, out, err, seconds = run_in_wall([pdftotext, "-enc", "UTF-8", "-l", str(max_pages), "/tmp/input.pdf", "-"], {"input.pdf": path},
                                              timeout=timeout, memory_mb=memory_mb, cpu_seconds=max(5, int(timeout)))
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    if code is None:
        raise PdfError("the converter did not finish within %s seconds (or produced far too much text)" % timeout)
    if code != 0:
        raise PdfError("the converter failed (exit code %s): %s" % (code, err.decode("utf-8", "replace").strip()[:200]))
    raw = out.decode("utf-8", "replace")
    pages = raw.count("\f")
    text = raw.replace("\f", "\n\n")
    truncated = len(text) > max_chars
    return {"text": text[:max_chars], "pages_read": pages, "truncated": truncated, "seconds": seconds,
            "warnings": [l for l in err.decode("utf-8", "replace").splitlines() if l.strip()][:10]}
