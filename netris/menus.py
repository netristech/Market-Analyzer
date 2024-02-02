# module and class for handling terminal menus
# import third-party modules
import os
import sys

# Import internal Modules
from netris import fsops
import netris.ui as ui

class Menu:
    def __init__(self, menu):
        self.menu = menu
        self.active = menu.get('main')
        self.names = menu.keys()

    def display(self):
        # Displays the active menu in the terminal,
        # if the user's selection is another menu, the active menu is changed
        # otherwise, the action that corresponds to the users selection is returned
        items = self.active.get('items')
        empty = True if len(items) < 1 else False
        if empty:
            items =  [{ "name": "No items found...", "action": None }]
        main = True if self.active == self.menu.get('main') else False
        split = True if len(items) > 9 else False
        for i in range(0, len(items), 9):
            last = True if split and i + 9 >= len(items) else False
            ui.header(self.active.get('title'))
            for j in range(len(items[i:i+9])):
                if empty:
                    print(f"{items[i+j].get('name')}")
                else:
                    print(f"{str(j + 1)}: {items[i+j].get('name')}")
            if split and not last:
                print("m: More items.. ")
            if not main:
                print(f"r: Return to {self.menu.get(self.active.get('parent')).get('title')}")
            print("x: Exit")
            print("")
            selection = input("Enter selection: ")
            try:
                if selection in ui.responses("exit"):
                    return "exit"
                elif not main and selection in ui.responses("return"):
                    self.active = self.menu.get(self.active.get('parent'))
                    break
                elif split and not last and selection in ui.responses("more"):
                    continue
                else:
                    action = items[i + int(selection) - 1].get('action')
                    if self.menu.get(action) is not None:
                        self.active = self.menu.get(action)
                        break
                    else:
                        return action
            except:
                break
    
    def update(self, **kwargs):
        # Updates menu items; note: this overwrites the existing menu items
        try:
            for k,v in kwargs.items():
                self.menu.get(k).update(items=[{ "name": x, "action": f"{k}:{x}" } for x in v])
        except:
            pass

    def update_subs(self, **kwargs):
        # Updates menu items for all sub menus of the parent menu passed in <kwargs>
        try:
            for k,v in kwargs.items():
                for name in self.names:
                    if k == self.menu.get(name).get('parent'):
                        self.menu.get(name).update(items=[{ "name": x, "action": f"{name}:{x}" } for x in v])
        except:
            pass