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

class CmdPose(BaseCommand):
    """
    strike a pose

    Usage:
      pose <pose text>
      pose's <pose text>

    Example:
      pose is standing by the wall, smiling.
       -> others will see:
      Tom is standing by the wall, smiling.

    Describe an action being taken. The pose text will
    automatically begin with your name.
    """

    key = "pose"
    aliases = [":", "emote"]
    locks = "cmd:all()"

    def parse(self):
        """
        Custom parse the cases where the emote
        starts with some special letter, such
        as 's, at which we don't want to separate
        the caller's name and the emote with a
        space.
        """
        args = self.args
        if args and not args[0] in ["'", ",", ":"]:
            args = " %s" % args.strip()
        self.args = args

    def func(self):
        """Hook function"""
        if not self.args:
            msg = "What do you want to do?"
            self.caller.msg(msg)
        else:
            msg = self.args
            rm.dark_aware_msg(
                '{caller}{msg}',
                self.caller.location,
                {"{caller}":self.caller.name, "{msg}":msg},
                {"{caller}":"Someone", "{msg}":msg}
            )



class SocialCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdYell)
        self.add(CmdPose)
