# module for file operations
# import third-party modules
import os
import json
import csv
from cryptography.fernet import Fernet

# import internal modules
from netris.printing import inline_print

def create_dir(dir):
    # Create the directory <dir> if it does not already exist
    if not os.path.exists(dir):
        inline_print(f"Creating {dir} directory... ")
        try:
            os.makedirs(dir)
        except:
            print("[FAILED]")
        else:
            print("[OK]")
    return dir

def list_dir(dir):
    # If directory <dir> exists, return the contents of the directory
    if os.path.exists(dir):
        return os.listdir(dir)

def get_key(key_file):
    # Loads encryption key from <key_file>; generates a new key and writes it to <keyfile> if load fails
    key = read_file(key_file, type="key")
    if key is None:
        key = Fernet.generate_key()
        write_file(key, key_file, type="key")
    return Fernet(key)

def read_file(file, **kwargs):
    # Returns the contents of <file> as follows:
    # For CSV Files, the contents are returned as a CSV reader object (iterable)
    # For JSON Files, the contents are deserialized and returned as the data type stored in the file
    # For all other files, the contents are returned as str type
    # Accepts optional str keyword argument <type>, and optional encryption key keyword argument <key>
    if not kwargs.get('silent'):
        inline_print(f"Loading file {file}... ")
    try:
        if os.path.exists(file):
            read_mode = "rb" if kwargs.get('type') == "key" or kwargs.get('key') else "r"
            if kwargs.get('type') == "csv":
                with open(file, read_mode, newline="") as csv_file:
                    if kwargs.get('key'):
                        decrypted = kwargs.get('key').decrypt(csv_file.read())
                        content = csv.reader(decrypted.decode('utf-8').splitlines(), delimiter='', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    else:
                        content = csv.reader(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            elif kwargs.get('type') == "json":
                with open(file, read_mode) as json_file:
                    if kwargs.get('key'):
                        decrypted = kwargs.get('key').decrypt(json_file.read())
                        content = json.loads(decrypted.decode('utf-8').replace("'", "\""))
                    else:
                        content = json.load(json_file)
            else:
                with open(file, read_mode) as other_file:
                    if kwargs.get('key'):
                        decrypted = kwargs.get('key').decrypt(other_file.read())
                        content = decrypted.decode('utf-8')
                    else:
                        content = other_file.read()
            if len(content) < 1: 
                raise Exception()
        else:
            raise Exception()
    except:
        if not kwargs.get('silent'):
            print("[FAILED]")
    else:
        if not kwargs.get('silent'):
            print("[OK]")
        return content
    
def write_file(data, file, **kwargs):
    # <data> must be str, list, or dict type, as follows:
    # For CSV files, <data> should be list type (with list type elements / multi-dimensional list).
    # For JSON files, <data> can be any type, but typically dict or list type.
    # For all other files, <data> can be any type, but typically list or str type.
    # Accepts optional str keyword argument <type>, and optional encryption key keyword argument <key>
    if not kwargs.get('silent'):
        inline_print(f"Writing data to {file}... ")
    try:
        write_mode = "wb" if kwargs.get('type') == "key" or kwargs.get('key') else "w"
        if kwargs.get('type') == "csv":
            with open(file, write_mode) as csv_file:
                if kwargs.get('key'):
                    encrypted = ""
                    for row in data:
                        for item in row:
                            if item == row[-1]:
                                if row == data[-1]:
                                    encrypted += f"{item}"
                                else:
                                    encrypted += f"{item}\n"
                            else:
                                encrypted += f"{item},"
                    csv_file.write(kwargs.get('key').encrypt(encrypted.encode('utf-8')))
                else:
                    writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    writer.writerows(data)
        elif kwargs.get('type') == "json":
            with open(file, write_mode) as json_file:
                if kwargs.get('key'):
                    json_file.write(kwargs.get('key').encrypt(str(data).encode('utf-8')))
                else:
                    json.dump(data, json_file, indent=2)
        else:
            with open(file, write_mode) as other_file:
                if type(data) is list:
                    if kwargs.get('key'):
                        other_file.write(kwargs.get('key').encrypt('\n'.join(data).encode('utf-8')))
                    else:
                        other_file.write('\n'.join(data))
                else:
                    if kwargs.get('key'):
                        other_file.write(kwargs.get('key').encrypt(str(data).encode('utf-8')))
                    else:
                        other_file.write(data)
    except:
        if not kwargs.get('silent'):
            print("[FAILED]")
    else:
        if not kwargs.get('silent'):
            print("[OK]")