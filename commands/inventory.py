"""
Inventory Commands

Commands for manipulating the players inventory.

"""

import re
from collections import defaultdict
import itertools
import operator
import evennia
from evennia.commands.command import Command
from evennia import CmdSet, utils

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
        items = self.caller.contents
        if not items:
            string = "You are not carrying anything."
        else:
            table = utils.evtable.EvTable("", "|w|yName|n", "|w|yWeight|n",
                                  border="none")
            table.reformat_column(1, width=60, align="l")
            table.reformat_column(2, align="r", valign="b")

            item_list = []
            total_weight = 0

            for item in items:
                item_list.append({"name" : item.name, "mass" : item.get_mass()}) 

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

            string = f"|wYou are carrying: |n\n\n{table}\n\n|YTotal Weight:|n |M{total_weight}|n\n"
        self.caller.msg(string)

class CmdPut(Command):
    """
    put

    Usage:
      put <item> = <container>
      put/all <item> = <container>

    Put an item inside a container.
    """

    pass

class CmdGet(Command):
    """
    pick up something

    Usage:
      get <item>
      get/all <item>
      get <item> = <container>

    Picks up an object from your location or from a
    container and puts it in your inventory.
    """

    key = "get"
    aliases = ["grab","pickup"]
    locks = "cmd:all()"
    arg_regex = r"\s|$"

    def func(self):
        """implements the command."""

        caller = self.caller

        if not self.args:
            caller.msg("Get what?")
            return
        obj = caller.search(self.args.lstrip(), location=caller.location)
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

        # calling at_before_get hook method
        if not obj.at_before_get(caller):
            return

        success = obj.move_to(caller, quiet=True)

        if not success:
            caller.msg("This can't be picked up.")
        else:
            caller.msg("You pick up %s." % obj.name)
            caller.location.msg_contents(
                    "%s picks up %s." % (caller.name, obj.name), exclude=caller
            )
            # calling at_get hook method
            obj.at_get(caller)

class InventoryCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdInventory)
        # self.add(CmdGet)
        self.add(CmdPut)
