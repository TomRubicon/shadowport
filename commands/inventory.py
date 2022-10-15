"""
Inventory Commands

Commands for manipulating the players inventory.

"""

import re
import itertools
from collections import Counter
from evennia.commands.command import Command
from evennia.commands.default.muxcommand import MuxCommand
from evennia import CmdSet, utils
from typeclasses.clothing import single_type_count, clothing_type_count, get_worn_clothes
from typeclasses.clothing import CLOTHING_OVERALL_LIMIT, CLOTHING_TYPE_LIMIT, WEARSTYLE_MAXLENGTH

CATEGORY_PRIORITY = [
        "weapon",
        "ammo",
        "clothing",
        "medical",
        "container",
        "consumable",
        "tool",
        "material",
        "misc"
        ]
# Helpers
def list_items_clean(caller, categories=None, exclude=None):
    items = []
    if categories:
        for category in categories:
            for item in caller.contents:
                if item.is_typeclass("typeclasses.exits.Exit", exact=False):
                    continue
                if item.is_typeclass("typeclasses.characters.Character", exact=False):
                    continue
                if item.db.category == category:
                    items.append(item)

    elif exclude:
        for excluded in exclude:
            for item in caller.contents:
                if item.db.category == excluded:
                    continue
                if item.is_typeclass("typeclasses.exits.Exit", exact=False):
                    continue
                if item.is_typeclass("typeclasses.characters.Character", exact=False):
                    continue
                items.append(item)
    else:
        items = [item for item in caller.contents]

    item_count = dict(Counter(item.name for item in items))
    counted = []
    string = ""
    loop = 0
    loop_max = len(items) - 1
    caller.msg_contents(loop_max)

    for item in items:
        if item.name in counted:
            continue
        count = item_count[item.name]
        if count > 1:
            name = item.get_numbered_name(count, caller)[1]
        else:
            name = item.get_numbered_name(count, caller)[0]
        if loop == 0 and loop_max == count - 1:
            string += f"|w{name}|n"
        elif loop == 0 and loop_max > 1:
            string += f"|w{name}|n, "
        elif loop > 0 and loop < loop_max:
            string += f"|w{name}|n, "
        elif loop == loop_max:
            string += f"and |w{name}|n"
        counted.append(item.name)
        loop += count

    return string


def display_contents(caller, empty_msg, carrying_msg, for_container=False):
    items = caller.contents

    if not items:
        string = empty_msg
    else:
        string = ""
        
        total_mass = 0
        
        if for_container:
            string += f"|wContents of {caller.name}:|n\n\n"

        for category in CATEGORY_PRIORITY:
            items_by_category = [item for item in items if item.attributes.get("category", "misc") == category]
            if not items_by_category:
                continue

            items_by_category = sorted(items_by_category, key=lambda itm: itm.name)
            item_count = dict(Counter(item.name for item in items_by_category))
            string += f"|w{category.capitalize()}:|n\n"
            counted = []

            for item in items_by_category:
                if for_container:
                    total_mass += item.get_mass_modified(caller.db.mass_reduction)
                    mass = item.get_mass_modified(caller.db.mass_reduction)
                else:
                    total_mass += item.get_mass()
                    mass = item.get_mass()
                # Skip if the item has already been counted and is not worn.
                if item.name in counted and not item.db.worn:
                    continue
                count = item_count[item.name]
                if item.db.worn:
                    string += f"    {item.get_numbered_name(1, caller)[0]} |m(worn)|n |Y[{mass:.2f} lbs]|n\n"
                else:
                    mass = 0
                    notworn = [itm for itm in items_by_category if itm.name == item.name and not itm.db.worn]
                    for itm in notworn:
                        if for_container:
                            mass += itm.get_mass_modified(caller.db.mass_reduction)
                        else:
                            mass += itm.get_mass()
                    if count > 1:
                        name = item.get_numbered_name(count, caller)[1]
                    else:
                        name = item.get_numbered_name(count, caller)[0]
                    string += f"    {name} |Y[{mass:.2f} lbs]|n\n"
                    counted.append(item.name)
        if for_container:
            capacity = caller.db.capacity
            remaining_space = capacity - total_mass
            string += f"[|Y Total Weight:|n |M{total_mass:.2f}|n/|M{capacity:.2f}|n ]\n"
        else:
            string += f"[|Y Total Weight:|n |M{total_mass:.2f}|n ]\n"

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
    rhs_split = ("=", " in ")
    
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
            obj_mass = obj.get_mass_modified(container.db.mass_reduction)
            container_free_space = container.db.capacity - container.get_contents_mass()

            if obj_mass > container_free_space:
                caller.msg(f"There is not enough room in {container.name} to fit {obj.name}")
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
    rhs_split = ("=", " from ")
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

