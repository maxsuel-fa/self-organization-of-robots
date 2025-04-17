# Self‑Organization of Robots – README
Interactive and batch simulation of multi‑robot waste collection in three radioactive zones.

---

## Table of Contents
1. [Project Architecture](#architecture)  
2. [Key Features](#features)  
3. [Installation](#installation)  
4. [How to Run](#running)  
   · [Interactive Dashboard (`server.py`)](#server)  
   · [Single Run CLI (`run.py`)](#run)  
   · [Batch Experiments (`multiple_simulations.py`)](#batch)  
5. [Experimental Results](#results)  
6. [How the Data Were Produced](#data)

---

<a id="architecture"></a>
## 1. Project Architecture

| Layer | Files | Responsibility |
|-------|-------|----------------|
| **Model** | `model.py` | Class `RobotMission` — grid (`MultiGrid`), data collection, stop‑condition (`finished`, `running`). |
| **Agents** | `agents.py` | Three robot types (`Green`, `Yellow`, `Red`), each using one of four target‑selection heuristics: `astar`, `closest`, `random`, `min_total_distance`. |
| **Passive Objects** | `objects.py` | Waste, radioactivity, walls, disposal point. |
| **Web UI** | `server.py` | Solara dashboard: colored grid, PNG/SVG icons, dual‑axis performance plot, sliders & heuristic selector. |
| **CLI Runners** | `run.py`, `multiple_simulations.py` | Single run until waste‑free; and automated parameter sweep. |
| **Data** | `batch_results/*.csv` | Output of the batch script, ready for plotting or further analysis. |

---

<a id="features"></a>
## 2. Key Features

* **Three zones** (`z1 → z3`) with increasing radioactivity.
* **Waste conversion**  
  · 2 green → 1 yellow (done by green robot)  
  · 2 yellow → 1 red (done by yellow robot)
* **Conditional walls**: built only when `astar` is the selected heuristic.
* **Auto stop**: simulation ends automatically when no `WasteAgent` remains.
* **Interactive dashboard**:  
  · Animated grid with icons  
  · Control panel (dimensions, robots, waste, heuristic)  
  · Performance graph with left axis = total distance, right axis = delivered waste.
* **Batch runner**: 10 independent repetitions per scenario, averages written to CSV.

---

<a id="installation"></a>
## 3. Installation

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install mesa solara matplotlib numpy
```

---

<a id="running"></a>
## 4. How to Run

<a id="server"></a>
### 4.1 Interactive Dashboard

```bash
solara run server.py
```
Open the URL shown in the terminal (e.g. `http://localhost:8765`).  
Pick a heuristic, adjust sliders, hit **Run ▶**. The loop stops once all waste is disposed.

<a id="run"></a>
### 4.2 Single Command‑Line Run

```bash
python run.py
```
Runs one simulation with the parameters hard‑coded inside `run.py`, printing step‑by‑step logs until the grid is waste‑free.

<a id="batch"></a>
### 4.3 Batch Experiments

```bash
python multiple_simulations.py
```

* Parameter grid:  
  * Heuristics = `closest`, `random`, `min_total_distance`  
  * Robots per color = 1 / 2 / 4  
  * Waste per color  = 4 / 8 / 16  
* Each scenario is executed **10 times**; metrics are averaged.  
* Output CSV is saved to `batch_results/results_<timestamp>.csv`.

---

<a id="results"></a>
## 5. Experimental Results  
*Averages of 10 runs per scenario (column **`delivered_waste`** omitted).*

| Heuristic | Robots/Color | Waste/Color | Avg. Steps | Avg. Distance |
|-----------|--------------|-------------|------------|---------------|
| closest | 1 | 4 | 162.45 | 189.22 |
| closest | 1 | 8 | 340.35 | 386.38 |
| closest | 1 | 16 | 680.13 | 750.88 |
| closest | 2 | 4 | 74.78 | 173.51 |
| closest | 2 | 8 | 165.94 | 371.93 |
| closest | 2 | 16 | 335.45 | 743.91 |
| closest | 4 | 4 | 53.34 | 172.21 |
| closest | 4 | 8 | 84.20 | 361.77 |
| closest | 4 | 16 | 172.55 | 747.28 |
| random | 1 | 4 | 171.05 | 204.94 |
| random | 1 | 8 | 350.24 | 422.01 |
| random | 1 | 16 | 694.00 | 836.58 |
| random | 2 | 4 | 80.73 | 192.46 |
| random | 2 | 8 | 175.24 | 411.38 |
| random | 2 | 16 | 359.74 | 854.60 |
| random | 4 | 4 | 57.06 | 190.52 |
| random | 4 | 8 | 90.35 | 404.71 |
| random | 4 | 16 | 179.79 | 840.55 |
| min_total_distance | 1 | 4 | 159.08 | 188.86 |
| min_total_distance | 1 | 8 | 336.29 | 380.16 |
| min_total_distance | 1 | 16 | 677.87 | 752.00 |
| min_total_distance | 2 | 4 | 82.93 | 191.50 |
| min_total_distance | 2 | 8 | 169.65 | 378.91 |
| min_total_distance | 2 | 16 | 338.25 | 749.07 |
| min_total_distance | 4 | 4 | 53.40 | 181.77 |
| min_total_distance | 4 | 8 | 89.79 | 387.38 |
| min_total_distance | 4 | 16 | 170.84 | 744.08 |

---

<a id="data"></a>
## 6. How the Data Were Produced

`multiple_simulations.py` loops over every combination of  
`heuristic × robots × waste`.  
For each combination:

1. **Runs** 10 independent simulations (cap = `MAX_STEPS = 1000`).  
2. **Measures** per run:  
   * `step_count` — steps until grid is waste‑free.  
   * Total distance travelled — sum of `distance_traveled` for all robots.  
3. **Averages** these two metrics across the 10 runs.  
4. **Writes** one CSV row with parameters + averaged metrics.  

The table above is a direct copy of that CSV (ignoring the `delivered_waste` column, as requested).
