# A Data-driven Adaptive Koopman Identification for Nonautonomous Systems

## Overview of Project 

This code can be used to identidy nonautonomous systems directly from data using an adaptive Koopman operator.
The identification performence is compared between another four variants. 

The provided examples use a water network simulator pystorm (https://github.com/kLabUM/pystorms.git).

Below are the names and descriptions of some of the included contents:

### `models/`
	Contains five adaptive data-driven system identification models.
	-Koopman.py		- Builds an adaptive Koopman model from data.
	-Koopman_liftCtrl.py	- Builds an adaptive Koopman model with imputs lifted from data.
	-DMD.py			- Builds an adaptive DMD model from data.
	-NARX.py 		- Builds an adaptive NARX model from data.
	-MovingAnchor.py	- Builds an adaptive Moving Anchoring model from data.
	
### `controllers/`
	Contains MPC controller used to control involved systems.
	-MPC_cvx.py		- Builds a linear MPC controller from a Koopman model
	
### `tests/`      		
	Where saved examples
	-systems.py		- Defines candidate systems for tests.
	-Delta.py		- Uses system Delta in pystorm.
	-Theta.py		- Uses system Theta in pystorm.	


## How to construct an adaptive Koopman model from data

### Step 1. Provide nonautonomous systems
	You need to customize you own models by changing parameters in `tests/systems.py` file:
	Name:                       Semantics:
	'statesUpper'               States upper bounds
	'statesLower'               States lower bounds
	'inputUpper'                Inputs upper bounds
	'inputLower'                Inputs lower bounds
	'simulator'                 Simulation with control inputs and state outputs 

### Step 2. Run adaptive identification 
Each identification needs to go through model initialization and model updates. 

### Step 3. Visualize results
Comparison plots between different adaptive methods will be generated in the end of test.
Template code file is provided in the `tests/` folder.


## Running Examples
Examples provided here use pystorm, which can be installed according to the instruction.

	Two example files are included in the folder test/:
	-Delta.py
	-Theta.py

Each of these files will simulate a water network system, conduct system identification with the adaptive Koopman operator, construct an MPC controller based on the identified model, and compare its identification performance with another four adaptive methods.

You can change the parameters (the forgetting factor, the initialization time, the adaptive period, etc.) of the adaptive identification methods.
