"""
Queue Commands

Commands that have an effect on the command queue.

"""

import evennia
from evennia.commands.command import Command as BaseCommand
from evennia import CmdSet

class CommandQueue:
    def __init__(self):
        self.queue = []

    def append(self, command):
        self.queue.append(command) 

    def call_next(self):
        if self.queue:
            command = self.queue[0]
            self.queue.pop(0)
            return command
        return ""

class CmdStop(BaseCommand):
    """
    stop action

    Usage:
      stop
    
    Stops the current action, if any. (Currently it only stops movement)
    """

    key = "stop"
    help_category = "movement"

    def func(self):
        """
        This is a very simple command, using the
        stored deferred from the exit traversal found
        in typeclasses/exits.py Exit class.
        """
        currently_moving = self.caller.ndb.currently_moving
        if currently_moving and not currently_moving.called:
            currently_moving.cancel()
            self.caller.msg("You stop moving.")
            for observer in self.caller.location.contents_get(self.caller):
                observer.msg("%s stops." % self.caller.get_display_name(observer))
        else:
            self.caller.msg("You are not moving!")

class QueueCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdStop)
