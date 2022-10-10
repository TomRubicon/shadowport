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
from commands.inventory import display_contents

class Object(DefaultObject):
    def get_mass(self, modifier=1.0):
        mass = self.attributes.get("mass", 1)
        return mass + (sum(obj.get_mass() for obj in self.contents) * modifier)

class Container(Object):
    def at_object_creation(self):
        self.db.container = True
        self.db.capacity = 100
        self.db.mass_reduction = 0.90
    
    def return_appearance(self, looker, **kwargs):
        description = f"|y{self.get_display_name(looker).capitalize()}|n\n"
        description += self.db.desc
        items = display_contents(self, "It is empty.", "Contents")
        description += f"\n\n{items}"
        return description

    def get_mass(self, modifier=1.0):
        return super().get_mass(self.db.mass_reduction)
