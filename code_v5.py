import simpy
import random
import math
import pandas as pd
import csv

flight_time = pd.read_csv("flights_southwest.csv")
NUM_PASSENGERS = 175

class Passenger:
    def __init__(self, env, pid, infected=False):
        self.env = env
        self.pid = pid
        self.infected = infected
        self.incubating = False
        self.contagious = False
        self.newly_infected = False
        self.seat = None

        # Random number of connections (0, 1, or 2)
        probabilities = [0.3, 0.5, 0.2]
        outcomes = [0, 1, 2]
        self.connections_left = random.choices(outcomes, probabilities)[0]

        if self.infected:
            self.env.process(self.start_incubation())

    def start_incubation(self):
        self.incubating = True
        incubation_time = random.uniform(120, 240)  # 2-4 hours in minutes
        yield self.env.timeout(incubation_time)
        self.incubating = False
        self.contagious = True

class Flight:
    def __init__(self, env, departure, flight_time, flight_id, occupancy=NUM_PASSENGERS, infected_passengers=[]):
        self.env = env
        self.departure = departure
        self.flight_time = flight_time
        self.flight_id = flight_id
        self.occupancy = occupancy
        self.infected_passengers = []
        self.seed_infected_passengers = infected_passengers

        self.rows = (NUM_PASSENGERS + 5) // 6  # 6 seats per row (A–F)
        self.seating = {}  # seat -> Passenger
        self.bathroom = simpy.Resource(env, capacity=1)
        self.bathroom_infected = False
        self.bathroom_clean_time = 0
        self.new_infected = 0
        self.passengers = []

        self._assign_seats()
        self.env.process(self.run_flight())

    def _assign_seats(self):
        for p in self.seed_infected_passengers:
            self.infected_passengers.append(p)

        passenger_pool = [Passenger(self.env, pid=i) for i in range(self.occupancy)]

        infected_indices = random.sample(range(self.occupancy), len(self.infected_passengers))
        for idx in infected_indices:
            passenger_pool[idx].infected = True
            self.env.process(passenger_pool[idx].start_incubation())

        seats = [(r, c) for r in range(self.rows) for c in range(6)]
        assigned_seats = random.sample(seats, self.occupancy)
        for passenger, seat in zip(passenger_pool, assigned_seats):
            passenger.seat = seat
            self.seating[seat] = passenger
            self.passengers.append(passenger)

    def run_flight(self):
        for p in self.passengers:
            self.env.process(self.bathroom_behavior(p))

        while self.env.now < self.flight_time:
            yield self.env.timeout(5)
            self.handle_row_infection()

        self.finish_flight()

    def handle_row_infection(self):
        for r in range(self.rows):
            proximity_infection_rates = {
                1: 0.02 * self.flight_time,
                2: 0.01 * self.flight_time,
                3: 0.005 * self.flight_time
            }

            row_passengers = [p for p in self.passengers if p.seat[0] == r]
            contagious_passengers = [p for p in row_passengers if p.contagious]

            if contagious_passengers:
                for p in row_passengers:
                    if not (p.infected or p.incubating or p.newly_infected):
                        for contagious in contagious_passengers:
                            distance_btwn = abs(p.seat[1] - contagious.seat[1])
                            prox_infection_rate = proximity_infection_rates.get(distance_btwn, 0)

                            if random.random() < prox_infection_rate:
                                p.newly_infected = True
                                p.infected = True
                                self.env.process(p.start_incubation())
                                self.infected_passengers.append(p)
                                self.new_infected += 1

    def bathroom_behavior(self, passenger):
        while self.env.now < self.flight_time:
            lam = 2 if passenger.contagious else 0.5
            wait_time = random.expovariate(lam)
            yield self.env.timeout(wait_time)

            with self.bathroom.request() as req:
                yield req
                yield self.env.timeout(2)

                if passenger.contagious:
                    self.bathroom_infected = True
                    self.bathroom_infection_time = self.env.now

                if self.bathroom_infected and self.env.now < self.bathroom_clean_time:
                    if not (passenger.infected or passenger.incubating or passenger.newly_infected):
                        initial_infection_prob = 0.50
                        k = 0.00153  # decay rate per minute (~2.2/day)
                        t = self.env.now - self.bathroom_infection_time
                        current_infection_prob = initial_infection_prob * math.exp(-k * t)
                        if random.random() < current_infection_prob:
                            passenger.newly_infected = True
                            passenger.infected = True
                            self.env.process(passenger.start_incubation())
                            self.infected_passengers.append(passenger)
                            self.new_infected += 1

    def finish_flight(self):
        infected = [p for p in self.passengers if p.infected]
        new_infected = len([p for p in self.passengers if p.newly_infected])
        departing = [p for p in self.passengers if not p.contagious]
        continuing = []

        print(f"\nFlight {self.flight_id} Summary at {self.env.now:.1f} min")
        print(f"Total passengers: {len(self.passengers)}")
        print(f"New infections: {new_infected}")
        print(f"Departing passengers: {len(departing)}")
        #print(f"Placeholder - continuing passengers: {len(continuing)}")

        return [p.pid for p in infected], new_infected

