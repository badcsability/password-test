#!/usr/bin/env python3
import argparse
import hashlib
import base64
import os
import json
from pw_class import pw, loginList, pwStruct
from pathlib import Path
from dotenv import load_dotenv
from key_manager import KeyManager

JSON_FILE_PATH = ""


def init():
    global JSON_FILE_PATH
    created = KeyManager.new_env(os.path.join(os.getcwd(), ".env"))
    load_dotenv()
    JSON_FILE_PATH = os.getenv("PWD_FILE")
    print(JSON_FILE_PATH)
    if not os.path.exists(JSON_FILE_PATH):
        data = {
            "pass-list": {},
            "services": {},
        }
        try:
            with open(JSON_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            print(f"Failed to create file at '{JSON_FILE_PATH}': {e}")
            return

        print(
            f"Password store file '{JSON_FILE_PATH}' did not exist. "
            "Created new file with empty structure."
        )
        return

    if not os.path.isfile(JSON_FILE_PATH):
        print(f"Path '{JSON_FILE_PATH}' exists but is not a regular file.")
        return

    try:
        with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
        data = json.loads(content)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Password store file '{JSON_FILE_PATH}' is invalid JSON: {e}")
        return

    if not isinstance(data, dict):
        print(
            f"Password store file '{JSON_FILE_PATH}' is invalid: "
            "top-level JSON value must be an object."
        )
        return

    if "pass-list" not in data or "services" not in data:
        print(
            f"Password store file '{JSON_FILE_PATH}' is invalid: "
            "missing 'pass-list' or 'services' keys."
        )
        return

    if not isinstance(data["pass-list"], dict) or not isinstance(
        data["services"], dict
    ):
        print(
            f"Password store file '{JSON_FILE_PATH}' is invalid: "
            "'pass-list' must be an object and 'services' must be an object."
        )
        return

    print(f"Password store file '{JSON_FILE_PATH}' exists and is valid.")

def add_pass(service, password, username):
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
    add_pw.add_argument("-u", type=str, required=True)
    add_pw.add_argument("-p", type=str, required=True)
    add_pw.add_argument("-s", type=str, required=True)
    
    rem_pw = functions.add_parser("remove")
    rem_pw.add_argument("-s", type=str, required=True)
    rem_pw.add_argument("-u", type=str)
    
    get_pw = functions.add_parser("get")
    get_pw.add_argument("-su", type=str)
    
    show_pw = functions.add_parser("show")
    
    init_pw = functions.add_parser("init")
    
    args = parser.parse_args()
    command = args.command
    
    match command:
        case "init":
            init()
        case "add":
            add_pass(args.u, args.p, args.s)
        case "remove":
            rem_pass(args.s, args.u)
        case "get":
            get_pass(args.su)
        case "show":
            show_all()
        case _:
            print("Unknown command, please try again")
    
if __name__ == "__main__":
    main()


