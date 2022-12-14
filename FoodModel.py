import mesa
import numpy as np
from Utilities import get_locs

GRID_PIXEL_WIDTH = 1000
GRID_PIXEL_HEIGHT = 1000
GRID_WIDTH = 20
GRID_HEIGHT = 24
MINUTES_PER_TICK = 15

class StreetAgent(mesa.Agent):
    pass

class BackyardAgent(mesa.Agent):
    pass

class ShopAgent(mesa.Agent):
    pass

class RestaurantAgent(mesa.Agent):
    pass

class CatAgent(mesa.Agent):
    # @param hunger_rate Rate in hours until hungry
    def __init__(self, unique_id, model, hunger_rate):
        super().__init__(unique_id, model)
        self.hunger_rate = np.random.poisson((hunger_rate * 60) / MINUTES_PER_TICK)
        self.is_hungry = self.random.choices(
            [True, False], weights=[0.2,0.8])[0]
        self.ticks_until_hungry = 0 if self.is_hungry else \
            np.random.poisson(self.hunger_rate)
        self.found_food = None # Food zone (e.g. House)
        self.found_food_type = None # Food zone type (e.g. HouseAgent)

    def cat_encounter(self, other):
        pass

    # Looking for food...
    # - Houses              [ ]
    # - Birds               [ ]
    # - Mice                [ ]
    def find_food(self):
        new_loc = None
        # Do a search of radius 1 for houses with food
        for neighbor in self.model.grid.iter_neighbors(self.pos, True, True):
            if isinstance(neighbor, HouseAgent) and neighbor.food:
                new_loc = neighbor.pos
                self.found_food = neighbor
                self.found_food_type = HouseAgent
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
    # - Need to sleep               [ ]
    # - Pregnant (if female)        [ ]
    # - Injured                     [ ]
    # - Starved                     [ ]
    # Mostly captures change due to time
    def update_state(self):
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
    # Wander                        [ ]
    def move(self):
        if self.is_hungry:
            new_loc = self.find_food()

            self.model.grid.move_agent(self, new_loc)
        # CHANGE
        else:
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
            if self.found_food_type is HouseAgent:
                self.is_hungry = False
                self.found_food.food = False
            self.ticks_until_hungry = np.random.poisson(self.hunger_rate)
            #print("I ATE FOOD")

        # Wandering?

    def step(self):
        #print("Cat: ", self.unique_id, " is hungry ", self.is_hungry, " at ",
        # self.pos)
        self.update_state()
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
    return len([1 for agent in model.schedule.agents \
        if isinstance(agent,CatAgent) and agent.is_hungry]) / \
        len([1 for agent in model.schedule.agents \
            if isinstance(agent,CatAgent)])

class_map = {
    "street" : StreetAgent,
    "house" : HouseAgent,
    "backyard" : BackyardAgent,
    "shop" : ShopAgent,
    "restaurant" : RestaurantAgent
}

class FoodModel(mesa.Model):
    def __init__(self, num_cats, hunger_rate, width, height, house_willingness,
        house_rate, seed=1234):
        self.current_id = 1
        self.num_cats = num_cats

        self.grid = mesa.space.MultiGrid(width, height, True)

        self.schedule = mesa.time.RandomActivation(self)

        for i in range(self.num_cats):
            curr_a = CatAgent(self.next_id(), self, hunger_rate)
            self.schedule.add(curr_a)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(curr_a, (x, y))

        # GRID / ENVIRONMENTAL SETUP
        environment = get_locs(width, height)

        # TODO: UPDATE THIS ACCORDINGLY
        environment_params={
            "house" : (house_willingness, house_rate)
        }

        action_zones = ["house"]
        for zone_type in environment:
            schedule = zone_type in action_zones
            for loc in environment[zone_type]:
                if zone_type in environment_params:
                    curr_a = class_map[zone_type](self.next_id(), self,
                        *environment_params[zone_type])
                else:
                    curr_a = class_map[zone_type](self.next_id(), self)
                if schedule:
                    self.schedule.add(curr_a)
                self.grid.place_agent(curr_a, loc)

        self.datacollector = mesa.DataCollector(
            model_reporters={"Hunger": get_hunger})

    def step(self):
        """Advance the model by one step."""
        self.datacollector.collect(self)
        self.schedule.step()

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
        "num_cats" : mesa.visualization.Slider(
            "Number of cats", value=10, min_value=1, max_value=100, step=1),
        "hunger_rate" : mesa.visualization.Slider(
            "Cat hunger rate (hours)", value=6, min_value=1, max_value=10,
            step=1),
        "house_willingness" : mesa.visualization.Slider(
            "House willingness", value=0.2, min_value=0, max_value=1, step=0.1),
        "house_rate" : mesa.visualization.Slider(
            "House rate (hours)", value=8, min_value=4, max_value=24, step=1)}

    grid = mesa.visualization.CanvasGrid(agent_portrayal, GRID_WIDTH,
        GRID_HEIGHT, GRID_PIXEL_WIDTH,GRID_PIXEL_HEIGHT)
    chart = mesa.visualization.ChartModule(
        [{"Label" : "Hunger", "Color" : "Black"}])
    server = mesa.visualization.ModularServer(
        FoodModel, [grid,chart], "Food Model", model_parameters)
    server.launch()


