# Modeling and Simulation (CSCI 74000) Final Project 
## Authors: Artjom Plaunov and Daniel Mallia

## Description
This repository constitutes an attempt to simulate outdoor (unowned / not pets)
 cat life in a fairly residential, urban environment for the purposes of
understanding multiple trends and quantities with respect to the cats and their
 environmental impact. Namely, we simulate to understand:
- Cat growth trends, both the course of the simulation length and projected
  into the future by making use of the number of pregnancies at the end of the
  simulated period. In connection with this we estimate how many cats will be
  hit by cars.
- Mouse growth trends, understanding how the mouse population (explored here in
  simple fashion) may grow or shrink with respect to a certain cat population.
- The number of cat fights - a measure of how much of a nuisance cats might be
  to their human neighbors.

Simulation is conducted under an Agent Based Modeling (ABM) approach, making
use of Python and the excellent ABM package, Mesa. We emphasize considerable
temporal detail, making use of a 15 minute increment per step or tick in the
simulation.

## Setup
This project assumes an installation of Python (>= 3.8.5) as well as the
packages in requirements.txt. To install them you can run:

```
pip3 install -r requirements.txt
```

If any issues are encountered in installing using this requirments file
(possibly due to cross-platform compatibility issues), this project really only 
requires 5 packages: mesa, pandas, numpy, scipy and matplotlib. As long as you
can set up Python 3.8.5 (with which this was tested) and pip, then install
these 5, you shouldn't encounter any problems.

## How to run
To run the **interactive version** of the simulation use the following:
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

To run the simulation in **batch run mode** for simulating growth trends and
estimating parameters, use:
```
python3 batch_run.py
```

Please note the following:
- To have reproducible results, you should control the number of simulations to
  be run by using the ```--repro_iter``` and ```--seed``` arguments; for
  instance ```--repro_iter 10 --seed 1234``` will execute 10 runs of the
  simulation under the given parameters and if run again for the same number of
  iterations with the same seed, the results will be identical. The default is
  to run 10 reproducible iterations with a seed of 1234.
- The default setting for ```--data_collection_period``` is 96; 96 ticks =
  1 day under the initial simulation time setting of 15 minutes per tick. This
  will ensure that the growth trends will be updated on a per day basis. We
  advise leaving this as it is or increasing it for longer simulation runs;
  shortening it may cause a failure in the plotting of the growth trends
