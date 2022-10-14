"""
Utility functions and classes

Little helper tools that may oneday be split into different files.

"""

import math

def get_distance(p1, p2):
    return int(math.dist(p1, p2))

def get_direction(p1, p2):
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    angle = math.degrees(math.atan2(dy, dx))
    angle360 = angle % 360
    dir = "none"

    if angle > 65 and angle < 120:
        dir = 'north'
    elif angle > -110 and angle < -70:
        dir = 'south'
    elif angle < 25 and angle > -25:
        dir = 'east'
    elif angle360 > 160 and angle360 < 205:
        dir = 'west'
    elif angle > 25 and angle < 65:
        dir = 'northeast'
    elif angle360 > 205 and angle360 < 245:
        dir = 'southwest'
    elif angle > 110 and angle < 155:
        dir = 'northwest'
    elif angle360 > 295 and angle360 < 335:
        dir = 'southeast'

    return dir
