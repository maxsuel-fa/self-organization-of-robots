"""
File: multiple_simulations.py
Group: 5 
Date of creation: 17/04/2024
Brief: Implements the run object
Authors: Mateus Goto, Maxsuel Fernandes, João Pedro Regazzi
"""

import itertools
import csv
import os
from datetime import datetime
from statistics import mean  

from model import RobotMission


# --------------------------------------------------------------------------- #
# Parameter space:  three scenarios for robots, three levels for waste
# --------------------------------------------------------------------------- #
HEURISTICS      = [#"astar",
                   "closest",
                   "random",
                   "min_total_distance"
                   ]

ROBOT_SCENARIOS = [1, # same count for green, yellow, red
                   2,
                   4
                   ]

WASTE_LEVELS    = [4,  # same amount for green, yellow, red
                   8,
                   16
                   ]

MAX_STEPS       = 10000
NUM_RUNS       = 100   

# --------------------------------------------------------------------------- #
# Output – folder + CSV
# --------------------------------------------------------------------------- #
OUT_DIR   = "batch_results"
os.makedirs(OUT_DIR, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
CSV_PATH  = os.path.join(OUT_DIR, f"results_{timestamp}.csv")

CSV_HEADER = [
    "heuristic",
    "num_green",
    "num_yellow",
    "num_red",
    "green_waste",
    "yellow_waste",
    "red_waste",
    "steps_to_finish",
    "total_distance_traveled",
    "delivered_waste"
]

# --------------------------------------------------------------------------- #
# Run the experiments
# --------------------------------------------------------------------------- #
with open(CSV_PATH, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(CSV_HEADER)

        # ----------------------------------------------------------------------- #
    # iterate over heuristic × robot‑scenario × waste‑level
    # ----------------------------------------------------------------------- #
    for heuristic in HEURISTICS:
        for robots in ROBOT_SCENARIOS:
            for waste in WASTE_LEVELS:

                step_runs  = []
                dist_runs  = []
                deli_runs  = []

                print(f"Heuristic: {heuristic}   -   Robots: {robots}   -   Waste: {waste}")
                for _ in range(NUM_RUNS):              
                    model = RobotMission(
                        width=30, height=30,
                        num_green=robots, num_yellow=robots, num_red=robots,
                        num_green_waste=waste,
                        num_yellow_waste=waste,
                        num_red_waste=waste,
                        heuristic=heuristic,
                    )

                    while not model.finished and model.step_count < MAX_STEPS:
                        model.step()

                    step_runs.append(model.step_count)

                    total_distance = sum(
                        getattr(a, "distance_traveled", 0)
                        for a in model.custom_agents
                        if hasattr(a, "distance_traveled")
                    )

                    dist_runs.append(total_distance)
                    deli_runs.append(model.waste_delivered_count)

                writer.writerow([
                    heuristic,
                    robots, robots, robots,        # num_green / yellow / red
                    waste, waste, waste,           # green / yellow / red waste
                    round(mean(step_runs), 2),       # steps_to_finish (avg)
                    round(mean(dist_runs), 2),       # total_distance (avg)
                    round(mean(deli_runs), 2),       # delivered_waste (avg)
                ])


print(f"✓ Finished. CSV saved to {CSV_PATH}")
