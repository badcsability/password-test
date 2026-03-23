
import os
import struct
import time
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
from key_manager import KeyManager



class pw:
    """
    structure to store the login information of a single account
    """
    def __init__(self, user, pwd, service, key, url="None", *, encrypted: bool = False):
        """
        Initialize a pw instance.

        If encrypted is False (default), user and pwd are treated as plaintext
        and will be encrypted with the provided key.
        If encrypted is True, user and pwd are treated as ciphertext and stored
        as-is without additional encryption.
        """

        if not key:
            raise ValueError("encryption key not found")

        if encrypted:
            self.user = user
            self.pwd = pwd
        else:
            self.user = key.encrypt(user)
            self.pwd = key.encrypt(pwd)
        self.service = service
        self.created_at = datetime.now(timezone.utc).timestamp()
        self.last_accessed = datetime.now(timezone.utc).timestamp()
        self.url = url
        self.key = key
        
    def show_usr(self):
        return self.key.decrypt(self.user)
        
    def show_pwd(self):
        return self.key.decrypt(self.pwd)
    
    def update_pwd(self, new_pwd):
        self.pwd = self.key.encrypt(new_pwd)
        
    def update_usr(self, new_usr):
        self.user = self.key.encrypt(new_usr)
        
    def serialize(self):
        """
        convert login information to store into JSON file 
        """
        return {
            "service": self.service,
            "user": self.user,
            "pwd": self.pwd,
            "url": self.url,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
        }

    @classmethod
    def from_serialized(cls, data: dict, key: KeyManager) -> "pw":
        """
        Reconstruct a pw instance from a serialized dict without decrypting.
        Expects all required fields to be present and correctly typed.
        """
        required_fields = [
            "service",
            "user",
            "pwd",
            "url",
            "created_at",
            "last_accessed",
        ]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field '{field}' in pw entry")

        service = data["service"]
        user = data["user"]
        pwd = data["pwd"]
        url = data["url"]
        created_at = data["created_at"]
        last_accessed = data["last_accessed"]

        if not isinstance(service, str):
            raise ValueError("Field 'service' must be a string")
        if not isinstance(user, str):
            raise ValueError("Field 'user' must be a string")
        if not isinstance(pwd, str):
            raise ValueError("Field 'pwd' must be a string")
        if not isinstance(url, str):
            raise ValueError("Field 'url' must be a string")
        if not isinstance(created_at, (int, float)):
            raise ValueError("Field 'created_at' must be a number")
        if not isinstance(last_accessed, (int, float)):
            raise ValueError("Field 'last_accessed' must be a number")

        obj = cls(
            user=user,
            pwd=pwd,
            service=service,
            key=key,
            url=url,
            encrypted=True,
        )
        obj.created_at = float(created_at)
        obj.last_accessed = float(last_accessed)
        return obj

class loginList:
    """
    structure to store the logins for a specific service/site in a list
    """
    def __init__(self, site_name):
        self.logins = []
        self.site_name = site_name
        
    def serialize(self):
        """
        convert list of logins into json format
        """
        return {
            "site-name": self.site_name,
            "logins": [login.serialize() for login in self.logins],
        }
    
    def add_pw(self, new_pw:pw):
        """
        append new password object to list of logins
        """
        self.logins.append(new_pw)
        #print("added to loginlist")

    def rem_pw(self, usr:str):
        for login in self.logins:
            if login.show_usr() == usr:
                self.logins.remove(login)

    @classmethod
    def from_serialized(cls, service_name: str, data: dict, key: KeyManager) -> "loginList":
        """
        Reconstruct a loginList for a given service from serialized data.
        """
        if not isinstance(data, dict):
            raise ValueError("loginList data must be an object")

        if "site-name" not in data or "logins" not in data:
            raise ValueError("loginList data must contain 'site-name' and 'logins'")

        site_name = data["site-name"]
        logins_data = data["logins"]

        if not isinstance(site_name, str):
            raise ValueError("'site-name' must be a string")
        if site_name != service_name:
            raise ValueError(
                f"service key '{service_name}' does not match 'site-name' '{site_name}'"
            )
        if not isinstance(logins_data, list):
            raise ValueError("'logins' must be a list")

        lst = cls(site_name=service_name)
        for entry in logins_data:
            if not isinstance(entry, dict):
                raise ValueError("Each login entry must be an object")
            lst.logins.append(pw.from_serialized(entry, key))
        return lst

