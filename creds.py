# module for handling credentials
# import thrid-party modules
import os
from getpass import getpass

# Import internal modules
from netris import fsops
from netris.printing import inline_print
import netris.ui as ui

class Credential:
    def __init__(self, cred):
        self.username = cred.get('username')
        self.priv_key = cred.get('priv_key')
        self.password = cred.get('password')
    
    def update(self):
        updated = False
        nun = input(f"Enter new username or press 'Enter' to keep current value: ")
        if nun != "":
            self.username = nun
            updated = True
        npk = input(f"Enter new path to private key file or press 'Enter' to keep current value: ")
        if npk != "":
            if fsops.read_file(npk, type="key", silent=True) is not None:
                self.priv_key = npk
                updated = True
            else:
                print("Key file not found, leaving at current value.")
        npw = getpass("Enter new password or press 'Enter' to keep current password: ")
        if npw != "":
            self.password = npw
            updated = True
        return updated

def get_credentials():
    # Returns a dictionary containing credential data from user input
    data = {}
    while True:
        try:
            name, username, priv_key, password = ("" for x in range(4))
            name = input("Enter a unique name to identify this credential (e.g. firewall-admin-account): ")
            if name == "":
                raise Exception("name cannot be blank")
            username = input("Username: ")
            if username == "":
                raise Exception("Username cannot be blank")
            if input("Does this credential require a private key? (y/n): ") in ui.responses("yes"):
                priv_key = input("Enter full path to private key file: ")
                if priv_key == "" or fsops.read_file(priv_key, type="key", silent=True) is None:
                    raise Exception("Private key file not found")
            if input("Does this credential require a password? (y/n): ") in ui.responses("yes"):
                password = getpass("Password: ")
            data.update({
                name: {
                    "username": username,
                    "password": password,
                    "priv_key": priv_key
                }
            })
            if input(ui.prompts("additional", message="credentials")) in ui.responses("no"):
                break
        except Exception as e:
            if input(ui.prompts("quit", message=f"{e}. ")) in ui.responses("quit"):
                break
    return data   

# DEPRICATED
# def get_creds(cred_key, cred_file):
#     # generate key and store in key file
#     key = Fernet.generate_key()
#     with open(cred_key, "wb") as key_file:
#         key_file.write(key)
#     f = Fernet(key)
#     # gather and store credential sets
#     creds = []
#     while True:
#         i = input("How many credential sets would you like to enter? (1 - 5): ")
#         try:
#             if int(i) in range (1,6):
#                 for i in range(int(i)):
#                     print(f"Enter credential set {i + 1}")
#                     username = input("Username: ")
#                     password = getpass("Password: ")
#                     creds.append({"username": username, "password": password})
#             else:
#                 raise Exception()
#         except:
#             if input("Invalid input. Press any key to continue or 'q' to quit: ") == "q":
#                 sys.exit()
#         else:
#             break
#     # write encrypted credentials to creds file
#     if input("Do you want to cache (encrypted) credentials for future use? [y/n]: ") == "y":
#         n_print.inline("Encrypting and caching credential file to disk... ")
#         try:
#             with open(cred_file, "wb") as file:
#                 file.write(f.encrypt(str(creds).encode('utf-8')))
#         except:
#             print("[FAILED]")
#         else:
#             print("[OK]")
#     return creds