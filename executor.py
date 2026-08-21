import docker
import base64
import uuid
import os
import tempfile

client = docker.from_env()

SANDBOX_IMAGE = "sandbox-executor"
TIMEOUT_SECONDS = 30


def run_code_in_sandbox(code: str, output_filename: str) -> dict:
    """
    Spins up an ephemeral container, runs the code,
    reads the output file, destroys the container.
    Returns { success, data (base64), error }
    """

    container = None
    host_dir = tempfile.mkdtemp()  # temp dir on host to mount into container

    try:
        # write the code to a file inside the temp dir
        code_path = os.path.join(host_dir, "script.py")
        with open(code_path, "w") as f:
            f.write(code)

        # spin up container with the host dir mounted
        container = client.containers.run(
            image=SANDBOX_IMAGE,
            command=f"python /sandbox/script.py",
            volumes={
                host_dir: {
                    "bind": "/sandbox",
                    "mode": "rw"
                }
            },
            working_dir="/sandbox",
            mem_limit="256m",          # memory cap
            cpu_period=100000,
            cpu_quota=50000,           # 50% of one CPU
            network_disabled=True,     # no internet access inside sandbox
            remove=False,              # we remove manually after reading logs
            detach=True,
        )

        # wait for container to finish, with timeout
        result = container.wait(timeout=TIMEOUT_SECONDS)
        exit_code = result["StatusCode"]
        logs = container.logs().decode("utf-8")

        if exit_code != 0:
            return {
                "success": False,
                "error": logs,
                "data": None,
                "output_type": None
            }

        # read the output file from the mounted host dir
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
            "logs": logs
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": None,
        }

    finally:
        # always clean up — remove container and temp dir
        if container:
            try:
                container.remove(force=True)
            except Exception:
                pass

        # clean up temp files on host
        for f in os.listdir(host_dir):
            try:
                os.remove(os.path.join(host_dir, f))
            except Exception:
                pass
        try:
            os.rmdir(host_dir)
        except Exception:
            pass