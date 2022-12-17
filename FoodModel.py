import time
import mesa
import numpy as np
import pandas as pd
from Utilities import get_locs, euclidean_distance

# MESA GRID CONVENTION
#   |
# y |       o
#   |
#       -   -   -
#           x
#

#pos[x][y] = o

GRID_PIXEL_WIDTH = 1000
GRID_PIXEL_HEIGHT = 1000
GRID_WIDTH = 20
GRID_HEIGHT = 24
MINUTES_PER_TICK = 15
# Ticks per average mouse arrival
MAX_MOUSE_GROWTH_RATE = (48 * 60) / MINUTES_PER_TICK
MATING_PROBABILITY = .8
# Assumes all births in 60 days
TICKS_UNTIL_BIRTH = (60 * 24 * 60) / MINUTES_PER_TICK
TICKS_UNTIL_MATURE = (45 * 24 * 60 ) / MINUTES_PER_TICK
KITTEN_LITTER_MIN = 2
KITTEN_LITTER_MAX = 6
# Threshold for when the cat decides to head back to known food sources (we
# assume this is around 6 hours). Must be negative as this is the time elapsed
# since they became hungry.
FOOD_THRESHOLD = -1 * (360 / MINUTES_PER_TICK)


class StreetAgent(mesa.Agent):
    pass

class BackyardAgent(mesa.Agent):
    pass

class ShopAgent(mesa.Agent):
    pass

class RestaurantAgent(mesa.Agent):
    def __init__(self, unique_id, model, initial_mice_pop, mouse_growth_rate):
        super().__init__(unique_id, model)
        self.mice_pop = 1 + np.random.poisson(initial_mice_pop)
        self.mouse_growth_rate = np.random.poisson(
            (mouse_growth_rate * 60) / MINUTES_PER_TICK)
        self.ticks_until_new_mouse = np.random.poisson(self.mouse_growth_rate)
        self.mice_caught = 0

        # Probability of Interaction
        self.mouse_prob = self.mice_pop / 100

    def step(self):
        self.ticks_until_new_mouse -= 1
        if self.ticks_until_new_mouse <= 0:
            self.mice_pop += 1
            self.mouse_growth_rate = max(self.mouse_growth_rate - 1,
                MAX_MOUSE_GROWTH_RATE)
            self.mouse_prob = min(1, self.mice_pop / 100)
            self.ticks_until_new_mouse = np.random.poisson(
                self.mouse_growth_rate)