class pwStruct:
    """
    password structure to store lists of logins for various services(eg. gmail, amazon)
    """
    def __init__(self):
        self.pass_list = {}
        self.created = datetime.now(timezone.utc).timestamp()
        self.last_modified = datetime.now(timezone.utc).timestamp()

    def add_pw(self, new_pw:pw):
        """
        given a PW object, add it to an existing loginList
        or create a new loginList if the service is not in the loginList
        additionally update time for when pw was last modified
        """
        service_name = new_pw.service
        if service_name not in self.pass_list:
            new_login = loginList(service_name)
            self.pass_list[service_name] = new_login
        self.pass_list[service_name].add_pw(new_pw)
        self.last_modified = new_pw.created_at

        print("added") 
    
    def rem_pw(self, service:str, username:str=""):
        """
        Given a service, either clear all logins for that service or for a specific username
        """
        if service not in self.pass_list:
            print(f"This service does not exist")
        if username:
            self.pass_list[service].rem_pw(username)
        else:
            self.pass_list[service].logins = []

    def rem_get(self, service:str):
        """
        Return a list of usernames for a given service for deletion
        """
        if service not in self.pass_list:
            raise ValueError("Service name not in services")
        login_list = self.pass_list[service]
        results = []

        for login in login_list.logins:
            username = login.show_usr()
            results.append(username)

        return results

    def get_pw(self, service: str):
        """
        Return a list of (username, password) tuples for the given service.
        Error handling done in pw_manager
        Updates last_accessed on each returned pw entry.
        """
        login_list = self.pass_list[service]
        results = []

        now_ts = datetime.now(timezone.utc).timestamp()
        for login in login_list.logins:
            username = login.show_usr()
            password = login.show_pwd()
            login.last_accessed = now_ts
            results.append((username, password))

        return results

    def serialize(self):
        """
        convert all lists of logins into json format
        """
        return {
            "pass-list": {
                service: login_list.serialize()
                for service, login_list in self.pass_list.items()
            },
            "meta" : {
                "created_at": self.created,
                "last_modified": self.last_modified,
            }
        }
    def show_all(self):
        """
        return tuple of service and all users connected to each service
        """
        result = []
        services = self.pass_list.keys()
        for service in services:
            tmp = []
            for login in self.pass_list[service].logins:
                user = login.show_usr()
                tmp.append(user)
            result.append((service, tmp))
        return result
    
    def clear(self, file_path):
        """
        clear struct and clean json file
        """
        self.pass_list = {}
        now = datetime.now(timezone.utc).timestamp()
        self.created = now
        self.last_modified = now
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Failed to access '{file_path}' : {e}")

    def save_to_file(self, path: str): 
        data = self.serialize()
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)


    @classmethod
    def load_from_file(cls, path: str, key_manager: KeyManager) -> "pwStruct":
        if not os.path.exists(path):
            raise FileNotFoundError(f"File at {path} not found")
        if not os.path.isfile(path):
            raise RuntimeError(f"File at {path} is not valid")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            raise ValueError("Password store file is empty")

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
             RuntimeError(f"Invalid JSON in '{path}': {e}")

        return cls.from_serialized(data, key_manager)
  

    @classmethod
    def from_serialized(cls, data: dict, key: KeyManager) -> "pwStruct":
        """
        Reconstruct a pwStruct from a top-level serialized dict.
        """
        if not isinstance(data, dict):
            raise ValueError("Top-level password store data must be an object")

        if "meta" not in data or "pass-list" not in data:
            raise ValueError("Password store must contain 'meta' and 'pass-list'")

        meta = data["meta"]
        pass_list_data = data["pass-list"]

        if not isinstance(meta, dict):
            raise ValueError("'meta' must be an object")
        if not isinstance(pass_list_data, dict):
            raise ValueError("'pass-list' must be an object")

        if "created_at" not in meta or "last_modified" not in meta:
            raise ValueError("'meta' must contain 'created_at' and 'last_modified'")

        created_at = meta["created_at"]
        last_modified = meta["last_modified"]

        if not isinstance(created_at, (int, float)):
            raise ValueError("'created_at' must be a number")
        if not isinstance(last_modified, (int, float)):
            raise ValueError("'last_modified' must be a number")

        struct_obj = cls()
        struct_obj.created = float(created_at)
        struct_obj.last_modified = float(last_modified)
        struct_obj.pass_list = {}

        for service_name, service_data in pass_list_data.items():
            if not isinstance(service_name, str):
                raise ValueError("Service names must be strings")
            struct_obj.pass_list[service_name] = loginList.from_serialized(
                service_name, service_data, key
            )

        return struct_obj
   
