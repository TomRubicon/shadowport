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
import typeclasses.rooms as rooms
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
def list_items_clean(caller, show_doing_desc=False, categories=None, exclude=None):
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

    items = sorted(items, key=lambda itm: itm.name)
    item_count = dict(Counter(item.name for item in items))
    counted = []
    string = ""
    # loop_max = len(items) - 1
    loop_max = len(item_count)
    caller.msg_contents(loop_max)

    for loop, item in enumerate(items):
        if item.name in counted:
            continue

        count = item_count[item.name]
        if count > 1:
            name = item.get_numbered_name(count, caller)[1]
        else:
            name = item.get_numbered_name(count, caller)[0]

        doing_desc = ""
        if show_doing_desc and item.db.doing_desc:
            doing_desc = f" {item.db.doing_desc}"

        prefix = ""
        if show_doing_desc and item.db.doing_prefix:
            prefix = f"{items.db.doing_prefix} "

        name = f"{prefix}|w{name}|n{doing_desc}"

        if loop == 0:
            if loop_max == 1:
                string += f"{name}"
            elif loop_max == 2:
                string += f"{name} "
            else:
                string += f"{name}, "
        elif loop > 0 and loop < loop_max - 1:
            if loop < loop_max - 2:
                string += f"{name}, "
            else:
                string += f"{name} "
        else:
            string += f"and {name}"

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
                caller_name = f"|w{caller.name}|n"
                item_name = f"|w{obj.get_numbered_name(1, caller)[0]}|n"
                container_name = f"|w{container}|n"
                
                rooms.dark_aware_msg(
                    "{character} puts {item_name} into {container_name}.",
                    location,
                    {"{character}":caller_name, "{item_name}":item_name, "{container_name}":container_name},
                    {"{character}":"|wSomeone|n", "{item_name}":"|wsomething|n", "{container_name}":"|wsomething else|n"},
                    caller
                )

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
        container_msg_dark = ""

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
                container_msg_dark = f" from |wsomething else|n"
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
                container_msg_dark = f" from |wsomething else|n"
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
                caller_name = caller.name
                obj_name = obj.get_numbered_name(1, caller)[0]
                rooms.dark_aware_msg(
                    "|w{character}|n gets |w{obj_name}|n{container_msg}.",
                    location,
                    {"{character}":caller_name, "{obj_name}":obj_name, "{container_msg}":container_msg},
                    {"{character}":"Someone", "{obj_name}":"something", "{container_msg}":container_msg_dark},
                    caller
                        )
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
        location = caller.location
        
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
            caller.msg(f"You aren't carrying |w{self.lhs}|n.")
            return

        for obj in obj_list:
            if not obj:
                continue
            
            if obj.db.worn:
                caller.msg(f"|w{obj.name}|n is worn. |wRemove|n it before dropping.")
                continue

            # Call the object script's at_before_drop() method.
            if not obj.at_before_drop(caller):
                continue

            success = obj.move_to(caller.location, quiet=True)
            if not success:
                caller.msg(f"|w{obj.name}|n couldn't be dropped.")
            else:
                caller.msg(f"You drop |w{obj.name}|n.")
                caller_name = caller.name
                obj_name = obj.get_numbered_name(1, caller)[0]
                
                rooms.dark_aware_msg(
                   "|w{character}|n drops |w{obj_name}|n.",
                   location,
                   {"{character}":caller_name, "{obj_name}":obj_name},
                   {"{character}":"Someone", "{obj_name}":"something"},
                   caller
                )
                # if location.db.dark:
                #     caller_name = "Someone"
                #     obj_name = "something"
                # caller.location.msg_contents(f"|w{caller_name}|n drops |w{obj_name}|n.", exclude=caller)
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

class CmdUse(MuxCommand):
    """
    Use an item on your self or someone else.

    Usage:
      use <obj>
      use <obj> on <character>

    """

    key = "use"
    help_category = "Inventory and Equipment"
    locks = "cmd:all()"
    rhs_split = ("=", " on ")
    adjective = "usable"

    def find_item(self, caller):
        item = caller.search(
            self.lhs,
            location=caller,
            use_nicks=True,
            quiet=True,
        )
        if not item:
            caller.msg(f"You aren't carrying |w{self.lhs}|n.")
            return
        return item[0]

    def func(self):
        """
        This performs the actual command
        """
        caller = self.caller
        target = None
        
        if not self.lhs:
            caller.msg(f"{self.key.capitalize()} what?")
            return
        # find item in inventory
        item = self.find_item(caller)

        if not item:
            return

        # check if consumable
        if not item.is_typeclass("typeclasses.objects.Consumable"):
            caller.msg(f"|w{item.name}|n is not {self.adjective}.")
            return

        # check if this consumable is a USE type. (as opposed to eat or drink)
        if not item.db.consume_type == self.key:
            caller.msg(f"|w{item.name}|n is not {self.adjective}. Try the |w{item.db.consume_type}|n command instead.")
            return

        # check for target
        if self.rhs:
            target = caller.search(
                self.rhs,
                location=caller.location,
                use_nicks=True,
                quiet=True
            )
            target = target[0]

            if not target:
                caller.msg(f"No one named |w{self.rhs} here.")
                return

            if not target.is_typeclass("typeclasses.characters.Character"):
                caller.msg(f"{target.name} is not a character.")
                return
        
        item.consume(caller, target)
        return

