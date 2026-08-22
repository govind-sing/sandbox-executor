import docker
import base64
import os
import tempfile

client = docker.from_env()

SANDBOX_IMAGE = "sandbox-executor"
TIMEOUT_SECONDS = 30

BANNED_PATTERNS = [
    "os.system",
    "subprocess",
    "shutil.rmtree",
    "__import__",
    "eval(",
    "exec(",
    "open('/",
    "os.remove",
    "os.unlink",
]


def is_code_safe(code: str) -> tuple[bool, str]:
    for pattern in BANNED_PATTERNS:
        if pattern in code:
            return False, f"Banned pattern detected: '{pattern}'"
    return True, ""


def run_code_in_sandbox(code: str, output_filename: str) -> dict:
    """
    Spins up an ephemeral container, runs the code,
    reads the output file, destroys the container.
    Returns { success, data (base64), error }
    """

    # safety check before touching Docker
    safe, reason = is_code_safe(code)
    if not safe:
        return {
            "success": False,
            "error": f"Code rejected by safety filter: {reason}",
            "data": None,
        }

    container = None
    host_dir = tempfile.mkdtemp()

    try:
        code_path = os.path.join(host_dir, "script.py")
        with open(code_path, "w") as f:
            f.write(code)

        container = client.containers.run(
            image=SANDBOX_IMAGE,
            command="python /sandbox/script.py",
            volumes={
                host_dir: {
                    "bind": "/sandbox",
                    "mode": "rw"
                }
            },
            working_dir="/sandbox",
            mem_limit="256m",
            cpu_period=100000,
            cpu_quota=50000,
            network_disabled=True,
            remove=False,
            detach=True,
        )

        # wait with timeout
        try:
            result = container.wait(timeout=TIMEOUT_SECONDS)
            exit_code = result["StatusCode"]
            logs = container.logs().decode("utf-8")
        except Exception as e:
            error_str = str(e).lower()
            if "timed out" in error_str or "read timeout" in error_str or "unixhttp" in error_str:
                return {
                    "success": False,
                    "error": "This task could not be completed within 30 seconds. Try a simpler or smaller request.",
                    "data": None,
                }
            raise
        if exit_code != 0:
            return {
                "success": False,
                "error": logs,
                "data": None,
            }

        output_path = os.path.join(host_dir, output_filename)

        if not os.path.exists(output_path):
            return {
                "success": False,
                "error": f"Expected output file '{output_filename}' was not created.\nLogs: {logs}",
                "data": None,
            }

        with open(output_path, "rb") as f:
            file_bytes = f.read()

        encoded = base64.b64encode(file_bytes).decode("utf-8")

        return {
            "success": True,
            "data": encoded,
            "error": None,
            "logs": logs,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": None,
        }

    finally:
        if container:
            try:
                container.remove(force=True)
            except Exception:
                pass

        for f in os.listdir(host_dir):
            try:
                os.remove(os.path.join(host_dir, f))
            except Exception:
                pass
        try:
            os.rmdir(host_dir)
        except Exception:
            pass