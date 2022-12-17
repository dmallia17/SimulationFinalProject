# File:         server.py
# Authors:      Artjom Plaunov and Daniel Mallia
# Class:        Modeling and Simulation (CSCI 74000)
# Professor:    Professor Vazquez-Abad
# Assignment:   Final Project
# Description:  This file contains the code necessary to run the simulation in
#               interactive and visual fashion in the browser.
# Run:          python3 server.py

from CatModel import *

# Function to define how each agent should be rendered
def agent_portrayal(agent):
    # Uses modified versions of the image from:
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
        portrayal = { # Basic house rendering
                "Shape" : "rect",
                "Color" : ["#00EEBB"],
                "Layer" : 0,
                "w" : 0.8,
                "h" : 0.8,
                "Filled" : "false",
        }
        # Modify color if house puts out food
        if agent.puts_food:
            portrayal["Color"] = "#00EEEE"
        if agent.food: # Put text if there is food there now
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

    # Uses image from:
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
        CatModel, [grid, max_cat_hunger_chart], "Cat Model", model_parameters)
    server.launch()

