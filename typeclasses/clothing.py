from evennia.utils import list_to_string
import typeclasses.rooms as rooms
from typeclasses.objects import Object

# Options start here.
# Maximum character length of 'wear style' strings, or None for unlimited.
WEARSTYLE_MAXLENGTH = 50

# The order in which clothing types appear in the description.
CLOTHING_TYPE_ORDER = [
    "hat",
    "face",
    "fullbody",
    "jacket",
    "shirt",
    "pants",
    "underwear",
    "gloves",
    "socks",
    "shoes",
    "accessory",
]

# The maximum number of each type of clothes that can be worn.  (Replace this with
# a more complicated layering system eventually.)
CLOTHING_TYPE_LIMIT = {"hat": 1, "gloves": 1, "socks": 1, "shoes": 1}
# Max number of clothing items that can be worn.
CLOTHING_OVERALL_LIMIT = 20
# What types of clothes will automatically cover what other types of clothes when worn.
# Note that clothing only gets auto_covered if it's already worn when you put something
# on that auto-covers it - for example, its perfectly possible to have your underwear
# showing if you put them on after your pants.
CLOTHING_TYPE_AUTOCOVER = {
    "fullbody": ["jacket", "shirt", "pants"], 
    "jacket": ["shirt"],
    "pants": ["underwear"],
    "shoes": ["socks"]
}
# Types of clothes that can't be used to cover other clothes.
CLOTHING_TYPE_CANT_COVER_WITH = ["jewelry"]


# Helper Functions


def order_clothes_list(clothes_list):
    """
    Orders a given clothes list by the order specified in CLOTHING_TYPE_ORDER.

    Args:
        clothes_list (list): List of clothing items to put in order

    Returns:
        orders_clothes_list (list): The same list as passed, bu re-orderd
                                    according to the heirarchy of clothing types
                                    specified in CLOTHING_TYPE_ORDER.
    """
    ordered_clothes_list = clothes_list
    # For each type of clothing that exists...
    for current_type in reversed(CLOTHING_TYPE_ORDER):
        # Check each item in the given clothes list.
        for clothes in clothes_list:
            # If the item has a clothing type...
            if clothes.db.clothing_type:
                item_type = clothes.db.clothing_type
                # And the clothing type matches the current type...
                if item_type == current_type:
                    # Move it to the front of the list!
                    ordered_clothes_list.remove(clothes)
                    ordered_clothes_list.insert(0, clothes)
    return ordered_clothes_list

def get_worn_clothes(character, exclude_covered=False):
    """
    Get a list of clothes worn by a given character.

    Args:
        character (obj): The character to get a list of worn clothes from.

    Keyword Args:
        exclude_covered (bool): If True, exclues clothes covered by other
                                clothing from the returned list.

    Returns:
        ordered_clothes_list (list): A list of clothing items worn by the
                                     given character, ordered according to
                                     the CLOTHING_TYPE_ORDER option specified
                                     in this module.
    """
    clothes_list = []
    for item in character.contents:
        # If uncovered or not excluding covered items
        if not item.db.covered_by or exclude_covered is False:
            # If 'worn' is True, add to the list
            if item.db.worn:
                clothes_list.append(item)
    # Might as well put them in order here too.
    ordered_clothes_list = order_clothes_list(clothes_list)
    return ordered_clothes_list

def clothing_type_count(clothes_list):
    """
    Returns a dictionary of the number of each clothing type
    in a given list of clothing objects.

    Args:
        clothes_list (list): A list of clothing items from which
                             to count the number of clothing types
                             represented among them.

    Returns:
        types_count (dict): A Dictionary of clothing types represented
                            in the given list and the number of each 
                            clothing type represented.
    """
    types_count = {}
    for garment in clothes_list:
        if garment.db.clothing_type:
            type = garment.db.clothing_type
            if type not in list(types_count.keys()):
                types_count[type] = 1
            else:
                types_count[type] += 1
    return types_count

