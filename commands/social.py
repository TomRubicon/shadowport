"""
Social Commands

Commands relating to socializing.

"""

import evennia
from evennia.commands.command import Command as BaseCommand
from evennia import CmdSet
from evennia.utils import search
import typeclasses.rooms as rm
from typeclasses.scripts.utils import get_direction

class CmdYell(BaseCommand):
    """
    yell

    Usage:
      yell <msg>

    Yell a message to everyone in the same zone.
    """
    
    key = "yell"
    aliases = ["shout"]
    help_category = "Social"
    
    def func(self):
        caller = self.caller
        this_room = caller.location
        coords = (this_room.db.x, this_room.db.y, this_room.db.z)
        tag = this_room.tags.get(category="zone")
        rooms = evennia.search_tag(tag, category="zone")
        msg = self.args.lstrip()
        caller.msg(f'You yell, "{msg}".')
        for room in rooms:
            if room == this_room:
                room.msg_contents(f'{caller} yells, "{msg}".', exclude=self.caller)
                rm.dark_aware_msg(
                    '{caller} yells, "{msg}".',
                    this_room,
                    {"{caller}":caller.name, "{msg}":msg},
                    {"{caller}":"Someone", "{msg}":msg},
                    caller
                )
            else:
                room_coords = (room.db.x, room.db.y, room.db.z)
                dir = get_direction(coords, room_coords)
                room.msg_contents(f'From the {dir} you hear someone yell, "{msg}".', exclude=self.caller)

class SocialCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdYell)
