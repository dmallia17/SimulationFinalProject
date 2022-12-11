import mesa
from Utilities import get_locs

class StreetAgent(mesa.Agent):
    pass

class BackyardAgent(mesa.Agent):
    pass

class ShopAgent(mesa.Agent):
    pass

class RestaurantAgent(mesa.Agent):
    pass

class CatAgent(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.is_hungry = self.random.choices([True, False], weights=[0.2,0.8])

    def step(self):
        #print("Cat: ", self.unique_id, " is hungry ", self.is_hungry, " at ", self.pos)
        if self.is_hungry:
            new_loc = None
            found_food = False
            for neighbor in self.model.grid.iter_neighbors(self.pos, True):
                if isinstance(neighbor, HouseAgent) and neighbor.food:
                    found_food = True
                    new_loc = neighbor.pos
                    break

            if new_loc is None:
                new_loc = self.random.choice(self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False))

            self.model.grid.move_agent(self, new_loc)
            #print("FOUND FOOD: ", found_food)
            if found_food:
                self.is_hungry = False
                #print("I ATE FOOD")
        else:
            self.is_hungry = self.random.choices([True, False], weights=[0.03,0.97])

class HouseAgent(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.food = True

    def step(self):
        #print("House: ", self.unique_id, " has food out ", self.food, " at ", self.pos)
        if not self.food:
            self.food = self.random.choices([True, False], weights=[0.03,0.97])

def get_hunger(model):
    return len([1 for agent in model.schedule.agents if isinstance(agent,CatAgent) and agent.is_hungry]) / len(model.schedule.agents)

class_map = {
    "street" : StreetAgent,
    "house" : HouseAgent,
    "backyard" : BackyardAgent,
    "shop" : ShopAgent,
    "restaurant" : RestaurantAgent
}

class FoodModel(mesa.Model):
    def __init__(self, num_cats, num_houses, width=20, height=24, seed=1234):
        self.current_id = 1
        self.num_cats = num_cats
        self.num_houses = num_houses

        self.grid = mesa.space.MultiGrid(width, height, True)

        self.schedule = mesa.time.RandomActivation(self)

        for i in range(self.num_cats):
            curr_a = CatAgent(self.next_id(), self)
            self.schedule.add(curr_a)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(curr_a, (x, y))

        # GRID / ENVIRONMENTAL SETUP
        environment = get_locs(width, height)

        # TODO: UPDATE THIS ACCORDINGLY
        action_zones = ["house"]
        for zone_type in environment:
            schedule = zone_type in action_zones
            for loc in environment[zone_type]:
                curr_a = class_map[zone_type](self.next_id(), self)
                if schedule:
                    self.schedule.add(curr_a)
                self.grid.place_agent(curr_a, loc)

        # for i in range(self.num_houses):
        #     curr_a = HouseAgent(self.next_id(), self)
        #     self.schedule.add(curr_a)
        #     x = self.random.randrange(self.grid.width)
        #     y = self.random.randrange(self.grid.height)
        #     self.grid.place_agent(curr_a, (x, y))

        self.datacollector = mesa.DataCollector(model_reporters={"Hunger": get_hunger})

    def step(self):
        """Advance the model by one step."""
        self.datacollector.collect(self)
        self.schedule.step()

def agent_portrayal(agent):

    # https://www.flaticon.com/free-icon/cat_220124
    if isinstance(agent, CatAgent):
        # portrayal = {
        #         "Shape" : "circle",
        #         "Color" : "red",
        #         "Filled" : "true",
        #         "Layer" : 1,
        #         "r" : 0.5
        # }

        portrayal = {
            "Shape" : "Images/cat.PNG",
            "Layer" : 1,
            "scale" : 0.7
        }

    if isinstance(agent, HouseAgent):
        portrayal = {
                "Shape" : "rect",
                "Color" : ["#00EEEE"],
                "Layer" : 0,
                "w" : 0.8,
                "h" : 0.8,
                "Filled" : "false",
                # "text" : "H",
                # "text_color" : "black"
        }

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
                "Layer" : 0,
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
        # portrayal = {
        #         "Shape" : "rect",
        #         "Color" : "yellow",
        #         "Layer" : 0,
        #         "w" : 0.8,
        #         "h" : 0.8,
        #         "Filled" : "false",
        # }

        # portrayal = {
        #         "Shape" : "House.png",
        #         "Layer" : 0,
        #         "scale" : 0.7
        # }

    return portrayal


if __name__ == "__main__":
    # MAKE THESE INTO ARGUMENTS 
    WIDTH = 20
    HEIGHT = 24
    grid = mesa.visualization.CanvasGrid(agent_portrayal, WIDTH,HEIGHT,1000,1000)
    chart = mesa.visualization.ChartModule([{"Label" : "Hunger", "Color" : "Black"}])
    server = mesa.visualization.ModularServer(
        FoodModel, [grid,chart], "Food Model",
        {"num_cats" : 10, "num_houses" : 5, "width" : WIDTH, "height" : HEIGHT}
    )
    server.launch()
    # model = FoodModel(5,5,20,20)
    # for i in range(20):
    #     model.step()


