# File:         batch_run.py
# Authors:      Artjom Plaunov and Daniel Mallia
# Class:        Modeling and Simulation (CSCI 74000)
# Professor:    Professor Vazquez-Abad
# Assignment:   Final Project
# Description:  This file contains the code necessary to run the simulation in
#               batch run mode for proper estimation.
# Run:          python3 batch_run.py

import argparse, json, time, random
import mesa
import pandas as pd
import matplotlib.pyplot as plt
from CatModel import *
from Utilities import populate_parser, check_args

def get_pop_plot(res_df, population, datetime):
    mean_pop = res_df.groupby(["Step"]).mean()[population + " Pop."]
    sd_pop = res_df.groupby(["Step"]).std()[population + " Pop."]

    fig, ax = plt.subplots()
    x_axis = mean_pop.index.to_numpy() / 96
    ax.fill_between(x_axis, mean_pop - sd_pop,
        mean_pop + sd_pop, alpha=.5, linewidth=0)
    ax.plot(x_axis, mean_pop, linewidth=2)
    ax.set_xlabel("Days")
    ax.set_ylabel(population + " population")
    ax.set_title(population + " population growth")
    fig.savefig("Plots/" + datetime + population + "_pop_growth.png")
    plt.close()

if __name__ == "__main__":
    # Read in JSON file with simulation parameters
    with open("simulation_params.json", "r") as f:
        sim_params = json.load(f)

    parser = argparse.ArgumentParser(
        description="Run Cat ABM simulation in batch run mode")
    # Pull simulation arguments from JSON file
    populate_parser(parser, sim_params)
    # Add batch running arguments
    parser.add_argument("--number_processes", type=int, default=1,
        help="Number of processes to use for batch running")
    parser.add_argument("--iterations", type=int, default=1,
        help="Number of times to run for each combination of parameters")
    parser.add_argument("--data_collection_period", type=int, default=-1,
        help="How many steps in between collection (-1 = only at end)")
    parser.add_argument("--max_steps", type=int, default=1000,
        help="How many steps to run the simulation")
    parser.add_argument("--no_display_progress", action="store_false")
    parser.add_argument("--repro_iter", type=int, default=0,
        help="Use this to set how many unique seeds to use")
    parser.add_argument("--seed", type=int, default=1234,
        help="Seed for reproducibility")
    args = parser.parse_args()
    args_sim_params = {k : v for k,v in vars(args).items() if k in sim_params}
    #print(args)

    file_datetime = time.strftime("%Y_%m_%d_%H_%M_",time.localtime())

    # Verify all simulation arguments against the min, max and step specified
    # in the JSON file
    check_args(args_sim_params, sim_params)
    time.sleep(3) # Sleep so warnings can be clearly observed

    if args.repro_iter:
        args_sim_params["seed"] = range(args.seed, args.seed + args.repro_iter)

    # Run
    results = mesa.batch_run(
        CatModel,
        parameters=args_sim_params,
        number_processes=args.number_processes,
        iterations=args.iterations,
        data_collection_period=args.data_collection_period,
        max_steps=args.max_steps,
        display_progress=args.no_display_progress
    )

    res_df = pd.DataFrame(results)

    # Plot cat population over time
    get_pop_plot(res_df, "Cat", file_datetime)
    get_pop_plot(res_df, "Mice", file_datetime)


