#key manager
import os
from pathlib import Path
from cryptography.fernet import Fernet
from dotenv import load_dotenv, set_key

class KeyManager():
    def __init__(self, env_path):
        """
        initialize key manager with path to env file
        """
        self.env_path = Path(env_path)
        self.env_path.parent.mkdir(parents=True, exist_ok=True)

        load_dotenv(self.env_path)
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            raise ValueError("Encryption key not found")
        
        self.cipher = Fernet(key.encode())
       
    @classmethod
    def new_env(cls, env_path):
        """
        generate and save new key to .env file
        MUST be called before init
        """
        env_path = Path(env_path)
        env_path.parent.mkdir(parents=True, exist_ok=True)
        
        load_dotenv(env_path)
        if os.getenv("ENCRYPTION_KEY"):
            print("Encryption key already exists")
        else:
            key = Fernet.generate_key().decode()
            set_key(env_path, "ENCRYPTION_KEY", key)
        return cls(env_path)
        
    def encrypt(self, plaintext):
        """Encrypt string data"""
        if not plaintext:
            return ""
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext):
        """Decrypt string data"""
        if not ciphertext:
            return ""
        return self.cipher.decrypt(ciphertext.encode()).decode()
