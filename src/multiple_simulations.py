"""
File: multiple_simulations.py
Runs many parameter combinations of RobotMission and stores summary stats.
Compatible with the April 2025 code (closest / farthest / min_total_distance).
"""

import csv
import os
from datetime import datetime
from statistics import mean

from model import RobotMission

# --------------------------------------------------------------------- #
# Parameter space
# --------------------------------------------------------------------- #
HEURISTICS      = ["closest",
                   "farthest",
                   "min_total_distance"]

ROBOT_SCENARIOS = [1, 2, 4]      # same count for green, yellow, red
WASTE_LEVELS    = [4, 8, 16]     # same count for green, yellow, red

NUM_RUNS        = 100
MAX_STEPS       = 10000

# --------------------------------------------------------------------- #
# Output – folder + CSV
# --------------------------------------------------------------------- #
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
    "avg_steps_to_finish",
    "avg_total_distance",
    "avg_delivered_waste",
    "win_rate",
    "gameover_rate",
]

# --------------------------------------------------------------------- #
# Helper to run one batch and collect stats
# --------------------------------------------------------------------- #
def run_batch(heuristic: str, robots: int, waste: int):
    step_runs, dist_runs, deli_runs = [], [], []
    wins = 0; gameovers = 0

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

        # ignore unfinished runs (should be rare now)
        if model.step_count >= MAX_STEPS and model.status == "running":
            continue

        step_runs.append(model.step_count)

        dist_runs.append(sum(
            getattr(a, "distance_traveled", 0)
            for a in model.custom_agents
            if hasattr(a, "distance_traveled")
        ))
        deli_runs.append(model.waste_delivered_count)

        if model.status == "win":
            wins += 1
        elif model.status == "gameover":
            gameovers += 1

    n = len(step_runs) or 1   # guard against division by zero
    return (
        round(mean(step_runs), 2),
        round(mean(dist_runs), 2),
        round(mean(deli_runs), 2),
        round(wins / n, 3),
        round(gameovers / n, 3),
    )

# --------------------------------------------------------------------- #
# Run the experiments and write CSV
# --------------------------------------------------------------------- #
with open(CSV_PATH, "w", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(CSV_HEADER)

    for h in HEURISTICS:
        for r in ROBOT_SCENARIOS:
            for w in WASTE_LEVELS:
                print(f"Running – heuristic={h}, robots={r}, waste={w}")
                stats = run_batch(h, r, w)

                writer.writerow([
                    h,
                    r, r, r,             # num_green / yellow / red
                    w, w, w,             # green / yellow / red waste
                    *stats               # unpack the six computed values
                ])

print(f"✓ Finished. Results saved to {CSV_PATH}")
