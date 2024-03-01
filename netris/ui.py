# Module for CLI UI elements
# Import third-party modules
import os
import sys

def inline_print(output):
    sys.stdout.write(output)
    sys.stdout.flush()

def wrap(msg, max_len):
    line = ""
    wrapped = ""
    for word in msg.split():
        if len(line + word) > max_len:
            wrapped += f"{line}\n"
            line = f"{word} "
        else:
            line += f"{word} "
    if len(line) > 0:
        wrapped += line
    return wrapped

def header(title, **kwargs):
    line = kwargs.get('line') if kwargs.get('line') else "".join(["—" for x in range(50)])
    os.system("clear")
    return "\n".join([line, title, line, ""])
    # print(line)
    # print(wrap(title, wrap_len))
    # print(line)
    # print("")

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