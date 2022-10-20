"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
from evennia import DefaultCharacter
from evennia.utils import list_to_string
import typeclasses.rooms as rooms
from typeclasses.clothing import get_worn_clothes


class Character(DefaultCharacter):
    """
    The Character defaults to reimplementing some of base Object's hook methods with the
    following functionality:

    at_basetype_setup - always assigns the DefaultCmdSet to this object type
                    (important!)sets locks so character cannot be picked up
                    and its commands only be called by itself, not anyone else.
                    (to change things, use at_object_creation() instead).
    at_after_move(source_location) - Launches the "look" command after every move.
    at_post_unpuppet(account) -  when Account disconnects from the Character, we
                    store the current location in the pre_logout_location Attribute and
                    move it to a None-location so the "unpuppeted" character
                    object does not need to stay on grid. Echoes "Account has disconnected"
                    to the room.
    at_pre_puppet - Just before Account re-connects, retrieves the character's
                    pre_logout_location Attribute and move it back on the grid.
    at_post_puppet - Echoes "AccountName has entered the game" to the room.

    """
    def announce_move_from(self, destination, msg=None, mapping=None):
        """
        Called if the move is to be announced. This is
        called while we are still standing in the old
        location.

        Args:
            destination (Object): The place we are going to.
            msg (str, optional): a replacement message.
            mapping (dict, optional): additional mapping objects.

        You can override this method and call its parent with a
        message to simply change the default message.  In the string,
        you can use the following as mappings (between braces):
            object: the object which is moving.
            exit: the exit from which the object is moving (if found).
            origin: the location of the object before the move.
            destination: the location of the object after moving.

        """
        if self.location.db.dark: 
            location = self.location
            exits = [
                o for o in location.contents if o.location is location and o.destination is destination
            ]
            exit_name = str(exits[0]) if exits else "somewhere"
            rooms.dark_aware_msg(
                "{character} leaves {exit}.",
                self.location,
                {"{character}":self.name, "{exit}":exit_name},
                {"{character}":"Someone", "{exit}":exit_name},
                self
            )
            return
        super().announce_move_from(destination, msg="{object} leaves {exit}.")

    def announce_move_to(self, source_location, msg=None, mapping=None):
        """
        Called after the move if the move was not quiet. At this point
        we are standing in the new location.

        Args:
            source_location (Object): The place we came from
            msg (str, optional): the replacement message if location.
            mapping (dict, optional): additional mapping objects.

        You can override this method and call its parent with a
        message to simply change the default message.  In the string,
        you can use the following as mappings (between braces):
            object: the object which is moving.
            exit: the exit from which the object is moving (if found).
            origin: the location of the object before the move.
            destination: the location of the object after moving.

        """
        origin = source_location
        destination = self.location
        exits = []
        if origin:
            exits = [
                o
                for o in destination.contents
                if o.location is destination and o.destination is origin
            ]
        the_exit = exits[0]
        exit_msg_obj = "{object}"
        exit_msg = "%s arrives from the {exit}." % (exit_msg_obj)
        exit_dict = {"up":"above", "down":"below", "in":"inside", "out":"outside"}
        if str(the_exit) in exit_dict:
            exit_msg = "%s arrives from %s." % (exit_msg_obj, exit_dict[str(the_exit)])
        if destination.db.dark:
            rooms.dark_aware_msg(
                exit_msg,
                self.location,
                {"{object}":self.name, "{exit}":str(the_exit)},
                {"{object}":"Someone", "{exit}":str(the_exit)},
                self
            )
            return

        super().announce_move_to(source_location, msg=exit_msg)

    def return_appearance(self, looker):
        """
        This formats a description. It is the hook a 'look' command
        should call.

        Args:
            looker (Object): Object doing the looking

        Notes:
            The name of every clothing item carried and worn by the character
            is appended to their description. If the clothing's db.worn value
            is set to True, only the name is appended, but if the value is a
            string, the string is appended to the end of the name, to allow
            characters to specify how clothing is worn.
        """
        if not looker:
            return ""
        # get description, build string
        string = "|y%s|n\n" % self.get_display_name(looker)
        desc = self.db.desc
        worn_string_list = []
        clothes_list = get_worn_clothes(self, exclude_covered=True)
        # Append worn, uncovered clothing to the description
        for garment in clothes_list:
            # If 'worn' is True, just append the name
            if garment.db.worn is True:
                worn_string_list.append(garment.name)
            # Otherwise, append the name and the string value of 'worn'
            elif garment.db.worn:
                worn_string_list.append("%s %s" % (garment.name, garment.db.worn))
        if desc:
            string += "%s" % desc
        # Append worn clothes.
        if worn_string_list:
            string += "|/|/%s is wearing %s." % (self, list_to_string(worn_string_list))
        else:
            string += "|/|/%s is not wearing anything." % self
        return string

    def at_say(self, message, msg_self=None, msg_location=None, receivers=None, msg_receivers=None, **kwargs):
        if self.location.db.dark:
            message_location = '{character} says, "%s"' % (message)
            rooms.dark_aware_msg(
                message_location,
                self.location,
                {"{character}":self.name},
                {"{character}":"Someone"},
                self
            )
            self.msg(f'You say, "{message}"')
            return
        
        super().at_say(message, msg_self, msg_location, receivers, msg_receivers, **kwargs)
