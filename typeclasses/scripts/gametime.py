import datetime
import re
from evennia import gametime

# set up the seasons and time slots. This assumes gametime started at the
# beginning of the year (so month 1 is equivalent to January), and that
# one CAN divide the game's year into four seasons in the first place ...
MONTHS_PER_YEAR = 12
SEASONAL_BOUNDARIES = (3 / 12.0, 6 / 12.0, 9 / 12.0)
HOURS_PER_DAY = 24
DAY_BOUNDARIES = (0, 6 / 24.0, 12 / 24.0, 18 / 24.0)

def get_time_and_season():
    """
    Calculate the current time and season ids.
    """
    # get the current time as parts of year and parts of day.
    # we assume a standard calendar here and use 24h format.
    timestamp = gametime.gametime(absolute=True)
    # note that fromtimestamp includes the effects of server time zone!
    datestamp = datetime.datetime.fromtimestamp(timestamp)
    season = float(datestamp.month) / MONTHS_PER_YEAR
    timeslot = float(datestamp.hour) / HOURS_PER_DAY

    # figure out which slots these represent
    if SEASONAL_BOUNDARIES[0] <= season < SEASONAL_BOUNDARIES[1]:
        curr_season = "spring"
    elif SEASONAL_BOUNDARIES[1] <= season < SEASONAL_BOUNDARIES[2]:
        curr_season = "summer"
    elif SEASONAL_BOUNDARIES[2] <= season < 1.0 + SEASONAL_BOUNDARIES[0]:
        curr_season = "autumn"
    else:
        curr_season = "winter"

    if DAY_BOUNDARIES[0] <= timeslot < DAY_BOUNDARIES[1]:
        curr_timeslot = "night"
    elif DAY_BOUNDARIES[1] <= timeslot < DAY_BOUNDARIES[2]:
        curr_timeslot = "morning"
    elif DAY_BOUNDARIES[2] <= timeslot < DAY_BOUNDARIES[3]:
        curr_timeslot = "afternoon"
    else:
        curr_timeslot = "evening"

    return curr_season, curr_timeslot


