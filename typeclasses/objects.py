"""
Object

The Object is the "naked" base class for things in the game world.

Note that the default Character, Room and Exit does not inherit from
this Object, but from their respective default implementations in the
evennia library. If you want to use this class as a parent to change
the other types, you can do so by adding this as a multiple
inheritance.

"""
from evennia import DefaultObject


class Object(DefaultObject):
    def get_mass(self):
        mass = self.attributes.get("mass", 1)
        return mass + sum(obj.get_mass() for obj in self.contents)

class Container(Object):
    def at_object_creation(self):
        self.db.container = True
        self.db.capacity = 100
        self.db.mass_reduction = 0.90
    
    def return_appearance(self, looker, **kwargs):
        description = self.db.desc
        items = self.contents
        description += f"\n\n|wItems inside:|n\n{items}"
        return description