class CmdWear(MuxCommand):
    """
    Puts on an item of clothing/armor you are holding.

    Usage:
      wear <obj> [wear style]

    Examples:
      wear shirt
      wear scarf wrapped loosely about the shoulders

    All the clothes you are wearing are appended to your description.
    If you provide a 'wear style' after the command, the message you
    provide will be displayed after the clothing's name.
    """

    key = "wear"
    help_category = "Inventory and Equipment"

    def func(self):
        """
        This performs the actual command.
        """
        caller = self.caller
        if not self.args:
            caller.msg("Usage: wear <obj> [wear style]")
            return
        clothing = caller.search(self.arglist[0], candidates=caller.contents)
        wearstyle = True
        if not clothing:
            caller.msg("Thing to wear must be in your inventory.")
            return
        if not clothing.is_typeclass("typeclasses.clothing.Clothing", exact=False):
            caller.msg("That's not clothes!")
            return

        # Enforce overall clothing limit.
        if CLOTHING_OVERALL_LIMIT and len(get_worn_clothes(self.caller)) >= CLOTHING_OVERALL_LIMIT:
            caller.msg("You can't wear any more clothes.")
            return

        # Apply individual clothing type limits.
        if clothing.db.clothing_type and not clothing.db.worn:
            type_count = single_type_count(get_worn_clothes(caller), clothing.db.clothing_type)
            if clothing.db.clothing_type in list(CLOTHING_TYPE_LIMIT.keys()):
                if type_count >= CLOTHING_TYPE_LIMIT[clothing.db.clothing_type]:
                    caller.msg(
                        "You can't wear any more clothes of the type '%s'."
                        % clothing.db.clothing_type
                    )
                    return

        if clothing.db.worn and len(self.arglist) == 1:
            caller.msg("You're already wearing %s!" % clothing.name)
            return
        if len(self.arglist) > 1: # If wearstyle arguments given
            wearstyle_list = self.arglist
            del wearstyle_list[0] # Leave first argument (the clothing item) out of the wearstyle
            wearstring = " ".join(
                str(e) for e in wearstyle_list
            ) # Join list of args back into one string
            if (WEARSTYLE_MAXLENGTH and len(wearstring) > WEARSTYLE_MAXLENGTH):
                caller.msg("Please keep your wear style message to less than %i characters."
                           % WEARSTYLE_MAXLENGTH)
            else:
                wearstyle = wearstring
        clothing.wear(self.caller, wearstyle)

class CmdRemove(MuxCommand):
    """
    Takes off an item of clothing.

    Usage:
      remove <obj>

    Removes an item of clothing you are wearing. You can't remove
    clothes that are covered up by something else - you must take
    off the covering item first.
    """

    key = "remove"
    help_category = "Inventory and Equipment"

    def func(self):
        """
        This performs the actual command.
        """
        caller = self.caller
        clothing =  caller.search(self.args, candidates=caller.contents)
        if not clothing:
            caller.msg("Thing to remove must be carried or worn.")
            return
        if not clothing.db.worn:
            caller.msg("You're not wearing that!")
            return
        if clothing.db.covered_by:
            caller.msg("You have to take off %s first." % clothing.db.covered_by.name)
            return
        clothing.remove(caller)


class InventoryCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdInventory)
        self.add(CmdGet)
        self.add(CmdPut)
        self.add(CmdDrop)
        self.add(CmdWear)
        self.add(CmdRemove)
