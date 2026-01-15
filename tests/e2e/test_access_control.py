import os
import shutil
import subprocess

import pytest

# Configuration
CONTAINER_NAME = "ssi-agent-test-1"


# Check if we are running inside the container (approximate check)
IN_CONTAINER = os.path.exists("/.dockerenv") or os.path.exists(
    "/opt/ssi-agent/.run_tests"
)


def run_in_container(cmd: str, user: str = "root"):
    """
    Executes a bash command.
    If running locally, uses 'podman exec'.
    If running inside container, uses 'su'.
    """
    if IN_CONTAINER:
        # Internal execution
        if user == "root":
            final_cmd = ["bash", "-c", cmd]
        else:
            # -c must be the last argument to su
            final_cmd = ["su", "-", user, "-c", cmd]

        # We don't check returncode here to be consistent with external behavior
        return subprocess.run(final_cmd, capture_output=True, text=True)
    else:
        # External execution
        # We use 'bash -c' to allow complex command strings
        podman_cmd = ["podman", "exec", "-u", user, CONTAINER_NAME, "bash", "-c", cmd]

        # Run without checking return code immediately, so we can assert on it
        result = subprocess.run(podman_cmd, capture_output=True, text=True)
        return result


def is_container_running():
    """Checks if the target container is active."""
    if shutil.which("podman") is None:
        return False

    res = subprocess.run(
        ["podman", "ps", "--format", "{{.Names}}"], capture_output=True, text=True
    )
    return CONTAINER_NAME in res.stdout


@pytest.mark.skipif(
    not IN_CONTAINER and not is_container_running(),
    reason=f"Container {CONTAINER_NAME} is not running",
)
class TestAccessControl:
    def test_admin_can_run_ssi(self):
        """
        Verify that the 'admin' user (granted via sudo/wheel group)
        has permission to execute the ssi CLI.
        """
        # The 'ssi' command usually prints usage on --help or runs status
        result = run_in_container("ssi --help", user="admin")

        # Should succeed (exit 0)
        assert result.returncode == 0, f"Admin user failed to run ssi: {result.stderr}"
        assert "Usage: ssi" in result.stdout

    def test_regular_user_denied_ssi(self):
        """
        Verify that a regular user (not in admin group) CANNOT execute ssi.
        This validates the chmod/chown hardening on /opt/ssi-agent/venv.
        """
        test_user = "test_regular_user"

        # 1. Ensure a dummy regular user exists
        # We run this as root to have permission to create users
        setup = run_in_container(
            f"id {test_user} || useradd -m {test_user}", user="root"
        )
        assert setup.returncode == 0, f"Setup failed: {setup.stderr}"

        # 2. Attempt to run ssi via absolute path to ensure we hit the permission check
        # and not a PATH lookup failure.
        result = run_in_container("/usr/local/bin/ssi --help", user=test_user)

        # 3. Assert Failure
        assert result.returncode != 0, (
            "Security Check Failed: Regular user was able to execute ssi!"
        )

        # 4. Assert correct reason (Permission denied)
        # Note: Bash error messages typically go to stderr
        combined_output = result.stderr + result.stdout
        assert "Permission denied" in combined_output, (
            f"Unexpected error message: {combined_output}"
        )
