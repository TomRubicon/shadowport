"""
Gamemaster Commands

Commands relating to game mastering.

"""

from evennia.commands.command import Command as BaseCommand
from evennia import CmdSet

class CmdSound(BaseCommand):
    """
    sound

    Usage:
      sound <volume> = <sound/msg>

    Send a sound to the current zone you are in.
    """

    pass

class GMCmdSet(CmdSet):
    pass
