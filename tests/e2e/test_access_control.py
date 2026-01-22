import subprocess


def run_command(cmd: str, user: str = "root"):
    """
    Executes a bash command locally (inside the container).
    """
    if user == "root":
        final_cmd = ["bash", "-c", cmd]
    else:
        # -c must be the last argument to su
        final_cmd = ["su", "-", user, "-c", cmd]

    return subprocess.run(final_cmd, capture_output=True, text=True)


class TestAccessControl:
    def test_admin_can_run_ssi(self):
        """
        Verify that the 'admin' user (granted via sudo/wheel group)
        has permission to execute the ssi CLI.
        """
        # The 'ssi' command usually prints usage on --help or runs status
        result = run_command("ssi --help", user="admin")

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
        setup = run_command(f"id {test_user} || useradd -m {test_user}", user="root")
        assert setup.returncode == 0, f"Setup failed: {setup.stderr}"

        # 2. Attempt to run ssi via absolute path to ensure we hit the permission check
        # and not a PATH lookup failure.
        result = run_command("/usr/local/bin/ssi --help", user=test_user)

        # 3. Assert Failure
        assert (
            result.returncode != 0
        ), "Security Check Failed: Regular user was able to execute ssi!"

        # 4. Assert correct reason (Permission denied)
        # Note: Bash error messages typically go to stderr
        combined_output = result.stderr + result.stdout
        assert (
            "Permission denied" in combined_output
        ), f"Unexpected error message: {combined_output}"
