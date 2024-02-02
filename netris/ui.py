# Module for CLI UI elements
# Import third-party modules
import os

def header(title):
    os.system("clear")
    print("--------------------------------")
    print(title)
    print("--------------------------------")
    print("")

def prompts(p, **kwargs):
    message = kwargs.get('message') if kwargs.get('message') else ""
    return {
        "enter": f"{message}Press 'Enter' to continue: ",
        "quit": f"{message}Enter 'q' to quit or any other key to continue: ",
        "delete": f"Are you sure you want to permanently delete {message}? (y/n): ",
        "additional": f"Would you like to enter additional {message}? (y/n): "
    }.get(p)

def responses(r):
    return {
        "yes": ["Y","y","yes","Yes","YES"],
        "no": ["N","n","no","No","No"],
        "quit": ["Q","q","quit","Quit","QUIT"],
        "exit": ["X","x","exit","Exit","EXIT"],
        "return": ["R", "r", "Return", "return", "RETURN"],
        "more": ["M", "m", "more", "More", "MORE"]
    }.get(r)