"""
Rules

This module contains methods and classes that handle the games
rule system.

"""

def apply_effects(effects, character):
    """
    Takes an input dict and runs through it, apply effects on a chracter

    Args:
        effects (dict): 
        character (obj):
    """
    for effect, value in effects.items():
        if character.attributes.has(effect):
            stat = character.attributes.get(effect, return_obj=True)
            if stat == type(bool):
                stat = value
                continue
            stat += value
            continue
        getattr(character, effect)(*value)
        
        
