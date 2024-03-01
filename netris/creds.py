# module for handling credentials
# import thrid-party modules
from getpass import getpass

# Import internal modules
from netris import fsops
import netris.ui as ui

class Credential:
    def __init__(self, cred):
        self.username = cred.get('username')
        self.priv_key = cred.get('priv_key')
        self.password = cred.get('password')
    
    def update(self, **kwargs):
        wrap_len = kwargs.get('wrap_len') if kwargs.get('wrap_len') else 50
        updated = False
        nun = input(ui.wrap(f"Enter new username or press 'Enter' to keep current value: ", wrap_len))
        if nun != "":
            self.username = nun
            updated = True
        npk = input(ui.wrap(f"Enter new path to private key file or press 'Enter' to keep current value: ", wrap_len))
        if npk != "":
            if fsops.read_file(npk, type="key", silent=True) is not None:
                self.priv_key = npk
                updated = True
            else:
                print("Key file not found, leaving at current value.")
        npw = getpass(ui.wrap("Enter new password or press 'Enter' to keep current password: ", wrap_len))
        if npw != "":
            self.password = npw
            updated = True
        return updated

def get_credentials(**kwargs):
    # Returns a dictionary containing credential data from user input
    wrap_len = kwargs.get('wrap_len') if kwargs.get('wrap_len') else 50
    data = {}
    while True:
        try:
            name, username, priv_key, password = ("" for x in range(4))
            name = input(ui.wrap("Enter a unique name to identify this credential (e.g. firewall-admin): ", wrap_len))
            if name == "":
                raise Exception("name cannot be blank")
            username = input("Username: ")
            if username == "":
                raise Exception("Username cannot be blank")
            if input(ui.wrap("Does this credential require a private key? (y/n): ", wrap_len)) in ui.responses("yes"):
                priv_key = input("Enter full path to private key file: ")
                if priv_key == "" or fsops.read_file(priv_key, type="key", silent=True) is None:
                    raise Exception("Private key file not found")
            if input(ui.wrap("Does this credential require a password? (y/n): ", wrap_len)) in ui.responses("yes"):
                password = getpass("Password: ")
            data.update({
                name: Credential({
                    "username": username,
                    "password": password,
                    "priv_key": priv_key
                })
            })
            if input(ui.prompts("additional", message="credentials")) in ui.responses("no"):
                break
        except Exception as e:
            if input(ui.prompts("quit", message=f"{e}. ")) in ui.responses("quit"):
                break
    return data