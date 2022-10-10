"""
Inventory Commands

Commands for manipulating the players inventory.

"""

import re
import itertools
import evennia
from evennia.commands.command import Command
from evennia.commands.default.muxcommand import MuxCommand
from evennia import CmdSet, utils

def display_contents(caller, empty_msg, carrying_msg):
    items = caller.contents

    if not items:
        string = empty_msg
    else:
        table = utils.evtable.EvTable("", "|w|yName|n", "|w|yWeight|n",
                              border="none")
        table.reformat_column(1, width=60, align="l")
        table.reformat_column(2, align="r", valign="b")

        item_list = []
        total_weight = 0

        for item in items:
            item_list.append({"name" : item.name, "mass" : item.get_mass()}) 

        item_list = sorted(item_list, key=lambda itm: itm["name"])

        for name, item in itertools.groupby(item_list, key=lambda itm: itm["name"]):
            items = list(item)
            count = len(items)
            mass = 0
            for i in items:
                mass += i["mass"]
            total_weight += mass
            mass = f"|M{mass}|n"
            count = f"|mx{count}|n"
            name = f"{count} {name}"
            table.add_row("|W*|n",name, mass)

        string = f"|w{carrying_msg}: |n\n\n{table}\n\n|YTotal Weight:|n |M{total_weight}|n\n"
    
    return string

class CmdInventory(Command):
    """
    view inventory

    Usage:
      inventory
      inv

    Shows the contents of your inventory.
    """

    key = "inventory"
    aliases = ["i", "inv"]
    help_category = "Inventory and Equipment"
    locks = "cmd:all()"

    def func(self):
        "check inventory"
        self.caller.msg(display_contents(self.caller, "|wYou are not carrying anything.|n", "You are carrying:"))

class CmdPut(MuxCommand):
    """
    put

    Usage:
      put <item> = <container>
      put/all <item> = <container>
      put/all = <container>

    Put an item inside a container.
    """

    key = "put"
    aliases = ["p", "place"]
    help_category = "Inventory and Equipment"
    locks = "cmd:all()"
    
    def func(self):
        caller = self.caller
        location = caller.location

        # put 
        if not self.lhs and not self.rhs:
            caller.msg("Put what?")
            return
        # put <obj>
        if not self.rhs:
            caller.msg(f"Put {self.lhs} in what?")
            return

        # put/all = <container>
        if not self.lhs and "all" in self.switches and self.rhs:
            obj_list = [obj for obj in caller.contents if obj !=caller and obj.access(caller, "get")] 
        # put <obj> = <container>
        else:
            obj_list = caller.search(
                self.lhs,
                location=caller,
                use_nicks=True,
                quiet=True
            )

        if not obj_list:
            caller.msg(f"You aren't carring |w{self.lhs}|n.")
            return

        container = caller.search(self.rhs)

        if not container:
            return

        # is it a container?
        if not container.db.container:
            caller.msg("You can't put anything in this.")
            return

        for obj in obj_list:
            if not obj:
                return
            if caller == obj:
                caller.msg("You can't put yourself in a container!")
                return
            if container and obj == container:
                caller.msg(f"You can't put {container.name} in itself.")
                return
            if not obj.at_before_get(caller):
                return

            success = obj.move_to(container, quiet=True)

            if not success:
                caller.msg("This can't be put in a container.")
            else:
                caller.msg(f"You put |w{obj.get_numbered_name(1, caller)[0]}|n into |w{container.name}|n.")
                location.msg_contents(f"|w{caller.name}|n puts |w{obj.get_numbered_name(1,caller)[0]}|n into |w{container}|n.", exclude=caller)

            if "all" not in self.switches:
                return

class CmdGet(MuxCommand):
    """
    pick up something

    Usage:
      get <item>
      get/all <item>
      get <item> = <container>
      get/all <item> = <container>

    Picks up an object from your location or from a
    container and puts it in your inventory.
    """

    key = "get"
    aliases = ["grab","pickup"]
    help_category = "Inventory and Equipment"
    locks = "cmd:all()"
    # switch_options = ("all")

    def func(self):
        """implements the command."""

        caller = self.caller
        location = caller.location
        container_msg = ""

        # get
        if not self.lhs and not self.switches:
            caller.msg("Get what?")
            return
        # get/all
        elif not self.lhs and "all" in self.switches:
            if self.rhs:
                container = caller.search(self.rhs)
                if not container:
                    return
                container_msg = f" from |w{container.name}|n"
                obj_list = [obj for obj in container.contents if obj !=caller and obj.access(caller, "get")]
            else:
                obj_list = [obj for obj in location.contents if obj != caller and obj.access(caller, "get")]
        elif self.lhs:
            # get <obj> = <container>
            if self.rhs:
                container = caller.search(self.rhs)
                if not container:
                    return
                container_msg = f" from |w{container.name}|n"
                obj_list = caller.search(
                    self.lhs,
                    location=container,
                    use_nicks=True,
                    quiet=True
                )
            # get <obj>
            else:
                obj_list = caller.search(
                    self.lhs,
                    location=location,
                    use_nicks=True,
                    quiet=True
                )

        if not obj_list:
            if self.lhs:
                caller.msg(f"There is no |w{self.lhs}|n to get here.")
            else:
                caller.msg("There is nothing to get here.")
            return

        for obj in obj_list:
            if not obj:
                return
            if caller == obj:
                caller.msg("You can't get yourself.")
                return
            if not obj.access(caller, "get"):
                if obj.db.get_err_msg:
                    caller.msg(obj.db.get_err_msg)
                else:
                    caller.msg("You can't get that.")
                return

            # calling at_before_get mothod
            if not obj.at_before_get(caller):
                return

            success = obj.move_to(caller, quiet=True)

            if not success:
                caller.msg("This can't be picked up.")
            else:
                caller.msg(f"You get |w{obj.get_numbered_name(1, caller)[0]}|n{container_msg}.")
                location.msg_contents(f"|w{caller.name}|n gets |w{obj.get_numbered_name(1,caller)[0]}|n{container_msg}.", exclude=caller)
                obj.at_get(caller)
            
            if "all" not in self.switches:
                return

class CmdDrop(MuxCommand):
    """
    drop something

    Usage:
      drop <obj>
      drop/all <obj>

    Lets you drop an object from your inventory into the
    location you are currently in.
    """

    key = "drop"
    help_category = "Inventory and Equipment"
    locks = "cmd:all()"

    def func(self):
        """implement command"""

        caller = self.caller
        
        # drop
        if not self.lhs and not self.switches:
            caller.msg("Drop what?")
            return
        # drop/all 
        elif not self.lhs and "all" in self.switches:
            obj_list = [obj for obj in caller.contents]
        # drop/all <obj>
        elif self.lhs: 
            obj_list = caller.search(
                self.lhs,
                location=caller,
                use_nicks=True,
                quiet=True
            ) 

        if not obj_list:
            caller.msg(f"You aren't carrying {self.lhs}.")
            return

        for obj in obj_list:
            if not obj:
                return

            # Call the object script's at_before_drop() method.
            if not obj.at_before_drop(caller):
                return

            success = obj.move_to(caller.location, quiet=True)
            if not success:
                caller.msg(f"{obj.name} couldn't be dropped.")
            else:
                caller.msg(f"You drop {obj.name}.")
                caller.location.msg_contents(f"{caller.name} drops {obj.name}", exclude=caller)
                obj.at_drop(caller)

            # Only drop the first item if all is not specified.
            if "all" not in self.switches:
                return

class InventoryCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdInventory)
        self.add(CmdGet)
        self.add(CmdPut)
        self.add(CmdDrop)
