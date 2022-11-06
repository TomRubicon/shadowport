"""
Object

The Object is the "naked" base class for things in the game world.

Note that the default Character, Room and Exit does not inherit from
this Object, but from their respective default implementations in the
evennia library. If you want to use this class as a parent to change
the other types, you can do so by adding this as a multiple
inheritance.

"""

import itertools
from evennia import DefaultObject, utils
import commands.inventory as inv_utils
import typeclasses.rooms as rooms
from world import rules

class Object(DefaultObject):
    def get_mass(self, modifier=1.0):
        mass = self.attributes.get("mass", 1)
        return mass + (sum(obj.get_mass() for obj in self.contents) * modifier)

    def get_mass_modified(self, modifier=1.0):
        mass = self.attributes.get("mass", 1)
        return mass * modifier

class Container(Object):
    def at_object_creation(self):
        self.db.container = True
        self.db.capacity = 100
        self.db.mass_reduction = 0.90
        self.db.category = "container"

    def return_appearance(self, looker, **kwargs):
        description = f"|y{self.get_display_name(looker).capitalize()}|n\n"
        description += self.db.desc
        description += f"\n|YEmpty Weight:|n {self.db.mass}"
        items = inv_utils.display_contents(self, "It is empty.", "Contents", for_container=True)
        description += f"\n\n{items}"
        return description

    def get_mass(self, modifier=1.0):
        return super().get_mass(self.db.mass_reduction)
    
    def get_contents_mass(self):
        return sum(obj.get_mass_modified(self.db.mass_reduction) for obj in self.contents)

class Consumable(Object):
    def at_object_creation(self):
        self.db.category = "consumable"
        self.db.uses = 1
        self.db.effects = {}
        self.db.consume_msg = "|w{character}|n consumes a use of |w{item}|n."
        self.db.consume_msg_self = "|wYou|n consume a use of |w"
        self.db.use_on_msg = "|w{character}|n uses |w{item}|n on |w{target}|n."
        self.db.use_on_msg_self = ["|wYou|n use |w{item}|n", " on |w"]
        self.db.consume_type = "use"
        self.db.usable_on_target = False

    def consume(self, user, target=None):
        self.db.uses -= 1 
        name = self.name
        if not target:
            user.msg(f"{self.db.consume_msg_self}{name}|n.")
            rooms.dark_aware_msg(
                self.db.consume_msg,
                user.location,
                {"{character}":user.name, "{item}":self.name},
                {"{character}":"Someone", "{item}":"something"},
                user
            )
            rules.apply_effects(self.db.effects, user)
        else:
            if not self.db.usable_on_target:
                user.msg(f"You can't use {self.name} on someone/something else.")
                return
            user.msg(f"{self.db.use_on_msg_self[0]}{name} {self.db.use_on_msg_self[1]}{target}|n.")
            rooms.dark_aware_msg(
                self.db.use_on_msg,
                user.location,
                {"{character}":user.name, "{target}":target.name, "{item}":self.name},
                {"{character}":"Someone", "{target}":"someone", "{item}":"something"},
                user
            )
            rules.apply_effects(self.db.effects, target)

        if self.db.uses <= 0:
            user.msg(f"The {self.name} has been used up.")
            self.delete()