class CatAgent(mesa.Agent):
    # @param hunger_rate Rate in hours until hungry
    def __init__(self, unique_id, model, hunger_rate, sleep_rate,
        sleep_duration_rate, sex):
        super().__init__(unique_id, model)
        self.sex = sex # Assume True=male,False=female
        self.aggressiveness = 0 if not self.sex else self.random.uniform(0,1)
        self.pregnant = False # Default all cats to not pregnant
        self.ticks_until_birth = None
        self.chosen_mate = None

        # FOOD
        # Personal hunger rate (i.e. how often they become hungry)
        self.hunger_rate = np.random.poisson((hunger_rate * 60) / MINUTES_PER_TICK)
        # Are they hungry now
        self.is_hungry = self.random.choices(
            [True, False], weights=[0.2,0.8])[0]
        # Time until hungry (randomly generated, sampled with mean
        # corresponding to their own personal hunger rate)
        self.ticks_until_hungry = 0 if self.is_hungry else \
            np.random.poisson(self.hunger_rate)
        self.found_food = None # Food zone (e.g. House)
        self.found_food_type = None # Food zone type (e.g. HouseAgent)
        self.last_food_loc = None
        self.go_wander = False

        # SLEEP
        # NOTE: Can revisit and add some tolerance for still searching for food
        #       even if sleepy...
        # Personal sleepy rate (i.e. how often they become sleepy)
        self.sleepy_rate = 1 + np.random.poisson((sleep_rate * 60) / MINUTES_PER_TICK)
        # Average time asleep (for all cats, not personalized)
        self.sleep_duration_rate = ((sleep_duration_rate * 60) / MINUTES_PER_TICK)


        print("SLEEPY RATE:", self.sleepy_rate)
        print("SLEEP DURATION RATE:", self.sleep_duration_rate)

        # Are they asleep right now
        self.is_asleep = self.random.choices(
            [True, False], weights=[0.2,0.8])[0]
        # Are they sleepy now
        self.is_sleepy = False if self.is_asleep else self.random.choices(
            [True, False], weights=[0.2,0.8])[0]
        # Time until sleepy (randomly generated, sampled with mean
        # corresponding to their own personal sleepy rate)
        self.ticks_until_sleepy = 0 if (self.is_sleepy or self.is_asleep) else np.random.poisson(self.sleepy_rate)
        # Time until they wake up
        self.ticks_until_awake = 0 if not self.is_asleep else np.random.poisson(self.sleep_duration_rate)

        self.hunt_ability = self.random.uniform(0.5,1)

    def cat_encounter(self, other):
        pass

    # Looking for food...
    # - Houses              [X]
    # - Birds               [ ]
    # - Mice                [X]
    def find_food(self):
        new_loc = None
        # Do a search of radius 1 for houses with food
        for neighbor in self.model.grid.iter_neighbors(self.pos, True, True):
            if (isinstance(neighbor, HouseAgent) and neighbor.food) or \
                (isinstance(neighbor, RestaurantAgent) and \
                    neighbor.mice_pop > 0 and not self.go_wander):
                new_loc = neighbor.pos
                self.found_food = neighbor
                self.found_food_type = type(neighbor)
                break

        if new_loc is None and self.last_food_loc is not None and \
            self.ticks_until_hungry < FOOD_THRESHOLD and not self.go_wander:
            new_loc = min([(loc, euclidean_distance(self.pos, loc)) \
                for loc in self.model.grid.get_neighborhood(self.pos, True)],
                key=lambda x : x[1])[0]

        if self.ticks_until_hungry < -96:
            self.go_wander = True

        # Currently just random search if no food
        # Can update to...
        # - go to last location with food
        # - "instinctively" go to streets/backyards/restaurants (or just head
        #   to avenue)
        if new_loc is None:
            new_loc = self.random.choice(
                self.model.grid.get_neighborhood(self.pos, 
                                                    moore=True, 
                                                    include_center=False))

        # new_loc should never be None
        return new_loc

    # STATE TO UPDATE (currently):
    # - Hunger                      [X]
    # - Need to sleep               [X]
    # - Pregnant (if female)        [X]
    # - Injured                     [ ]
    # - Starved                     [ ]
    # Mostly captures change due to time
    def update_state(self):
        if self.is_asleep: # The cat is asleep
            self.ticks_until_awake -= 1 # Decrement time until awakened
            if self.ticks_until_awake <= 0: # If wake up time
                self.is_asleep = False # No longer asleep
                self.is_sleepy = False # Not sleepy
                # Generate time until sleepy
                self.ticks_until_sleepy = np.random.poisson(self.sleepy_rate)
        else: # The cat is awake
            self.ticks_until_sleepy -= 1 # Decrement time until sleepy
            if self.ticks_until_sleepy <= 0: # If sleep time
                self.is_sleepy = True # Now sleepy
                self.is_asleep = True # Now asleep (assuming sleepy = go to sleep)
                # Generate how long until they are awakened
                self.ticks_until_awake = np.random.poisson(self.sleep_duration_rate)


        # UPDATE THESE IF FOUND_FOOD SHOULD LIVE BEYOND 1 TICK
        self.found_food = None
        self.found_food_type = None
        self.ticks_until_hungry -= 1
        if self.ticks_until_hungry <= 0:
            self.is_hungry = True

        # SAME IDEA FOR REPRODUCTION
        self.chosen_mate = None
        if self.ticks_until_birth is not None:
            self.ticks_until_birth -= 1
            # QUEUE UP KITTENS
            if self.ticks_until_birth <= 0:
                future_time = self.model.current_tick + TICKS_UNTIL_MATURE
                num_kittens = self.random.choice(list(range(KITTEN_LITTER_MIN, 
                            KITTEN_LITTER_MAX + 1)))
                if future_time in self.model.kitten_queue:
                    self.model.kitten_queue[future_time] += num_kittens
                else: 
                    self.model.kitten_queue[future_time] = num_kittens
                self.ticks_until_birth = None
                self.pregnant = False
                #print("GAVE BIRTH")

    # Handles movement under...
    # CAT PRIORITIES
    # Hunger                        [X]
    # Reproduce                     [X]
    # Sleep                         [X] (move does not get called)
    # Wander                        [X]
    def move(self):
        if self.is_hungry:
            new_loc = self.find_food()

            self.model.grid.move_agent(self, new_loc)
        elif (not self.pregnant) and (possible_mates := \
            [a for a in self.model.grid.iter_neighbors(self.pos, True, True) \
            if isinstance(a, CatAgent) and a.sex != self.sex and \
                not a.pregnant and not a.is_asleep]):
            self.chosen_mate = self.random.choice(possible_mates)
            self.model.grid.move_agent(self, self.chosen_mate.pos)
        # CHANGE
        else: # Wander
            self.model.grid.move_agent(self,
                self.random.choice(self.model.grid.get_neighborhood(
                                   self.pos, 
                                   moore=True, 
                                   include_center=False)))

    def no_cat_in_cell(self, cell):
        print(cell)
        return (len(
            [agent for agent in cell if isinstance(agent, CatAgent)]) == 0)

    # A CAT MAY
    # - Eat house food              [X]
    # - Eat mice                    [X]
    # - Eat bird                    [ ]
    # - Fight                       [X]
    # - Reproduce                   [X]
    # - Killed by fight             [ ]
    # - Killed by car               [ ]
    def act(self):
        other_agents = [a for a in \
            self.model.grid.grid[self.pos[0]][self.pos[1]] if a is not self]
        # On street
        if [a for a in other_agents if isinstance(a, StreetAgent)]:
            # Gets hit by car?
            if (self.random.uniform(0,1) < self.model.car_hit_prob):
                self.model.grid.remove_agent(self)
                self.model.schedule.remove(self)
                self.model.cat_list.remove(self)
                self.model.num_cats -=1
                self.model.num_cats_hit_by_car += 1
                return

        # Encountered other cat?
        active_cats_in_cell = [a for a in other_agents if \
            isinstance(a, CatAgent) and not a.is_asleep]
        male_cats = [cat for cat in active_cats_in_cell if cat.sex]
        female_cats = [cat for cat in active_cats_in_cell if not cat.sex]
        if self.sex and male_cats: # If male and encountering other males
            # Encounter?
            encounter_prob = 1 - (1 / (1 + len(male_cats)))
            if (self.random.uniform(0, 1) < encounter_prob):
                print(encounter_prob)
                # Which cat
                other_male = self.random.choice(male_cats)
                # Violent?
                violent_prob = (self.aggressiveness + \
                    other_male.aggressiveness + int((len(female_cats) > 0))) / 3
                if self.random.uniform(0, 1) < violent_prob*.3:
                    print(violent_prob)
                    print("CAT FIGHT AT", self.pos)
                    self.model.cat_fights += 1
                    # BOTH CATS RUN TO RANDOM LOCATION
                    run_locations = []
                    radius_to_run = 3
                    while len(run_locations) < 2:
                        run_locations = [loc for loc in \
                            self.model.grid.get_neighborhood(
                                self.pos, True, False, radius_to_run) \
                            if self.no_cat_in_cell(
                                self.model.grid.grid[loc[0]][loc[1]])]
                        radius_to_run += 1
                        print(run_locations)
                    run_locs = self.random.choices(run_locations, k=2)
                    self.model.grid.move_agent(self, run_locs[0])
                    self.model.grid.move_agent(other_male, run_locs[1])
                    return

        # Came here to reproduce?
        if self.chosen_mate is not None:
            print("Moved to mate")
            # Probabilistic mating
            u = self.random.uniform(0, 1)
            if (u < MATING_PROBABILITY):
                if self.sex:
                    self.chosen_mate.pregnant = True
                    self.chosen_mate.ticks_until_birth = TICKS_UNTIL_BIRTH
                else:
                    self.pregnant = True
                    self.ticks_until_birth = TICKS_UNTIL_BIRTH

        # Came here to eat? 
        if self.found_food:
            food_success = False
            #self.last_food_loc = self.found_food.pos
            if self.found_food_type is HouseAgent:
                self.is_hungry = False
                self.found_food.food = False
                food_success = True
                self.last_food_loc = self.found_food.pos
                self.go_wander = False
            elif self.found_food_type is RestaurantAgent:
                u = self.random.uniform(0,1)
                if (u < self.hunt_ability * self.found_food.mouse_prob):
                    food_success = True
                    self.is_hungry = False
                    self.found_food.mice_pop -= 1
                    self.found_food.mice_caught += 1
                    self.found_food.mouse_growth_rate += 1
                    self.last_food_loc = self.found_food.pos
                    self.go_wander = False
            self.ticks_until_hungry = np.random.poisson(self.hunger_rate) \
                if food_success else self.ticks_until_hungry
            #print("I ATE FOOD")

        # Wandering?

    def step(self):
        # print("Is asleep:", self.is_asleep)
        # print("Is sleepy:", self.is_sleepy)
        # print("Ticks until sleepy:", self.ticks_until_sleepy)
        # print("Ticks until awake:", self.ticks_until_awake)

        #print("Cat: ", self.unique_id, " is hungry ", self.is_hungry, " at ",
        # self.pos)
        self.update_state()
        if not self.is_asleep:
            self.move()
            self.act()


