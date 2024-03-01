# module for file operations
# import third-party modules
import os
import json
import csv
import yaml
from cryptography.fernet import Fernet

class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

def create_dir(dir):
    # Create the directory <dir> if it does not already exist
    # Returns True when successful
    if not os.path.exists(dir):
        try:
            os.makedirs(dir)
        except:
            pass
        else:
            return True
    return False

def list_dir(dir):
    # If directory <dir> exists, return the contents of the directory as list type
    if os.path.exists(dir):
        file_list = os.listdir(dir)
        file_list.sort()
        return file_list

def get_key(key_file):
    # Attempts to load encryption key from <key_file>;
    # If <key_file> fails to load, a new key is generated and saved
    # Returns a Fernet encryption key object
    key = read_file(key_file, type="key")
    if key is None:
        key = Fernet.generate_key()
        write_file(key, key_file, type="key")
    return Fernet(key)

def read_file(file, **kwargs):
    # Returns the contents of <file> as follows:
    # For CSV Files, the contents are returned as multi-dimensional list (list type with list type elements)
    # For JSON Files, the contents are deserialized and returned as the data type stored in the file
    # For YAML Files, the contents are deserialized and returned as a dict type
    # For all other files, the contents are returned as str type
    # Accepts optional str keyword argument <type>, and optional encryption key keyword argument <key>
    # Returns file contents as either str, list, or dict type when success
    try:
        if os.path.exists(file):
            read_mode = "rb" if kwargs.get('type') == "key" or kwargs.get('key') else "r"
            if kwargs.get('type') == "csv":
                with open(file, read_mode, newline="") as csv_file:
                    if kwargs.get('key'):
                        decrypted = kwargs.get('key').decrypt(csv_file.read())
                        content = list(csv.reader(decrypted.decode('utf-8').splitlines(), delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL))
                    else:
                        content = list(csv.reader(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL))
            elif kwargs.get('type') == "json":
                with open(file, read_mode) as json_file:
                    if kwargs.get('key'):
                        decrypted = kwargs.get('key').decrypt(json_file.read())
                        content = json.loads(decrypted.decode('utf-8').replace("'", "\""))
                    else:
                        content = json.load(json_file)
            elif kwargs.get('type') == "yaml":
                with open(file, read_mode) as yaml_file:
                    if kwargs.get('key'):
                        decrypted = kwargs.get('key').decrypt(yaml_file.read())
                        content = yaml.safe_load(decrypted.decode('utf-8'))
                    else:
                        content = yaml.safe_load(yaml_file)
            else:
                with open(file, read_mode) as other_file:
                    if kwargs.get('key'):
                        decrypted = kwargs.get('key').decrypt(other_file.read())
                        content = decrypted.decode('utf-8')
                    else:
                        content = other_file.read()
            if len(content) < 1: 
                raise Exception(f"{file} is empty")
        else:
            raise Exception(f"{file} does not exist")
    except Exception as e:      
        return e
    else:
        return content
    
def write_file(data, file, **kwargs):
    # <data> should be str, list, or dict type, depending on file type as follows:
    # For CSV files, <data> should be multi-dimensional list type (list type with list type elements).
    # For JSON files, <data> can be dict or list type
    # For YAML files, <data> should be dict type
    # For all other files, <data> can be any type, but typically list or str type.
    # Accepts optional str keyword argument <type>, and optional encryption key keyword argument <key>
    # Returns True when successful
    try:
        write_mode = "wb" if kwargs.get('type') == "key" or kwargs.get('key') else "w"
        if kwargs.get('type') == "csv":
            with open(file, write_mode, newline="") as csv_file:
                if kwargs.get('key'):
                    encrypted = "\n".join([",".join(x) for x in data])
                    csv_file.write(kwargs.get('key').encrypt(encrypted.encode('utf-8')))
                else:
                    writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    writer.writerows(data)
        elif kwargs.get('type') == "json":
            with open(file, write_mode) as json_file:
                if kwargs.get('key'):
                    #json_file.write(kwargs.get('key').encrypt(str(data).encode('utf-8')))
                    json_file.write(kwargs.get('key').encrypt(json.dumps(data).encode('utf-8')))
                else:
                    json.dump(data, json_file, indent=2)
        elif kwargs.get('type') == "yaml":
            with open(file, write_mode) as yaml_file:
                if kwargs.get('key'):
                    yaml_file.write(kwargs.get('key').encrypt(yaml.dump(data, Dumper=NoAliasDumper).encode('utf-8')))
                else:
                    yaml.dump(data, yaml_file, Dumper=NoAliasDumper)
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
        return False
    else:
        return True    

def remove_file(file):
    # <file> should be the full path to a file as a str type
    try:
        os.remove(file)
    except:
        return False
    else:
        return True