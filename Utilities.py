import math, random
from collections import defaultdict
import mesa

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


def get_mesa_visualization_element(json_dict, element):
    mesa_type_map = {
        "Slider" : mesa.visualization.Slider,
        "Checkbox" : mesa.visualization.Checkbox
    }
    element_details = json_dict[element]
    constructor = mesa_type_map[element_details["type"]]
    return constructor(**{k : v for (k,v) in element_details.items() if k != "type"})

def populate_parser(parser, json_dict):
    for k in json_dict:
        curr_p = json_dict[k]
        default_val = curr_p["value"]
        help_str = curr_p["name"]
        if curr_p["type"] == "Slider":
            parser.add_argument("--" + k, type=type(default_val),
            default=default_val, help=help_str)
        elif curr_p["type"] == "Checkbox":
            if not default_val: # Defaults to false
                parser.add_argument("--" + k, action="store_true",
                help=help_str)
            else: # Defaults to true
                parser.add_argument("--no_" + k, action="store_false",
                    help=help_str)

# TODO: May need to add an optional ignore list if permitting parameter sweeps
def check_args(args_dict, json_dict):
    for k,v in args_dict.items():
        dict_entry = json_dict[k]
        if dict_entry["type"] == "Slider":
            min_anticipated = dict_entry["min_value"]
            max_anticipated = dict_entry["max_value"]
            step = dict_entry["step"]
            if v < min_anticipated:
                print("\x1b[41m" + k + " has a value LESS than expected" +
                    "\x1b[0m\n")
            if v > max_anticipated:
                print("\x1b[41m" + k + " has a value GREATER than expected" +
                    "\x1b[0m\n")
            if v % step != 0:
                print("\x1b[41m" + k +
                    " has a value that cannot be reached with step" +
                    "\x1b[0m\n")
