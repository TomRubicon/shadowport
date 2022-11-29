"""
Mapping

This mmodule contains methods and classes that handle
displaying the in-game map.

"""
from evennia import search_tag

DEFAULT_SYMBOL = "|[Y[]|n"
DEFAULT_EMPTY_SYMBOL = "|b||_|n"
DEFAULT_PLAYER_SYMBOL = "|[c|R()|n"

def draw_mini_map(location, width=3, height=3):
    # coords = (location.attributes.get("x", 0), location.attributes.get("y", 0))
    coords = (location.db.x, location.db.y)
    zone_tag = location.tags.get(category="zone")
    rooms = search_tag(zone_tag, category="zone")
    map_dict = {}
    string = ""
    string_list = []

    # map room attributes to dictionary
    for room in rooms:
        # only take room data from the same floor as the player
        if room.db.z != location.db.z:
            continue

        room_x = room.attributes.get("x")
        room_y = room.attributes.get("y")
        room_symbol = room.attributes.get("symbol", DEFAULT_SYMBOL)

        map_dict[(room_x, room_y)] = {"name":room.name,
                                      "symbol":room_symbol}
    
    for y in reversed(range(coords[1] - (height - 1), coords[1] + height)):
        for x in range(coords[0] - (width -1), coords[0] + width):
            # if this is where the player is located, draw the player symbol
            if (x, y) == coords:
                string += DEFAULT_PLAYER_SYMBOL
                continue
            # fill the string with the default symbol if the coords dont exist
            # in the current zone
            if (x, y) not in map_dict.keys():
                string += DEFAULT_EMPTY_SYMBOL
                continue
            string += map_dict[(x, y)]["symbol"]

        string += "\n"
        string_list.append(string)

    return string
