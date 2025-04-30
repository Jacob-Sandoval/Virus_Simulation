# Flight Transmission Simulation

## Overview
This simulation models the spread of an infectious disease through interconnected flights. It tracks how infections spread among passengers during flights and across connecting flights, considering various transmission vectors including proximity in seating and bathroom usage.

## Features
- Models infection spread based on passenger proximity
- Simulates bathroom usage as a transmission vector
- Tracks passengers across connecting flights
- Models varying incubation periods and contagiousness
- Supports variable flight durations based on real flight data
- Generates realistic layover times between connections
- Collects and reports statistics on infection spread

## Requirements
- Python 3.6+
- SimPy
- Pandas
- CSV file with flight duration data (`flights_southwest.csv`)

## Key Components

### Passenger Class
Represents an individual passenger with attributes:
- Infection status (susceptible, incubating, contagious)
- Seat assignment
- Number of connections remaining
- Incubation process

### Flight Class
Models a single flight with:
- Seating arrangements (rows and seats)
- Bathroom as a shared resource
- Processes for in-flight infection transmission
- Tracking of newly infected passengers

### Simulation Logic
- Initializes with a small number of infected passengers
- Models transmission through close proximity in airplane seating
- Models transmission through shared bathroom usage with decay of viral particles
- Tracks passengers making connecting flights
- Records statistics on infection spread

## Configuration Parameters
- `NUM_PASSENGERS`: Number of passengers per flight (default: 175)
- `SIM_DURATION`: Total simulation duration in minutes (default: 48 hours)
- `n_runs`: Number of simulation runs to average results (default: 10)

## Infection Dynamics
- Proximity-based transmission with distance-dependent rates
- Bathroom-based transmission with time-decay of infection probability
- Incubation period varies between 2-4 hours

## Usage
```python
python code_v5.py
```

The simulation will:
1. Run the specified number of simulations
2. Output progress and results to the console
3. Save aggregated results to `simulation_results.csv`

## Output Data
The simulation generates a CSV file with the following columns:
- `run`: Simulation run number
- `total_flights`: Number of flights simulated in the run
- `newly_infected`: Number of new infections that occurred during the simulation
- `total_infected`: Total number of unique infected passengers by the end of the simulation

## Example Output
```
==== Run 1 ====

Flight 1 Summary at 120.0 min
Total passengers: 175
New infections: 8
Departing passengers: 170

Flight 2 Summary at 225.0 min
Total passengers: 175
New infections: 12
Departing passengers: 163

...

==== Simulation Complete ====
Total Flights Simulated: 45
Total Newly Infected (cumulative, may include duplicates): 320
Total Infected (cumulative): 325
```

## Notes
- The simulation uses realistic flight durations from the `flights_southwest.csv` file
- Layover times are generated from a normal distribution between 30-180 minutes
- Each passenger has a random probability of having connecting flights
- The model assumes passengers remain infectious across multiple flights
- Bathroom contamination decreases exponentially over time

## Extending the Model
To modify this simulation, consider adjusting:
- Infection parameters in the `handle_row_infection` and `bathroom_behavior` methods
- Flight capacity and configuration in the `Flight` class
- Incubation periods and contagiousness in the `Passenger` class
- Layover time distributions in the `generate_layover` function