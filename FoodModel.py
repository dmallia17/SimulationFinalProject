import mesa

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
                if isinstance(neighbor, Household) and neighbor.food:
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

class Household(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.food = True

    def step(self):
        #print("House: ", self.unique_id, " has food out ", self.food, " at ", self.pos)
        if not self.food:
            self.food = self.random.choices([True, False], weights=[0.2,0.8])


class FoodModel(mesa.Model):
    def __init__(self, num_cats, num_houses, width, height, seed=1234):
        self.num_cats = num_cats
        self.num_houses = num_houses

        self.grid = mesa.space.MultiGrid(width, height, True)

        self.schedule = mesa.time.RandomActivation(self)

        for i in range(self.num_cats):
            curr_a = CatAgent(i, self)
            self.schedule.add(curr_a)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(curr_a, (x, y))

        for i in range(self.num_cats, self.num_cats + self.num_houses):
            curr_a = Household(i, self)
            self.schedule.add(curr_a)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(curr_a, (x, y))

    def step(self):
        """Advance the model by one step."""
        self.schedule.step()

def agent_portrayal(agent):
    portrayal = {
            "Shape" : "circle",
            "Color" : "red",
            "Filled" : "true",
            "Layer" : 0,
            "r" : 0.5
    }

    if isinstance(agent, Household):
        portrayal["Color"] = "blue"
        portrayal["Layer"] = 1
        portrayal["r"] = 0.2

    return portrayal


if __name__ == "__main__":
    grid = mesa.visualization.CanvasGrid(agent_portrayal, 20,20,500,500)
    server = mesa.visualization.ModularServer(
        FoodModel, [grid], "Food Model",
        {"num_cats" : 100, "num_houses" : 5, "width" : 20, "height" : 20}
    )
    server.launch()
    # model = FoodModel(5,5,20,20)
    # for i in range(20):
    #     model.step()


