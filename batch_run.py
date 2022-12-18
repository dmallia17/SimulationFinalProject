# File:         batch_run.py
# Authors:      Artjom Plaunov and Daniel Mallia
# Class:        Modeling and Simulation (CSCI 74000)
# Professor:    Professor Vazquez-Abad
# Assignment:   Final Project
# Description:  This file contains the code necessary to run the simulation in
#               batch run mode for proper estimation.
# Run:          python3 batch_run.py

import argparse, json, time
import mesa
import pandas as pd
from CatModel import *
from Utilities import populate_parser, check_args


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
    args = parser.parse_args()
    args_sim_params = {k : v for k,v in vars(args).items() if k in sim_params}
    #print(args)

    # Verify all simulation arguments against the min, max and step specified
    # in the JSON file
    check_args(args_sim_params, sim_params)
    time.sleep(3) # Sleep so warnings can be clearly observed

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

    # for i in results:
    #     print(i)

    # print(pd.DataFrame(results))
    #print(results)