class HouseAgent(mesa.Agent):
    def __init__(self, unique_id, model, willingness, rate):
        super().__init__(unique_id, model)
        self.puts_food = self.random.choices([True, False],
            weights=[willingness,1-willingness])[0]
        self.food = False

        #print(self.puts_food)
        if self.puts_food:
            self.food = True
            self.rate = 1 + np.random.poisson(rate)
            self.food_p = 1 / ((self.rate * 60) / MINUTES_PER_TICK)
            self.food_p_n = 1 - self.food_p

    def step(self):
        #print("House: ", self.unique_id, " has food out ", self.food, " at ",
        # self.pos)
        if self.puts_food and not self.food:
            self.food = self.random.choices([True, False],
                weights=[self.food_p,self.food_p_n])[0]

def get_hunger(model):
    return 0 if not model.num_cats else \
        (len([1 for cat in model.cat_list if cat.is_hungry]) / model.num_cats)

def get_mice_pop(model):
    restaurants = model.restaurant_list
    return sum([res.mice_pop for res in restaurants])

def get_cat_pop(model):
    return model.num_cats

def get_cats_hit_by_car(model):
    return model.num_cats_hit_by_car

def get_cats_removed_under_policy(model):
    return model.num_cats_removed_under_policy

def max_hunger(model):
    print(min(model.cat_list, key= lambda cat:cat.ticks_until_hungry).pos)
    return min([cat.ticks_until_hungry for cat in model.cat_list])

