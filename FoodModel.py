import mesa
import numpy as np
from Utilities import get_locs

GRID_PIXEL_WIDTH = 1000
GRID_PIXEL_HEIGHT = 1000
GRID_WIDTH = 20
GRID_HEIGHT = 24
MINUTES_PER_TICK = 15
# Ticks per average mouse arrival
MAX_MOUSE_GROWTH_RATE = (48 * 60) / MINUTES_PER_TICK

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
        sleep_duration_rate):
        super().__init__(unique_id, model)
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
    # - Mice                [ ]
    def find_food(self):
        new_loc = None
        # Do a search of radius 1 for houses with food
        for neighbor in self.model.grid.iter_neighbors(self.pos, True, True):
            if (isinstance(neighbor, HouseAgent) and neighbor.food) or \
                (isinstance(neighbor, RestaurantAgent) and neighbor.mice_pop > 0):
                new_loc = neighbor.pos
                self.found_food = neighbor
                self.found_food_type = type(neighbor)
                break

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
    # - Pregnant (if female)        [ ]
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

    # Handles movement under...
    # CAT PRIORITIES
    # Hunger                        [X]
    # Reproduce                     [ ]
    # Sleep                         [X] (move does not get called)
    # Wander                        [ ]
    def move(self):
        if self.is_hungry:
            new_loc = self.find_food()

            self.model.grid.move_agent(self, new_loc)
        # CHANGE
        else: # Wander
            self.model.grid.move_agent(self,
                self.random.choice(self.model.grid.get_neighborhood(
                                   self.pos, 
                                   moore=True, 
                                   include_center=False)))

    # A CAT MAY
    # - Eat house food              [X]
    # - Eat mice                    [ ]
    # - Eat bird                    [ ]
    # - Fight                       [ ]
    # - Reproduce                   [ ]
    # - Killed by fight             [ ]
    # - Killed by car               [ ]
    def act(self):
        # Encountered other cat?

        # Came here to eat? 
        if self.found_food:
            food_success = False
            if self.found_food_type is HouseAgent:
                self.is_hungry = False
                self.found_food.food = False
                food_success = True
            elif self.found_food_type is RestaurantAgent:
                u = self.random.uniform(0,1)
                if (u < self.hunt_ability * self.found_food.mouse_prob):
                    food_success = True
                    self.is_hungry = False
                    self.found_food.mice_pop -= 1
                    self.found_food.mice_caught += 1
                    self.found_food.mouse_growth_rate += 1
            self.ticks_until_hungry = np.random.poisson(self.hunger_rate) \
                if food_success else self.ticks_until_hungry
            #print("I ATE FOOD")

        # Wandering?

    def step(self):
        print("Is asleep:", self.is_asleep)
        print("Is sleepy:", self.is_sleepy)
        print("Ticks until sleepy:", self.ticks_until_sleepy)
        print("Ticks until awake:", self.ticks_until_awake)

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
            self.rate = np.random.poisson(rate)
            self.food_p = 1 / ((self.rate * 60) / MINUTES_PER_TICK)
            self.food_p_n = 1 - self.food_p

    def step(self):
        #print("House: ", self.unique_id, " has food out ", self.food, " at ",
        # self.pos)
        if self.puts_food and not self.food:
            self.food = self.random.choices([True, False],
                weights=[self.food_p,self.food_p_n])[0]

def get_hunger(model):
    num_cats = len(model.cat_list)
    return 0 if not num_cats else \
        (len([1 for cat in model.cat_list if cat.is_hungry]) / num_cats)

def get_mice_pop(model):
    restaurants = model.restaurant_list
    return sum([res.mice_pop for res in restaurants])

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
        initial_mice_pop, mouse_growth_rate, seed=1234):
        self.current_tick = 1 # Time tracking for policies
        self.cat_removal_rate = ((cat_removal_rate * 60) / MINUTES_PER_TICK)
        self.current_id = 1
        self.num_cats = num_cats

        self.grid = mesa.space.MultiGrid(width, height, True)

        self.schedule = mesa.time.RandomActivation(self)

        # Maintain a list of the cats - MUST be updated by reproduction
        self.cat_list = []
        self.restaurant_list = []

        for i in range(self.num_cats):
            curr_a = CatAgent(self.next_id(), self, hunger_rate, sleep_rate,
                sleep_duration_rate)
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
                                "Mice Pop."   : get_mice_pop})

    def step(self):
        """Advance the model by one step."""
        self.datacollector.collect(self)
        self.schedule.step()
        self.current_tick += 1
        if self.cat_removal_rate and \
            ((self.current_tick % self.cat_removal_rate) == 0):
            random_cat = self.random.choice(self.cat_list)
            self.grid.remove_agent(random_cat)
            self.schedule.remove(random_cat)
            self.cat_list.remove(random_cat)

def agent_portrayal(agent):

    # https://www.flaticon.com/free-icon/cat_220124
    if isinstance(agent, CatAgent):
        portrayal = {
            "Shape" : "Images/cat.PNG",
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
            "Number of cats", value=10, min_value=1, max_value=100, step=1),
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
            max_value=480, step=24)}

    grid = mesa.visualization.CanvasGrid(agent_portrayal, GRID_WIDTH,
        GRID_HEIGHT, GRID_PIXEL_WIDTH,GRID_PIXEL_HEIGHT)
    chart = mesa.visualization.ChartModule(
        [{"Label" : "Hunger", "Color" : "Black"}])
    chart2 = mesa.visualization.ChartModule(
        [{"Label" : "Mice Pop.", "Color" : "Black"}])
    server = mesa.visualization.ModularServer(
        FoodModel, [grid, chart2], "Food Model", model_parameters)
    server.launch()


