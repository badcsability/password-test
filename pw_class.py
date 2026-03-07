
import os
import struct
from dotenv import load_dotenv
from key_manager import KeyManager

class pw:
    """
    structure to store the login information of a single account
    """
    def __init__(self, user, pwd, service, key, url=""):
        #only username and password need to be encrypted
        
        if not key:
            #if no encryption key is provided, raise an error
            raise ValueError("encryption key not found")
        self.user = key.encrypt(user)
        self.pwd = key.encrypt(pwd)
        self.service = service
        self.url = url
        self.key
        
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
            "service" : self.service,
            "user" : self.user,
            "pwd" : self.pwd,
            "url" : self.url
        }

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
            "site-name" : self.site_name,
            "logins" : [login.serialize() for login in self.logins]
        }

class pwStruct:
    """
    password structure to store lists of logins for various services(eg. gmail, amazon)
    """
    def __init__(self):
        self.pass_list = {}
        self.services = set()
        
    def serialize(self):
        """
        convert all lists of logins into json format
        """
        return {
            "pass-list" : {
                service: login_list.serialize() for service, login_list in self.pass_list.items()
            },
            "services" : list(self.services)
        }
        
   