def get_cat_pregnancies(model):
    return len([cat for cat in model.cat_list if cat.pregnant])

def get_cat_fights(model):
    return model.cat_fights

class_map = {
    "street" : StreetAgent,
    "house" : HouseAgent,
    "backyard" : BackyardAgent,
    "shop" : ShopAgent,
    "restaurant" : RestaurantAgent
}

class FoodModel(mesa.Model):
    def __init__(self, num_cats, hunger_rate, width, height, house_willingness,
        house_rate, sleep_rate, sleep_duration_rate, cat_removal_rate,
        initial_mice_pop, mouse_growth_rate, save_out, save_frequency,
        car_hit_prob, seed=1234):
        self.current_tick = 1 # Time tracking for policies
        self.cat_removal_rate = ((cat_removal_rate * 60) / MINUTES_PER_TICK)
        self.current_id = 1
        self.num_cats = num_cats
        self.hunger_rate = hunger_rate
        self.sleep_rate = sleep_rate
        self.sleep_duration_rate = sleep_duration_rate
        self.save_out = save_out
        self.save_frequency = save_frequency
        self.file_datetime = time.strftime("%Y_%m_%d_%H_%M",time.localtime())
        self.cat_fights = 0
        self.car_hit_prob = car_hit_prob
        self.num_cats_hit_by_car = 0
        self.num_cats_removed_under_policy = 0

        self.grid = mesa.space.MultiGrid(width, height, True)

        self.schedule = mesa.time.RandomActivation(self)

        # Maintain a list of the cats - MUST be updated by reproduction
        self.cat_list = []
        self.restaurant_list = []
        self.kitten_queue = {}

        for i in range(self.num_cats):
            curr_a = CatAgent(self.next_id(), self, hunger_rate, sleep_rate,
                sleep_duration_rate, (i % 2 == 0))
            self.schedule.add(curr_a)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(curr_a, (x, y))
            self.cat_list.append(curr_a)

        # GRID / ENVIRONMENTAL SETUP
        environment = get_locs(width, height)

        # TODO: UPDATE THIS ACCORDINGLY
        environment_params={
            "house" : (house_willingness, house_rate),
            "restaurant" : (initial_mice_pop, mouse_growth_rate)
        }

        action_zones = ["house", "restaurant"]
        for zone_type in environment:
            schedule = zone_type in action_zones
            for loc in environment[zone_type]:
                curr_a = None
                if zone_type in environment_params:
                    curr_a = class_map[zone_type](self.next_id(), self,
                        *environment_params[zone_type])
                else:
                    curr_a = class_map[zone_type](self.next_id(), self)
                if isinstance(curr_a, RestaurantAgent):
                    self.restaurant_list.append(curr_a)
                if schedule:
                    self.schedule.add(curr_a)
                self.grid.place_agent(curr_a, loc)

        self.datacollector = mesa.DataCollector(
            model_reporters = { "Hunger"      : get_hunger,
                                "Mice Pop."   : get_mice_pop,
                                "Max Hunger"  : max_hunger})

    def step(self):
        """Advance the model by one step."""
        self.datacollector.collect(self)
        self.schedule.step()
        self.current_tick += 1

        if self.current_tick % self.save_frequency == 0 and self.save_out:
            self.datacollector.get_model_vars_dataframe().to_csv(
                self.file_datetime + str(self.current_tick) + ".csv")

        if self.cat_removal_rate and \
            ((self.current_tick % self.cat_removal_rate) == 0):
            random_cat = self.random.choice(self.cat_list)
            self.grid.remove_agent(random_cat)
            self.schedule.remove(random_cat)
            self.cat_list.remove(random_cat)
            self.num_cats -=1
            self.num_cats_removed_under_policy += 1
        #print(self.kitten_queue)
        if self.current_tick in self.kitten_queue:
            num_cats_to_add = self.kitten_queue[self.current_tick]
            for i in range(num_cats_to_add):
                curr_a = CatAgent(self.next_id(), self, self.hunger_rate,
                    self.sleep_rate, self.sleep_duration_rate, (i % 2 == 0))
                self.schedule.add(curr_a)
                x = self.random.randrange(self.grid.width)
                y = self.random.randrange(self.grid.height)
                self.grid.place_agent(curr_a, (x, y))
                self.cat_list.append(curr_a)
                self.num_cats += 1
        #print(len(self.cat_list))
        print(self.cat_fights)

