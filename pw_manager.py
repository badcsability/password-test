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

def rem_pass(service, username):
    print("removed")
    
def get_pass(service_username):
    print("got")
    
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
    get_pw.add_argument("-su", type=str)
    
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
            get_pass(args.su)
        case "show":
            show_all()
        case "clear":
            print("cleared")
        case _:
            print("Unknown command, please try again")
    
if __name__ == "__main__":
    main()


