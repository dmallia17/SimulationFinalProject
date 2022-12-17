import math, random
from collections import defaultdict

# SCALE NOTES:
# We are focusing around house lots - a street including sidewalks is
# approximately the size of a lot, as is the distance between houses (across
# their backyards). Thus a block is considered 3 lots wide (house, backyards
# house) followed by a street and then another block...

# Lots between avenues (inclusive of backyard of BOTH top and bottom avenue
# shops/restaurants)
#LOTS_BETWEEN_AVENUES = 24

# # Lots between streets (house, backyards, house)
# LOTS_BETWEEN_STREETS = 3

# GRID width controls the number of blocks you'll generate
#GRID_WIDTH = 20

# NOTE FROM MESA DOCS:
# Grid cells are indexed by [x][y], where [0][0] is assumed to be the
# bottom-left and [width-1][height-1] is the top-right. If a grid is toroidal,
# the top and bottom, and left and right, edges wrap to each other

def get_locs(grid_width=20, lots_between=24):
    mapping = defaultdict(list)
    
    # Avenue backyards
    order = ["shop", "restaurant", "restaurant"]
    for x in range(grid_width):
        avenue1_curr = "street" if x % 4 == 0 else random.choice(order) 
        avenue2_curr = "street" if x % 4 == 0 else random.choice(order)
        mapping[avenue1_curr].append((x,0)) # BOTTOM OF GRID
        mapping[avenue2_curr].append((x,lots_between-1)) # TOP OF GRID


    # Residential areas
    orderResidential = ["street", "house", "backyard", "house"]
    for x in range(grid_width):
        entity = orderResidential[x % len(orderResidential)]
        for y in range (1, lots_between-1):
            mapping[entity].append((x,y))

    return mapping

def euclidean_distance(pos1, pos2):
    return math.sqrt(((pos1[0] - pos2[0]) ** 2) + ((pos1[1] - pos2[1]) ** 2))