def agent_portrayal(agent):

    # https://www.flaticon.com/free-icon/cat_220124
    if isinstance(agent, CatAgent):
        img_file = "Images/cat_male.PNG" if agent.sex else \
            "Images/cat_female.PNG"
        portrayal = {
            "Shape" : img_file,
            "Layer" : 1,
            "scale" : 0.7
        }

    if isinstance(agent, HouseAgent):
        portrayal = {
                "Shape" : "rect",
                "Color" : ["#00EEBB"],
                "Layer" : 0,
                "w" : 0.8,
                "h" : 0.8,
                "Filled" : "false",
        }

        if agent.puts_food:
            portrayal["Color"] = "#00EEEE"
        if agent.food:
            portrayal["text"] = "F"
            portrayal["text_color"] = "black"

    if isinstance(agent, StreetAgent):
        portrayal = {
                "Shape" : "rect",
                "Color" : ["#B8B8B8"],
                "Layer" : 0,
                "w" : 0.8,
                "h" : 0.8,
                "Filled" : "false",
        }

    if isinstance(agent, BackyardAgent):
        portrayal = {
                "Shape" : "rect",
                "Color" : ["#84e184", "#adebad", "#d6f5d6"],
                "Layer" : 1 ,
                "w" : 0.8,
                "h" : 0.8,
                "Filled" : "true",
        }

    if isinstance(agent, ShopAgent):
        portrayal = {
                "Shape" : "rect",
                "Color" : "green",
                "Layer" : 0,
                "w" : 0.8,
                "h" : 0.8,
                "Filled" : "false",
        }

