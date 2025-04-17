# Self‑Organization of Robots – README
Interactive and batch simulation of multi‑robot waste collection in three radioactive zones.

---

## Table of Contents
1. [Project Architecture](#architecture)  
2. [Key Features](#features)  
3. [Installation](#installation)  
4. [How to Run](#running)  
   * [Interactive Dashboard (`server.py`)](#server)  
   * [Single Run CLI (`run.py`)](#run)  
   * [Batch Experiments (`multiple_simulations.py`)](#batch)  
5. [Dashboard Interface](#ui)  
6. [Experimental Results](#results)  
7. [Heuristic Explanation & Analysis](#analysis)  
8. [How the Data Were Produced](#data)

---

<a id="architecture"></a>
## 1. Project Architecture

| Layer | Files | Responsibility |
|-------|-------|----------------|
| **Model** | `model.py` | Class `RobotMission` — grid, data collection, auto‑stop when waste = 0. |
| **Agents** | `agents.py` | Robots (`Green`, `Yellow`, `Red`) implementing four heuristics: `astar`, `closest`, `random`, `min_total_distance`. |
| **Passive Objects** | `objects.py` | Waste, radioactivity, walls, disposal point. |
| **Web UI** | `server.py` | Solara dashboard with animated grid and dual‑axis performance chart. |
| **CLI Runners** | `run.py`, `multiple_simulations.py` | Single run; automated parameter sweep with 10 repetitions. |
| **Data** | `batch_results/*.csv` | Output of batch experiments for analysis. |

---

<a id="features"></a>
## 2. Key Features

* **Three radioactive zones** (`z1 → z3`).
* **Waste conversion chain**  
  * 2 green → 1 yellow (green robot)  
  * 2 yellow → 1 red (yellow robot)
* **Conditional walls**: placed only when the selected heuristic is `astar`.
* **Automatic completion**: simulation halts when the grid is waste‑free.
* **Interactive dashboard**: parameter sliders, heuristic selector, live grid, dual‑axis metrics.
* **Batch runner**: 10 independent repetitions per scenario, averages written to CSV.

---

<a id="comm"></a>
## 3. Communication & Coordination

| Mechanism & Location | Purpose | Design Rationale |
|----------------------|---------|------------------|
| **Local perception** (`BaseRobot.perceive()`) | Robots sense the eight neighbouring cells every step. | Keeps agents fully decentralised and scalable; no broadcasting needed. |
| **Task pools** (`model.unassigned_*_wastes` sets) | Global queues of yet‑to‑be‑collected waste for each colour. | `set` gives *O(1)* membership tests; simple ownership semantics. |
| **Locks** (`model.*_lock`) | Guarantee exclusive access when popping from task pools. | Prevents race conditions caused by UI callbacks with minimal overhead. |
| **Assignment lists** (`robot.assigned_wastes`) | Each robot stores the wastes it owns. | Avoids duplicate work; clarifies responsibility. |
| **Progress counters** (`model.waste_delivered_count`, `DataCollector`) | Central collection of performance metrics. | Single source of truth for the dashboard and batch scripts. |
| **UI invalidation** (`update_counter` in `server.py`) | Triggers Solara re‑render each step. | Clean separation between simulation core and visual layer. |

> **Design choice:** We adopted a **stigmergic** communication style—robots interact **only via the environment** and small shared sets protected by locks. This mirrors biological swarms, reduces code complexity, and scales to many agents without message overhead.

---

<a id="installation"></a>
## 4. Installation

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install mesa solara matplotlib numpy
---
```
<a id="running"></a>
## 5. How to Run

<a id="server"></a>
### 5.1 Interactive Dashboard

```bash
solara run server.py
```
Open the provided URL (e.g. `http://localhost:8765`).  
Choose a heuristic, adjust parameters, and click **Run ▶**. The simulation stops automatically when all waste is disposed.

<a id="run"></a>
### 5.2 Single Command‑Line Run

```bash
python run.py
```
Runs one simulation with parameters defined in `run.py`.

<a id="batch"></a>
### 5.3 Batch Experiments

```bash
python multiple_simulations.py
```
Parameter grid: heuristics (`closest`, `random`, `min_total_distance`) × robots (1/2/4 per color) × waste (4/8/16 per color).  
Each combination is executed **10 times**; averages are written to `batch_results/results_<timestamp>.csv`.

---

<a id="ui"></a>
## 6. Dashboard Interface

| Area | Description |
|------|-------------|
| **Controls** | *Play Interval* (ms), *Render Interval* (steps), **Reset/Play/Step** buttons. |
| **Model Parameters** | Sliders for robot counts and initial waste, plus heuristic selector. Changing any control restarts the simulation. |
| **Grid Panel** | Colored background (green, yellow, pink). Icons for robots, waste, disposal bomb; gray walls visible only with A*. |
| **Performance Chart** | Red line = total distance (left y‑axis). Blue line = delivered waste (right y‑axis, integer ticks, starts at 0). |

![Robot Cleanup Dashboard](https://github.com/user-attachments/assets/f6810309-be3f-4481-968e-025ff7c117b2)

---

<a id="results"></a>
## 7. Experimental Results  
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

<a id="analysis"></a>
## 8. Heuristic Explanation & Analysis

| Heuristic | Principle | Avg. Steps | Avg. Distance | Verdict |
|-----------|-----------|-----------|---------------|---------|
| **closest** | Target the nearest eligible waste. | **229.9** | **433.0** | Best overall. |
| **min_total_distance** | Minimize *(robot→waste + waste→goal)* distance. | 230.9 | 439.3 | Very close second. |
| **random** | Choose a random eligible waste. | 239.8 | 484.2 | Worst performer. |

> **Conclusion:** The simple *closest* heuristic is marginally—but consistently—the most efficient in both speed and distance. The more elaborate *min total distance* offers no significant advantage, while *random* predictably wastes motion.

---

<a id="data"></a>
## 9. How the Data Were Produced

`multiple_simulations.py` sweeps `heuristic × robots(1/2/4) × waste(4/8/16)`.

1. Runs **10 independent simulations** per combination (`MAX_STEPS = 1000`).  
2. Records `step_count` and total distance travelled.  
3. Averages these metrics across the 10 runs.  
4. Writes one line per combination to a timestamped CSV in `batch_results/`.  

The table in section 6 comes directly from that CSV, omitting the `delivered_waste` column.
