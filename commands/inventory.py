"""
Inventory Commands

Commands for manipulating the players inventory.

"""

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

class InventoryCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdInventory)