def generate_layover():
    """Generate layover time in minutes between 30 and 180, centered at 105."""
    return max(30, min(180, random.normalvariate(105, 25)))

def generate_flight_duration():
    """randomly select a flight time from the logs sheet"""
    airtimes = flight_time["air_time"].dropna().astype(float)
    return random.choice(airtimes.tolist())

def run():
    SIM_DURATION = 48 * 60  # 48 hours
    OCCUPANCY = 175

    env = simpy.Environment()
    flight_id = 1
    flights = []

    initial_infected = []
    for i in range(5): # five passengers start as infected and contagious
        p = Passenger(env, pid=i, infected=True)
        p.incubating = False
        p.contagious = True
        initial_infected.append(p)
        
    total_infected = set(p.pid for p in initial_infected)  # Track unique infected passenger IDs
    new_infected = 0  # Initialize new_infected to track cumulative new infections
    
    first_duration = generate_flight_duration()

    first_flight = Flight(env, departure=0, flight_time=first_duration, flight_id=flight_id,
                          occupancy=OCCUPANCY, infected_passengers=initial_infected)
    flights.append(first_flight)

    def flight_chain(flight, flight_end_time):
        nonlocal new_infected, flight_id
        yield env.timeout(flight.flight_time)
        infected_ids, flight_new_infected = flight.finish_flight()
        new_infected += flight_new_infected  # Add up new infections
        total_infected.update(infected_ids)
        
        layover_groups = {}

        for p in flight.passengers:
            if p.pid in infected_ids:
                layover = generate_layover()
                next_departure = flight_end_time + layover

                if next_departure < SIM_DURATION:
                    if next_departure not in layover_groups:
                        layover_groups[next_departure] = []
                    layover_groups[next_departure].append(p)

        for departure_time, passengers in layover_groups.items():
            flight_id += 1
            next_duration = generate_flight_duration()
            next_flight = Flight(env, departure=departure_time, flight_time=next_duration,
                                 flight_id=flight_id, occupancy=OCCUPANCY,
                                 infected_passengers=passengers)
            flights.append(next_flight)
            env.process(flight_chain(next_flight, departure_time + next_duration))

    env.process(flight_chain(first_flight, 0 + first_duration))
    env.run(until=SIM_DURATION)

    print("\n==== Simulation Complete ====")
    print(f"Total Flights Simulated: {len(flights)}")
    # total_infected = sum(len(f.infected_passengers) for f in flights)
    print(f"Total Newly Infected (cumulative, may include duplicates): {new_infected}")
    print(f"Total Infected (cumulative): {len(total_infected)}")
    
    return len(flights), new_infected, len(total_infected)

if __name__ == "__main__":
    n_runs = 10  # Number of simulation runs
    results = []
    
    for i in range(n_runs):
        random.seed(i)
        print(f"\n==== Run {i + 1} ====")
        num_flights, newly, total = run()
        results.append({'run':i+1, 'total_flights':num_flights, 'newly_infected':newly, 'total_infected':total})
        
    # Save to CSV: from ChatGPT
    with open("simulation_results.csv", "w", newline="") as csvfile:
        fieldnames = ["run", "total_flights", "newly_infected", "total_infected"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(results)