class CmdEat(CmdUse):
    """
    Eat something from your inventory.

    Usage:
      eat <obj>

    """
    
    key = "eat"
    help_category = "Inventory and Equipment"
    locks = "cmd:all()"
    adjective = "edible"

class CmdDrink(CmdUse):
    """
    Drink something from a container in your inventory.

    Usage:
      drink <obj>

    """

    key = "drink"
    help_category = "Inventory and Equipment"
    locks = "cmd:all()"
    adjective = "drinkable"

    def find_item(self, caller):
        item = caller.search(
            self.lhs,
            location=caller,
            use_nicks=True,
            quiet=True,
        )
        if not item:
            caller.msg(f"You aren't carrying |w{self.lhs}|n.")
            return

        if not item[0].contents:
            caller.msg(f"The {item[0].name} is empty.")
            return

        return item[0].contents[0]

class CmdFill(MuxCommand):
    """
    Fill a container with a liquid.

    Usage:
      fill <obj> from <source>

    """

    key = "fill"
    help_category = "Inventory and Equipment"
    locks = "cmd:all()"
    rhs_split = ("=", " from ", " with ")

    def func(self):
        caller = self.caller
        location = caller.location
        
        # Return if no args
        if not self.lhs:
            caller.msg("Fill what?")
            return

        # find LiquidContainer to fill
        container = caller.search(
            self.lhs,
            location=[location, caller],
            use_nicks=True,
            quiet=True
        )

        # if no container
        if not container:
            caller.msg(f"You aren't carrying |w{self.lhs}|n.")
            return

        # check if item is liquid container
        if not container[0].is_typeclass("typeclasses.objects.LiquidContainer"):
            caller.msg(f"|w{container[0].name}|n can't be filled with liquid.")
            return

        # check if source is specified
        if not self.rhs:
            caller.msg(f"Fill |w{container[0].name}|n with what?")
            return
        
        # find source to fill from
        source = caller.search(
            self.rhs,
            location=[location, caller],
            use_nicks=True,
            quiet=True
        )

        # if no source
        if not source:
            caller.msg(f"Can't find {self.rhs} to fill from.")
            return

        # check if source is another container or a puddle
        if (
            not source[0].is_typeclass("typeclasses.objects.LiquidContainer")
            and not source[0].is_typeclass("typeclasses.objects.Liquid")
        ):
            caller.msg(f"|w{source[0].name}|n is not a liquid or a container.")
            return
        
        container[0].fill(source[0], caller)

class CmdDump(MuxCommand):
    """
    Dump the contents of a container filled with liquid onto the ground.

    Usage:
      dump <obj>

    """

    key = "dump"
    help_category = "Inventory and Equipment"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        location = caller.location

        if not self.lhs:
            caller.msg("Dump what?")
            return

        container = caller.search(
            self.lhs,
            location=caller,
            use_nicks=True,
            quiet=True
        )

        if not container:
            caller.msg(f"You aren't carrying |w{self.lhs}|n.")
            return

        if not container[0].is_typeclass("typeclasses.objects.LiquidContainer"):
            caller.msg("You can't dump this.")
            return

        liquid = container[0].contents[0].name
        success = container[0].dump(location)
        if success:
            caller.msg(f"You dump the |w{container[0].name}|n filled with |w{liquid}|n onto the ground.")
            rooms.dark_aware_msg(
                "|w{character}|n dumps |w{object}|n filled with |w{liquid}|n onto the ground.",
                location,
                {"{character}":caller.name, "{object}":container[0].name, "{liquid}":liquid},
                {"{character}":"Someone", "{object}":"something", "{liquid}":"something"},
                caller
            )

class InventoryCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdInventory)
        self.add(CmdGet)
        self.add(CmdPut)
        self.add(CmdDrop)
        self.add(CmdWear)
        self.add(CmdRemove)
        self.add(CmdUse)
        self.add(CmdEat)
        self.add(CmdDrink)
        self.add(CmdFill)
        self.add(CmdDump)
