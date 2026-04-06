import os
import sys
from pathlib import Path

import pexpect

from tests.helpers import run_cli


def test_help_subcommand(cli_workdir: Path) -> None:
    res = run_cli(cli_workdir, "help")
    assert res.returncode == 0
    assert "init:" in res.stdout
    assert "add:" in res.stdout
    assert "remove:" in res.stdout
    assert "show:" in res.stdout
    assert "get:" in res.stdout
    assert "clear:" in res.stdout


def test_init_creates_store_and_key(cli_workdir: Path) -> None:
    store = cli_workdir / "pwstore.json"
    assert not store.exists()

    res = run_cli(cli_workdir, "init")
    assert res.returncode == 0
    assert store.exists()

    env_file = cli_workdir / ".env"
    env_text = env_file.read_text(encoding="utf-8")
    assert "PWD_FILE=" in env_text
    assert "ENCRYPTION_KEY=" in env_text


def test_add_get_show_remove_clear_flow(cli_workdir: Path) -> None:
    # init first so add/get don't need to create the file mid-interaction
    res_init = run_cli(cli_workdir, "init")
    assert res_init.returncode == 0

    # add uses getpass; use pexpect for the hidden password prompt
    env = os.environ.copy()
    env["PYTHONPATH"] = str(cli_workdir)

    child = pexpect.spawn(
        sys.executable,
        [str(cli_workdir / "pw_manager.py"), "add"],
        cwd=str(cli_workdir),
        env=env,
        encoding="utf-8",
        timeout=15,
    )
    child.expect("Enter the site this login will be used for:")
    child.sendline("github")
    child.expect("Enter the username:")
    child.sendline("alice")
    child.expect("Enter your password:")
    child.sendline("S3cret!")
    child.expect("Enter the url of the site, otherwise press enter:")
    child.sendline("https://github.com")
    child.expect(pexpect.EOF)
    out = child.before or ""
    assert "added" in out

    # show should list github + alice (plaintext usernames)
    res_show = run_cli(cli_workdir, "show")
    assert res_show.returncode == 0
    assert "github" in res_show.stdout
    assert "alice" in res_show.stdout

    # get should find 1 login and copy password (assume clipboard works)
    res_get = run_cli(cli_workdir, "get", input_text="github\n")
    assert res_get.returncode == 0
    assert "Found 1 login for 'github' with username: alice" in res_get.stdout
    assert "Password has been copied to the clipboard." in res_get.stdout

    # remove: delete specific login [1]
    res_remove_one = run_cli(cli_workdir, "remove", input_text="github\n1\n")
    assert res_remove_one.returncode == 0
    assert "Deleted alice from github" in res_remove_one.stdout

    # now service exists but has no logins; get should report no logins found
    res_get_empty = run_cli(cli_workdir, "get", input_text="github\n")
    assert res_get_empty.returncode == 0
    assert "No logins found for service 'github'." in res_get_empty.stdout

    # add two logins so we can test remove-all and get multi-select cancel
    for user in ("alice", "bob"):
        child = pexpect.spawn(
            sys.executable,
            [str(cli_workdir / "pw_manager.py"), "add"],
            cwd=str(cli_workdir),
            env=env,
            encoding="utf-8",
            timeout=15,
        )
        child.expect("Enter the site this login will be used for:")
        child.sendline("gmail")
        child.expect("Enter the username:")
        child.sendline(user)
        child.expect("Enter your password:")
        child.sendline("pw12345")
        child.expect("Enter the url of the site, otherwise press enter:")
        child.sendline("")
        child.expect(pexpect.EOF)

    # get with multiple logins: cancel via Enter
    res_get_multi_cancel = run_cli(cli_workdir, "get", input_text="gmail\n\n")
    assert res_get_multi_cancel.returncode == 0
    assert "Found 2 logins for 'gmail':" in res_get_multi_cancel.stdout
    assert "Cancelled; no password was copied." in res_get_multi_cancel.stdout

    # get with multiple logins: choose second
    res_get_multi_choose = run_cli(cli_workdir, "get", input_text="gmail\n2\n")
    assert res_get_multi_choose.returncode == 0
    assert "Password for login 2 (username: bob) has been copied to the clipboard." in res_get_multi_choose.stdout

    # remove: clear all logins with 0
    res_remove_all = run_cli(cli_workdir, "remove", input_text="gmail\n0\n")
    assert res_remove_all.returncode == 0
    assert "Deleted 2 logins under gmail" in res_remove_all.stdout

    # clear: confirm y removes the JSON file
    store = cli_workdir / "pwstore.json"
    assert store.exists()
    res_clear = run_cli(cli_workdir, "clear", input_text="y\n")
    assert res_clear.returncode == 0
    assert "Password manager cleared and json file removed" in res_clear.stdout
    assert not store.exists()


def test_change_password(cli_workdir: Path) -> None:
    # init first to create store and key
    res_init = run_cli(cli_workdir, "init")
    assert res_init.returncode == 0

    # add a login we will later change
    env = os.environ.copy()
    env["PYTHONPATH"] = str(cli_workdir)

    child = pexpect.spawn(
        sys.executable,
        [str(cli_workdir / "pw_manager.py"), "add"],
        cwd=str(cli_workdir),
        env=env,
        encoding="utf-8",
        timeout=15,
    )
    child.expect("Enter the site this login will be used for:")
    child.sendline("github")
    child.expect("Enter the username:")
    child.sendline("alice")
    child.expect("Enter your password:")
    child.sendline("OldSecret!")
    child.expect("Enter the url of the site, otherwise press enter:")
    child.sendline("")
    child.expect(pexpect.EOF)

    # run the change subcommand to update the password
    child = pexpect.spawn(
        sys.executable,
        [str(cli_workdir / "pw_manager.py"), "change"],
        cwd=str(cli_workdir),
        env=env,
        encoding="utf-8",
        timeout=15,
    )
    child.expect("Enter the site to change logins for:")
    child.sendline("github")
    child.expect("Enter the username to change:")
    child.sendline("alice")
    child.expect("Enter your new password:")
    child.sendline("NewSecret!")
    child.expect(pexpect.EOF)
    out = child.before or ""
    assert "Password for alice in github has been changed" in out

    # verify on-disk data was actually updated by decrypting from the JSON store
    from key_manager import KeyManager
    from pw_class import pwStruct

    store_path = cli_workdir / "pwstore.json"
    env_path = cli_workdir / ".env"
    key_manager = KeyManager.new_env(env_path)
    pw_store = pwStruct.load_from_file(str(store_path), key_manager)
    creds = pw_store.get_pw("github")
    assert creds == [("alice", "NewSecret!")]


def test_remove_requires_nonempty_service(cli_workdir: Path) -> None:
    res = run_cli(cli_workdir, "remove", input_text="\n")
    assert res.returncode == 0
    assert "Error: service name must not be empty." in res.stdout

