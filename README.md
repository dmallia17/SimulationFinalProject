# Modeling and Simulation (CSCI 74000) Final Project 
## Authors: Artjom Plaunov and Daniel Mallia

## Description

## Setup
This project assumes an installation of Python (>= 3.8.5) as well as the
packages in requirements.txt. To install them you can run:

```
pip3 install -r requirements.txt
```

If any issues are encountered in installing using this requirments file
(possibly due to cross-platform compatibility issues), this project really only 
requires 4 packages: mesa, pandas, numpy and matplotlib. As long as you can set
up Python 3.8.5 (with which this was tested) and pip, then install these 4, you
shouldn't encounter any problems.

## How to run
To run the interactive version of the simulation use the following:
```
python3 server.py
```

Please note the following:
- server.py has multiple arguments for controlling which plots you would like
  to generate as the simulation runs. Pass ```--all_charts``` to include all,
  or choose among the other arguments.
- If you adjust parameters in the browser, such as the number of cats, you must
  reset the session (using the reset button on the top) for the changes to
  take effect.
