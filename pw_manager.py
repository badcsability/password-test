#!/usr/bin/env python3
import argparse
import base64
import os


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
        caes "init":
            print("init")
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


