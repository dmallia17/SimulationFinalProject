# File:         server.py
# Authors:      Artjom Plaunov and Daniel Mallia
# Class:        Modeling and Simulation (CSCI 74000)
# Professor:    Professor Vazquez-Abad
# Assignment:   Final Project
# Description:  This file contains the code necessary to run the simulation in
#               interactive and visual fashion in the browser.
# Run:          python3 server.py

import argparse, json
from CatModel import *
from Utilities import get_mesa_visualization_element

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
    # Read in JSON file with simulation parameters
    with open("simulation_params.json", "r") as f:
        sim_params = json.load(f)

    parser = argparse.ArgumentParser(
        description="Run interactive Cat ABM simulation")
    parser.add_argument("--hunger_chart", action="store_true")
    parser.add_argument("--mice_pop_chart", action="store_true")
    parser.add_argument("--max_hunger_chart", action="store_true")
    parser.add_argument("--all_charts", action="store_true")
    parser.add_argument("--grid_px_width", type=int, default=1000,
        help="Width of the grid display in pixels")
    parser.add_argument("--grid_px_height", type=int, default=1000,
        help="Height of the grid display in pixels")
    args = parser.parse_args()

    model_parameters = {
        k : get_mesa_visualization_element(sim_params,k) for k in sim_params}

    grid = mesa.visualization.CanvasGrid(agent_portrayal, GRID_WIDTH,
        GRID_HEIGHT, args.grid_px_width, args.grid_px_height)
    charts=[]
    if args.all_charts or args.hunger_chart:
        charts.append(mesa.visualization.ChartModule(
            [{"Label" : "Hunger", "Color" : "Black"}]))
    if args.all_charts or args.mice_pop_chart:
        charts.append(mesa.visualization.ChartModule(
            [{"Label" : "Mice Pop.", "Color" : "Black"}]))
    if args.all_charts or args.max_hunger_chart:
        charts.append(mesa.visualization.ChartModule(
            [{"Label" : "Max Hunger", "Color" : "Black"}]))
    elements = [grid] + charts
    server = mesa.visualization.ModularServer(
        CatModel, elements, "Cat Model", model_parameters)
    server.launch()

