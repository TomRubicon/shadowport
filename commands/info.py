"""
Info Commands

Commands that display character information.

"""

from evennia import CmdSet, search_tag
from evennia.utils import evtable
from evennia.contrib import health_bar
from commands.command import Command
from world import mapping

# helpers
def format_stat(stat):
    return f"|Y[|n |m{stat}|n |Y]|n"

def stat_bar(stat, cur_val, max_val, colors=['R', 'Y', 'G', 'G']):
    bar = f"|w{stat}|n  "
    bar += health_bar.display_meter(cur_val, max_val, 30, 
                                    fill_color=colors,
                                    empty_color="X", 
                                    show_values=False)
    bar += f" |Y[|n {cur_val}/{max_val} |Y]|n"
    return bar


class CmdSheet(Command):
    """
    sheet

    Usage:
        sheet
        score
        stats

    Display your character sheet.
    """

    key = "sheet"
    aliases = ["score", "stats", "sc", "sh"]
    help_category = "Info"
    
    def func(self):
        caller = self.caller

        # grab caller's stats 
        stats = caller.attributes.get("stats", {})
        strength = stats.get("strength", 8)
        dexterity = stats.get("dexterity", 8)
        intelligence = stats.get("intelligence", 8)
        toughness = stats.get("toughness", 8)
        perception = stats.get("perception", 8)
        charisma = stats.get("charisma", 8)

        title_table = evtable.EvTable(border="none")
        title_table.add_row("", f"|y{caller.name}'s Character Sheet")
        title_table.reformat_column(0, width=12)
        title_table.reformat_column(1, width=60, align="c")
        caller.msg(title_table)

        caller.msg(" ")

        stat_table = evtable.EvTable(border="none")
        stat_table.add_row("", "|wStrength:|n", f"{format_stat(strength)}", 
                               "|wDexterity:|n", f"{format_stat(dexterity)}", 
                               "|wIntelligence:|n", f"{format_stat(intelligence)}", "")
        stat_table.add_row("", "|wToughness:|n", f"{format_stat(toughness)}",
                               "|wPerception:|n", f"{format_stat(perception)}",
                               "|wCharisma:|n", f"{format_stat(charisma)}", "")
        stat_table.reformat_column(0, width=12)
        caller.msg(stat_table)

        caller.msg(" ")

        trait_table = evtable.EvTable(border="none")
        trait_table.add_row("", "|GPositive Traits|n: Thick Skin, Big Chill, Arcane Attuned")
        trait_table.add_row("", "|RNegative Traits|n: Addict, Poor Eyesight")
        trait_table.reformat_column(0, width=12)
        trait_table.reformat_column(1, align="c", width=60)
        caller.msg(trait_table)

        caller.msg(" ")

        xp_table = evtable.EvTable(border="none")
        xp_table.add_row("", "|wXP:|n |Y[|n |m25,023|n |Y]|n total |W//|n |Y[|n |m12,456|n |Y]|n to spend")
        xp_table.add_row("", "|wSP:|n |Y[|n |m1,455|n |Y]|n total // |Y[|n |m350|n |Y]|n available for training")
        xp_table.reformat_column(0, width=17)
        xp_table.reformat_column(1, align="c")
        caller.msg(xp_table)

        return

class CmdStatus(Command):
    """
    status

    Usage:
        status
        st

    Display your health, hunger, thirst, money and other important information.
    """

    key = "status"
    aliases = ["st"]
    help_category = "Info"

    def func(self):
        caller = self.caller

        vitals = caller.attributes.get("vitals", {})
        health = vitals.get("health", 10)
        health_max = vitals.get("health_max", 10)
        thirst = vitals.get("thirst", 0)
        hunger = vitals.get("hunger", 0)
        sanity = vitals.get("sanity", 1000)
        
        caller.msg(stat_bar("Health", health, health_max))
        caller.msg(stat_bar("Thirst", thirst, 500, colors=["C"]))
        caller.msg(stat_bar("Hunger", hunger, 500, colors=["Y"]))
        caller.msg(stat_bar("Sanity", sanity, 1000, colors=["M"]))

class CmdMap(Command):

    key = "map"

    def func(self):
        caller = self.caller
        location = caller.location
        string = ""
        for line in mapping.draw_mini_map(location, width=8, height=8):
            string += line
        caller.msg(string)


class InfoCmdSet(CmdSet):
    def at_cmdset_creation(self):
        self.add(CmdSheet)
        self.add(CmdStatus)
        self.add(CmdMap)
