"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""
from evennia import DefaultExit, utils, Command
from evennia.contrib.slow_exit import SlowExit
from commands.queue import CommandQueue
from commands.movement import handle_movement_queue
import typeclasses.rooms as rooms

class Exit(DefaultExit):
    """
    Exits are connectors between rooms. Exits are normal Objects except
    they defines the `destination` property. It also does work in the
    following methods:

     basetype_setup() - sets default exit locks (to change, use `at_object_creation` instead).
     at_cmdset_get(**kwargs) - this is called when the cmdset is accessed and should
                              rebuild the Exit cmdset along with a command matching the name
                              of the Exit object. Conventionally, a kwarg `force_init`
                              should force a rebuild of the cmdset, this is triggered
                              by the `@alias` command when aliases are changed.
     at_failed_traverse() - gives a default error message ("You cannot
                            go there") if exit traversal fails and an
                            attribute `err_traverse` is not defined.

    Relevant hooks to overload (compared to other types of Objects):
        at_traverse(traveller, target_loc) - called to do the actual traversal and calling of the other hooks.
                                            If overloading this, consider using super() to use the default
                                            movement implementation (and hook-calling).
        at_after_traverse(traveller, source_loc) - called by at_traverse just after traversing.
        at_failed_traverse(traveller) - called by at_traverse if traversal failed for some reason. Will
                                        not be called if the attribute `err_traverse` is
                                        defined, in which case that will simply be echoed.
    """
    def at_traverse(self, traversing_object, target_location):
        """
        Implements the actual traversal, using utils.delay to delay the move_to.
        """

        # if the traverser has an Attribute move_speed, use that,
        # otherwise default to "walk" speed
        move_speed = traversing_object.db.move_speed or 4

        def move_callback():
            "This callback will be called by utils.delay after move_delay seconds."
            source_location = traversing_object.location
            command_queue = traversing_object.ndb.command_queue

            if traversing_object.move_to(target_location):
                self.at_after_traverse(traversing_object, source_location)
                if command_queue:
                    traversing_object.execute_cmd(command_queue.call_next())
            else:
                if self.db.err_traverse:
                    # if exit has a better error message, let's use it.
                    self.caller.msg(self.db.err_traverse)
                else:
                    # No shorthand error message. Call hook.
                    self.at_failed_traverse(traversing_object)

        # check if traversing object is already moving. If it is, call the queue version of the exit command
        if traversing_object.ndb.currently_moving and not traversing_object.ndb.currently_moving.called:
            handle_movement_queue(traversing_object, self.key)
            return

        traversing_object.msg("You start moving %s. It will take %s seconds." % (self.key, move_speed))
        rooms.dark_aware_msg(
            "|w{traversing_object}|n starts moving |w{exit}|n |W(it will take {move_speed} seconds)|n",
            self.location,
            {"{traversing_object}":traversing_object.name, "{exit}":self.key, "{move_speed}":str(move_speed)},
            {"{traversing_object}":"Someone", "{exit}":self.key, "{move_speed}":str(move_speed)},
            traversing_object
        )
        # create a delayed movement
        t = utils.delay(move_speed, move_callback)
        # we store the deferred on the character, this will allow us
        # to abort the movement. We must use an ndb here since
        # deferreds cannot be pickled.
        traversing_object.ndb.currently_moving = t

    def return_appearance(self, looker, **kwargs):
        return self.destination.return_appearance(looker, **kwargs)

