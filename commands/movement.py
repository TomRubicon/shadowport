"""
Movement Commands

Commands relating to traversing the world.

"""

import evennia
from evennia.commands.command import Command as BaseCommand
from evennia import CmdSet
from evennia.utils import search

class BaseMovementCmd(BaseCommand):
    def func(self):
        self.caller.msg("You can't go that way.")

class CmdNorth(BaseMovementCmd):
    """
    north

    Usage:
      north
    """

    key = "north"
    aliases = "n"
    help_category = "movement"

class CmdNorthEast(BaseMovementCmd):
    """
    northeast

    Usage:
      northeast
    """

    key = "northeast"
    aliases = "ne"
    help_category = "movement"

class CmdNorthWest(BaseMovementCmd):
    """
    northwest

    Usage:
      northwest
    """

    key = "northwest"
    aliases = "nw"
    help_category = "movement"

class CmdSouth(BaseMovementCmd):
    """
    south

    Usage:
      south
    """

    key = "south"
    aliases = "s"
    help_category = "movement"

class CmdSouthEast(BaseMovementCmd):
    """
    southeast

    Usage:
      southeast
    """

    key = "southeast"
    aliases = "se"
    help_category = "movement"

class CmdSouthWest(BaseMovementCmd):
    """
    southwest

    Usage:
      southwest
    """

    key = "southwest"
    aliases = "sw"
    help_category = "movement"

class CmdEast(BaseMovementCmd):
    """
    east

    Usage:
      east
    """

    key = "east"
    aliases = "e"
    help_category = "movement"

class CmdWest(BaseMovementCmd):
    """
    west

    Usage:
      west
    """

    key = "west"
    aliases = "w"
    help_category = "movement"

class CmdUp(BaseMovementCmd):
    """
    up

    Usage:
      up
    """

    key = "up"
    aliases = "u"
    help_category = "movement"

class CmdDown(BaseMovementCmd):
    """
    down

    Usage:
      down
    """

    key = "down"
    aliases = "d"
    help_category = "movement"

class MovementCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdNorth)
        self.add(CmdNorthEast)
        self.add(CmdNorthWest)
        self.add(CmdSouth)
        self.add(CmdSouthEast)
        self.add(CmdSouthWest)
        self.add(CmdEast)
        self.add(CmdWest)
        self.add(CmdUp)
        self.add(CmdDown)