def single_type_count(clothes_list, type):
    """
    Returns an integet value of the number of a given type of clothing in a list.

    Args:
        clothes_list (list): List of clothing objects to count from
        type (str): Clothing type to count

    Returns:
        type_count (int): Number of garments of the specified type in the given
                          list of clothing objects.
    """
    type_count = 0
    for garment in clothes_list:
        if garment.db.clothing_type:
            if garment.db.clothing_type == type:
                type_count += 1
    return type_count


class Clothing(Object):
    def at_object_creation(self):
        self.db.category = "clothing"
        
    def wear(self, wearer, wearstyle, quiet=False):
        """
        Sets clothes to 'worn' and optionally echoes to the room.

        Args:
            wearer (obj): character object wearing this clothing object
            wearstyle (True or str): string describing the style of wear or True for none

        Keyword Args:
            quiet (bool): If False, does not message the room.

        Notes:
            Optionally sets db.worn with a 'wearstyle' that appends a short passage to
            the end of the name of the clothing to describe how it's worn that shows
            up in the wearer's desc - I.E. 'around his neck' or 'tied loosely around
            her waist'. If db.worn is set to 'True' then just the name will be shown.
        """
        # Set clothing as worn
        self.db.worn = wearstyle
        # Auto-cover appropriate clothing types, as specified above
        to_cover = []
        if self.db.clothing_type and self.db.clothing_type in CLOTHING_TYPE_AUTOCOVER:
            for garment in get_worn_clothes(wearer):
                if (
                    garment.db.clothing_type
                    and garment.db.clothing_type in CLOTHING_TYPE_AUTOCOVER[self.db.clothing_type]
                ):
                    to_cover.append(garment)
                    garment.db.covered_by = self
        # Return if quiet
        if quiet:
            return
        # Echo a message to the room
        message = "|w{wearer}|n puts on |w{item_name}|n"
        self_message = f"|wYou|n put on |w{self.name}|n"
        if wearstyle is not True:
            message = "|w{wearer}|n wears |w{item_name}|n {wearstyle}"
            self_message = f"|wYou|n wear |w{self.name}|n {wearstyle}"
        wearstyle = ""
        if to_cover:
            message = message + ", covering |w{to_cover}|n"
            self_message = self_message + f", covering |w{list_to_string(to_cover)}|n"
        message = message + "."

        rooms.dark_aware_msg(
            message,
            wearer.location,
            {"{wearer}":wearer.name, "{item_name}":self.name, "{wearstyle}":wearstyle, "{to_cover}": list_to_string(to_cover)},
            {"{wearer}":"Someone", "{item_name}":"something", "{wearstyle}":"", "{to_cover}":"something" },
            wearer
        )
        wearer.msg(self_message)

    def remove(self, wearer, quiet=False):
        """
        Removes worn clothes and optionally echoes to the room.

        Args:
            wearer (obj): character object wearing this clothing object

        Keyword Args:
            quiet (bool): If False, does not message the room
        """
        self.db.worn = False
        remove_message = "|w{wearer}|n removes |w{item_name}|n"
        self_remove_message = f"|wYou|n remove |w{self.name}|n"
        uncovered_list = []

        # Check to see if any other clothes are covered by this object.
        for item in wearer.contents:
            # If anything is covered by
            if item.db.covered_by == self:
                item.db.covered_by =False
                uncovered_list.append(item.name)
        if len(uncovered_list) > 0:
            remove_message = "|w{wearer}|n removes |w{item_name}|n, revealing |w{uncovered_list}|n"
            self_remove_message = f"|wYou|n remove |w{self.name}|n, revealing |w{list_to_string(uncovered_list)}|n"
        # Echo a message to the room.
        if not quiet:
            rooms.dark_aware_msg(
                remove_message,
                wearer.location,
                {"{wearer}":wearer.name, "{item_name}":self.name, "{uncovered_list}":list_to_string(uncovered_list)},
                {"{wearer}":"Someone", "{item_name}":"something", "{uncovered_list}":"something else"},
                wearer
            )
            wearer.msg(self_remove_message)

    def at_get(self, getter):
        """
        Makes absolutely sure clothes aren't arleady set as 'worn'
        when they're picked up, in case they've somehow had their
        location changed without getting removed.
        """
        self.db.worn = False
