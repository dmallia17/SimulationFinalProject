# File:         batch_run.py
# Authors:      Artjom Plaunov and Daniel Mallia
# Class:        Modeling and Simulation (CSCI 74000)
# Professor:    Professor Vazquez-Abad
# Assignment:   Final Project
# Description:  This file contains the code necessary to run the simulation in
#               batch run mode for proper estimation.
# Run:          python3 batch_run.py

import argparse, json, time
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
    
    args = parser.parse_args()
    
    # Verify all simulation arguments against the min, max and step specified
    # in the JSON file
    check_args(args, sim_params)
    time.sleep(5) # Sleep so warnings can be clearly observed






