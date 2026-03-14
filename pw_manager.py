#!/usr/bin/env python3
import argparse
import hashlib
import base64
import os
import json
import getpass
from datetime import datetime, timezone
from pw_class import pw, loginList, pwStruct
from pathlib import Path
from dotenv import load_dotenv
import pyperclip
from key_manager import KeyManager

pw_struct = pwStruct()
key_manager = None
JSON_FILE_PATH = ""

def init():
    """
    initialize the password key manager, set JSON file path, and
    ensure the on-disk password store exists and is valid.
    """
    global JSON_FILE_PATH
    global key_manager
    global pw_struct

    key_manager = KeyManager.new_env(os.path.join(os.getcwd(), ".env"))
    load_dotenv()
    JSON_FILE_PATH = os.getenv("PWD_FILE")

    if not JSON_FILE_PATH:
        raise RuntimeError("PWD_FILE environment variable is not set")

    # create a new file if file does not exist
    if not os.path.exists(JSON_FILE_PATH):
        # pw_struct was already initialized with created/last_modified timestamps
        data = {
            "pass-list": {},
            "meta": {
                "created_at": pw_struct.created,
                "last_modified": pw_struct.last_modified,
            },
        }
        try:
            with open(JSON_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            raise RuntimeError(f"Failed to create file at '{JSON_FILE_PATH}': {e}")

        print(
            f"Password store file '{JSON_FILE_PATH}' did not exist. "
            "Created new file with empty structure."
        )
        return

    # otherwise, strictly load existing file
    pw_struct = pwStruct.load_from_file(JSON_FILE_PATH, key_manager)
    print(f"Password store file '{JSON_FILE_PATH}' exists and was loaded successfully.")

def add_pass():
    """
    create a new password object
    """
    global pw_struct
    input_service = input("Enter the site this login will be used for: ")
    input_usr = input("Enter the username: ")
    input_pwd = getpass.getpass(prompt="Enter your password: ")
    input_url = input("Enter the url of the site, otherwise press enter: ")

    new_pw = pw(input_usr, input_pwd, input_service, key_manager, input_url)
    pw_struct.add_pw(new_pw)
    pw_struct.save_to_file(JSON_FILE_PATH)
    print("added")


def copy_to_clipboard(text: str) -> None:
    """
    Copy the given text to the system clipboard.

    Uses pyperclip so it can work across platforms.
    """
    try:
        pyperclip.copy(text)
    except Exception as e:
        print(f"Failed to copy to clipboard: {e}")


def rem_pass(service, username):
    print("removed")
    
def get_pass():
    """
    return the usernames/passwords for a specific service
    """
    global pw_struct
    input_service = input("Enter the site to find logins for: ")
    service = input_service.strip()

    if not service:
        print("Error: service name must not be empty.")
        return

    try:
        creds = pw_struct.get_pw(service)
    except ValueError as e:
        print(f"Error: {e}")
        return
    except KeyError:
        print(f"No logins stored for service '{service}'.")
        return

    if not creds:
        print(f"No logins found for service '{service}'.")
        return

    # Single-login case: auto-copy password
    if len(creds) == 1:
        username, password = creds[0]
        copy_to_clipboard(password)
        print(f"Found 1 login for '{service}' with username: {username}")
        print("Password has been copied to the clipboard.")
        return

    # Multiple-logins case: list usernames and ask which to copy
    print(f"Found {len(creds)} logins for '{service}':")
    for idx, (username, _password) in enumerate(creds, start=1):
        print(f"[{idx}] {username}")

    choice_str = input(
        "Enter the login number to copy its password (or press Enter to cancel): "
    ).strip()

    if choice_str == "":
        print("Cancelled; no password was copied.")
        return

    try:
        choice = int(choice_str)
    except ValueError:
        print("Invalid selection. Please enter a number.")
        return

    if choice < 1 or choice > len(creds):
        print("Selection out of range. No password was copied.")
        return

    username, password = creds[choice - 1]
    copy_to_clipboard(password)
    print(
        f"Password for login {choice} (username: {username}) has been copied to the clipboard."
    )
    
def show_all():
    print("show")

def main():
    parser = argparse.ArgumentParser()
    functions = parser.add_subparsers(dest="command",required = True)
    
    add_pw = functions.add_parser("add")
    
    rem_pw = functions.add_parser("remove")
    rem_pw.add_argument("-s", type=str, required=True)
    rem_pw.add_argument("-u", type=str)

    change_pw = functions.add_parser("change")
    
    get_pw = functions.add_parser("get")
    
    show_pw = functions.add_parser("show")
    
    init_pw = functions.add_parser("init")

    clear_pw = functions.add_parser("clear")
    
    args = parser.parse_args()
    command = args.command
    
    match command:
        case "init":
            init()
        case "add":
            add_pass()
        case "remove":
            rem_pass(args.s, args.u)
        case "change":
            print("changed")
        case "get":
            get_pass()
        case "show":
            show_all()
        case "clear":
            print("cleared")
        case _:
            print("Unknown command, please try again")
    
if __name__ == "__main__":
    main()