# https://www.clipartmax.com/png/middle/30-303462_rat-icon-enviropest-mouse.png
    if isinstance(agent, RestaurantAgent):
        portrayal = {
            "Shape" : "Images/Mouse.png",
            "Layer" : 0,
            "scale" : 0.5,
        }

    return portrayal


if __name__ == "__main__":
    model_parameters = {"width" : GRID_WIDTH, "height" : GRID_HEIGHT,
        "cat_removal_rate" : mesa.visualization.Slider(
            "Hours until cat removal", value=0, min_value=0,
            max_value=(30 * 24), step=24),
        "num_cats" : mesa.visualization.Slider(
            "Number of cats", value=10, min_value=2, max_value=100, step=2),
        "hunger_rate" : mesa.visualization.Slider(
            "Cat hunger rate (hours)", value=6, min_value=1, max_value=10,
            step=1),
        "sleep_rate" : mesa.visualization.Slider(
            "Cat sleep rate (hours)", value=.75, min_value=.25, max_value=1.25,
            step=.25),
        "sleep_duration_rate" : mesa.visualization.Slider(
            "Cat sleep duration (hours", value=1.5, min_value=1, max_value=2,
            step=.25),
        "house_willingness" : mesa.visualization.Slider(
            "House willingness", value=0.2, min_value=0, max_value=1, step=0.1),
        "house_rate" : mesa.visualization.Slider(
            "House rate (hours)", value=8, min_value=4, max_value=24, step=1),
        "initial_mice_pop" : mesa.visualization.Slider(
            "Average initial mice population", value=2, min_value=1,
            max_value=10, step=1),
        "mouse_growth_rate" : mesa.visualization.Slider(
            "Average mouse growth rate (hours)", value=72, min_value=48,
            max_value=480, step=24),
        "car_hit_prob" : mesa.visualization.Slider(
            "Car hit probability", value=.0001, min_value=.0001, max_value=0.001,
            step=.0001),
        "save_out" : mesa.visualization.Checkbox("Save data", True),
        "save_frequency" : mesa.visualization.Slider(
            "Number of ticks between saves", value=1000, min_value=1000,
            max_value=100000, step=1000)}

    grid = mesa.visualization.CanvasGrid(agent_portrayal, GRID_WIDTH,
        GRID_HEIGHT, GRID_PIXEL_WIDTH,GRID_PIXEL_HEIGHT)
    hunger_chart = mesa.visualization.ChartModule(
        [{"Label" : "Hunger", "Color" : "Black"}])
    mice_pop_chart = mesa.visualization.ChartModule(
        [{"Label" : "Mice Pop.", "Color" : "Black"}])
    max_cat_hunger_chart = mesa.visualization.ChartModule(
        [{"Label" : "Max Hunger", "Color" : "Black"}])
    server = mesa.visualization.ModularServer(
        FoodModel, [grid, max_cat_hunger_chart], "Food Model", model_parameters)
    server.launch()


