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

def ensure_initialized() -> bool:
    """
    If the JSON file and key manager exist, load from file, otherwise initialize json
    """
    if JSON_FILE_PATH and key_manager:
        pw_struct.load_from_file(JSON_FILE_PATH, key_manager)
        return
    else:
        try:
            init()
        except Exception as e:
            print(f"Failed to initialize password store: {e}")


def init():
    """
    set JSON file path, and
    ensure the on-disk password store exists and is valid.
    """
    global JSON_FILE_PATH
    global key_manager
    global pw_struct

    key_manager = KeyManager.new_env(".env")
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
    print(f"Password store file '{JSON_FILE_PATH}' already exists.")



def add_pass():
    """
    create a new password object with prompts for service, user,
    password, and an optional URL
    """
    global pw_struct
    input_service = input("Enter the site this login will be used for: ")
    input_usr = input("Enter the username: ")
    input_pwd = getpass.getpass(prompt="Enter your password: ")
    input_url = input("Enter the url of the site, otherwise press enter: ")

    new_pw = pw(input_usr, input_pwd, input_service, key_manager, input_url)
    pw_struct.add_pw(new_pw)
    pw_struct.save_to_file(JSON_FILE_PATH)


def copy_to_clipboard(text: str) -> None:
    """
    Copy the given text to the system clipboard.

    Uses pyperclip so it can work across platforms.
    """
    try:
        pyperclip.copy(text)
    except Exception as e:
        print(f"Failed to copy to clipboard: {e}")


def rem_pass():
    """
    Remove either all logins or a specific login from a service

    Prompt for a service, return usernames/logins connected to that service
    Prompt to either delete all(0), delete specific(1-n), or cancel(enter)
    """
    global pw_struct
    rem_service = input("Enter the site to remove logins for: ")
    service = rem_service.strip()

    if not service: 
        print("Error: service name must not be empty.")
        return
    try:
        users = pw_struct.rem_get(service)
    except ValueError as e:
        print(f"Error: {e}")
    
    #if no users to delete, inform and then exit function
    if not users:
        print(f"No logins stored for service '{service}'")
        return

    num_logins = len(users)
    
    print(f"Found {num_logins} logins for '{service}':")
    for idx, (username) in enumerate(users, start=1):
        print(f"[{idx}] {username}")

    del_choice_str = input(
    "Enter the number of the login to delete,"
    " 0 to clear all logins, or press enter to cancel: "
    ).strip()

    if del_choice_str == "":
        print(f"Cancelled, no password was deleted")
        return

    try:
        del_choice = int(del_choice_str)
    except:
        print(f"Invalid selection, please enter a number or press enter to cancel")
        return

    if del_choice > num_logins:
        print(f"Invalid input, please enter a number or 0 to clear all")
        return

    if del_choice == 0:
        pw_struct.rem_pw(service, "")
        pw_struct.save_to_file(JSON_FILE_PATH)
        print(f" Deleted {num_logins} logins under {service}")
    else:
        rem_user = users[del_choice-1]
        pw_struct.rem_pw(service, rem_user)
        pw_struct.save_to_file(JSON_FILE_PATH)
        print(f"Deleted {rem_user} from {service}")

    
def get_pass():
    global pw_struct
    """
    return the usernames/passwords for a specific service
    """
    input_service = input("Enter the site to find logins for: ")
    service = input_service.strip()

    if not service:
        print("Error: service name must not be empty.")
        return

    try:
        creds = pw_struct.get_pw(service)
        # Save new time of last access to json file
        pw_struct.save_to_file(JSON_FILE_PATH)
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
    global pw_struct
    """
    show all services and usernames
    """
    data = pw_struct.show_all()
    print(data)


def clear_all():
    global pw_struct
    confirm = input("Are you sure you want to reset the password manager? Respond with y/n: \n")
    if confirm.lower() in ["y", "yes"]:
        try:
            pw_struct.clear(JSON_FILE_PATH)
        except Exception as e:
            print(f"Error: {e}")
            return
        print(f"Password manager cleared and json file removed")
    else:
        print(f"No confirmation given, exiting command")

def show_commands():
    print(f"init: Initializes a new JSON file or checks that a current file exists and is valid")
    print(f"add: Adds a new set of logins, prompting for service, username, password, and website(optional)")
    print(f"remove: Either removes all logins related to a service"
        " or a specific login for that service, if there are multiple")
    print(f"clear: Remove all logins and delete the JSON file")
    print(f"show: Find a specific login given a service, copying the results to the clipboard")
    print(f"change: Change the information of a particular login given a service")
def reset_debug():
    print("clear debug")

def main():
    parser = argparse.ArgumentParser()
    functions = parser.add_subparsers(dest="command",required = True)
    
    add_pw = functions.add_parser("add")
    
    rem_pw = functions.add_parser("remove")

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
            ensure_initialized()
            add_pass()
        case "remove":
            ensure_initialized()
            rem_pass()
        case "change":
            ensure_initialized()
            print("changed")
        case "get":
            ensure_initialized()
            get_pass()
        case "show":
            ensure_initialized()
            show_all()
        case "clear":
            ensure_initialized()
            clear_all()
        case "help":
            show_commands()
        case _:
            print("Unknown command, please try again")
    
if __name__ == "__main__":
    main()


