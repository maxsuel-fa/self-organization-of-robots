# Self‑Organization of Robots – README
Interactive and batch simulation of multi‑robot waste collection in three radioactive zones.

---

## Table of Contents
1. [Project Architecture](#architecture)  
2. [Key Features](#features)  
3. [Installation](#installation)
4. [Local Perception and Vision System](#vision)  
5. [Installation](#installation)  
6. [How to Run](#running)  
   * [Interactive Dashboard (`server.py`)](#server)  
   * [Single Run CLI (`run.py`)](#run)  
   * [Batch Experiments (`multiple_simulations.py`)](#batch)  
7. [Dashboard Interface](#ui)  
8. [Experimental Results](#results)  
9. [Heuristic Explanation & Analysis](#analysis)  
10. [How the Data Were Produced](#data)  
11. [Visualization of Batch Results](#plots)  

---

<a id="architecture"></a>
## 1. Project Architecture

| Layer | Files | Responsibility |
|-------|-------|----------------|
| **Model** | `model.py` | Class `RobotMission` — grid, data collection, win/game-over logic. |
| **Agents** | `agents.py` | Robots (`Green`, `Yellow`, `Red`) with decentralized task assignment, local perception and coordination via environmental messaging. |
| **Passive Objects** | `objects.py` | Waste, radioactivity, walls, disposal point. |
| **Web UI** | `server.py` | Solara dashboard with animated grid and performance graphs. |
| **CLI Runners** | `run.py`, `multiple_simulations.py` | Interactive run; automated batch experiments. |
| **Data** | `batch_results/*.csv` | Output from experiments for evaluation. |

![uml_diagram_sma](https://github.com/user-attachments/assets/8c055bd1-813c-4ffe-a41a-14e5238c5a79)

---

<a id="features"></a>
## 2. Key Features

* **Three radioactive zones** (`z1`, `z2`, `z3`), increasing in danger.
* **Multi-step waste conversion** chain:  
  * 2 green → 1 yellow (by green robots)  
  * 2 yellow → 1 red (by yellow robots)
* **Win/game-over system**: simulation halts when no more red waste can be produced.
* **Vision-constrained agents**: limited perception radius, no global map.
* **Coordination via communication**: task requests and rendezvous handled via step-tagged messages.
* **Interactive dashboard**: live visualization, configurable inputs.
* **Batch runner**: full grid search with statistical averaging over 50 repetitions per case.

---

<a id="comm"></a>
## 3. Communication & Coordination

| Mechanism & Location | Purpose | Design Rationale |
|----------------------|---------|------------------|
| **Local perception** (`BaseRobot.perceive`) | Scan 8 neighboring cells. | Decentralized control without global awareness. |
| **Seen wastes** (`model.seen_wastes`) | Track visible wastes. | Enables limited cooperation. |
| **Task queues** (`unassigned_*_wastes`) | Track wastes not yet assigned. | Ensures unique ownership of tasks. |
| **Locks** (`green/yellow/red_lock`) | Avoid race conditions. | Required for concurrent UI callbacks. |
| **Message board** (`message_board`) | Step-stamped robot communication. | Simple, scalable, environment-based. |
| **Agent state** (`assigned_wastes`, `carrying`) | Tracks each robot's workload. | Local reasoning. |

> Robots follow **stigmergic coordination** — acting based on local signals and shared environmental state. Explicit messages are rare and lightweight.

---
<a id="vision"></a>
## 4. Local Perception and Vision System

Each robot operates under strict local perception constraints. At every simulation step, an agent can only observe the **8 adjacent cells** around its current location — including diagonals. This forms a **Moore neighborhood** of radius 1.

```text
  o o o
  o R o   <- R = Robot, o = observable cell
  o o o
```

This vision system has the following properties:

- 🔍 **Limited Awareness**: Robots cannot see waste or other agents outside their immediate surroundings. This enforces decentralized behavior and mimics physical sensor range in real-world robotics.

- 🔁 **Step-Based Sensing**: Perception is updated at every time step. Robots continuously scan their local neighborhood before making any decisions.

- 👁️ **Vision for Task Assignment**:
  - When a robot detects an unclaimed waste cell (green/yellow/red), it checks if that task is already assigned using a shared `seen_wastes` and `unassigned_*_wastes` structure.
  - If free, it claims and plans its path to collect it.

- 🤝 **Stigmergy-Driven Interaction**: Since no global map is available and robots do not communicate directly, all task coordination emerges from changes in the environment (e.g., claimed waste removed from pool, message board entries updated) — a concept known as **stigmergy**.

> This vision model forces robots to behave reactively and encourages emergent collaboration, as agents must move, explore, and observe repeatedly to locate and coordinate on waste collection tasks.
<a id="installation"></a>
## 4. Installation

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install mesa solara matplotlib numpy tqdm
```

---

<a id="running"></a>
## 5. How to Run

<a id="server"></a>
### 5.1 Interactive Dashboard

```bash
solara run server.py
```
Launches a UI at the provided localhost URL. Choose a heuristic, adjust parameters, and click **Run**.

> ⚠️ **Important:** Your terminal **must be inside the `src/` folder** when launching the dashboard, or image references and assets will not load properly.

<a id="run"></a>
### 5.2 Single Command-Line Run

```bash
python run.py
```
Runs a single simulation for debugging and visualization.

<a id="batch"></a>
### 5.3 Batch Experiments

```bash
python multiple_simulations.py
```
Full sweep: heuristics (`closest`, `farthest`, `min_total_distance`) × robots (1/2/4 per color) × waste (4/8/16 per color). Each combo is repeated 50 times. Output is written to a CSV in `batch_results/`.

---

<a id="ui"></a>
## 6. Dashboard Interface

| Component | Description |
|----------|-------------|
| **Controls** | Sliders for robot/waste count, heuristic selector, execution speed. |
| **Live Grid** | Color-coded zones + agents and wastes. Icons indicate robot/waste type. |
| **Performance Graph** | Dual-axis chart: delivered waste (blue) vs total distance (red). |
| **Game Status** | Displays “YOU WIN” or “GAME OVER” when applicable. |

---

<a id="results"></a>
## 7. Experimental Results (Selected)

*Averages from 50 repetitions per configuration.*

| Heuristic | Robots/Color | Waste/Color | Avg Steps | Total Distance | Win Rate | Game Over Rate |
|-----------|--------------|-------------|-----------|----------------|----------|----------------|
| closest | 1 | 16 | 694.83 | 1611.29 | 0.68 | 0.32 |
| closest | 2 | 16 | 361.04 | 1658.82 | 0.98 | 0.02 |
| closest | 4 | 16 | 200.68 | 1894.00 | 0.98 | 0.02 |
| farthest | 1 | 16 | 700.31 | 1436.15 | 0.70 | 0.30 |
| farthest | 2 | 16 | 366.82 | 1572.56 | 1.00 | 0.00 |
| farthest | 4 | 16 | 198.40 | 1777.32 | 0.94 | 0.06 |
| min_total_distance | 1 | 16 | 707.75 | 1491.06 | 0.64 | 0.36 |
| min_total_distance | 2 | 16 | 363.88 | 1675.02 | 1.00 | 0.00 |
| min_total_distance | 4 | 16 | 204.28 | 1961.56 | 0.98 | 0.02 |

---

<a id="analysis"></a>
## 8. Heuristic Analysis

All heuristics use decentralized logic and limited visibility. Below is a summary comparison:

| Heuristic | Description | Performance Summary |
|-----------|-------------|---------------------|
| **Closest** | Select the nearest waste within field of view. | Best balance of speed and robustness. |
| **Farthest** | Select the farthest waste within vision range. | Slightly slower but with fewer conflicts. |
| **Min Total Distance** | Minimize total path (to waste + to goal). | Higher cost, but more organized behavior. |

---

<a id="data"></a>
## 9. How the Data Were Produced

Batch results come from `multiple_simulations.py`, which uses:

1. A Cartesian grid of all combinations: `heuristic × robot_count × waste_count`.
2. 50 independent repetitions per configuration.
3. Timeout-safe simulation loop with up to 2000 steps.
4. Statistics recorded: average steps, distance, delivered waste, win and game-over rates.
5. Output CSV saved in `batch_results/`.

---

<a id="plots"></a>
## 10. Visualization of Batch Results

The following plots were generated from the experimental results:

### 10.1 Win Rate vs Number of Robots (per Heuristic)
This plot confirms that the system benefits significantly from additional robots. Regardless of the heuristic used, increasing the number of agents improves the win rate dramatically. This indicates an effective division of labor and coordination strategy.

![plot_1_winrate_vs_robots](https://github.com/user-attachments/assets/3bbbd16f-50b9-4ef9-93ea-fd3663682f69)

### 10.2 Total Distance vs Number of Robots
While the total distance increases with more agents, this is expected and reflects a healthy distribution of tasks. Importantly, the growth is consistent and does not suggest wasted motion or inefficiencies — supporting the idea that the agents optimize their movement locally.

![plot_2_distance_vs_robots](https://github.com/user-attachments/assets/8261bbe5-8ec2-48c6-8f5a-e06e75583e97)

### 10.3 Steps vs Total Distance
This scatter plot shows an important system characteristic: setups with fewer robots take significantly more steps and also accumulate comparable total distance. This suggests higher redundancy and lower throughput in smaller teams. In contrast, larger teams finish quickly and tend to spread the movement across more agents — an indicator of effective self-organization.

![plot_3_steps_vs_distance](https://github.com/user-attachments/assets/1c1ee3a8-1247-4ad5-bd8b-f32abb43bc8e)

### 10.4 Average Win Rate per Heuristic
Here, we see that all three heuristics perform well (average win rates > 0.7), with minor variation. The `closest` and `min_total_distance` strategies offer slight advantages over `farthest`, but all are viable. This robustness confirms that the coordination logic generalizes across different decision models.

![plot_4_barplot_winrate](https://github.com/user-attachments/assets/c9743474-c41c-482c-bf5a-840cb2fcedad)

## 12. Future Work

Several directions remain open to extend the current system and increase realism and complexity:

### 🔧 Improved Communication Protocols
Current coordination is mostly stigmergic and based on local task ownership. A richer communication model could include:
- Message types (e.g., HELP, AVOID, PRIORITY)
- Time-to-live (TTL) for messages
- Broadcasting or relayed messaging over limited range
- Explicit signaling for rendezvous and handoff

These additions would allow for more complex strategies such as task negotiation, collaborative routing, and dynamic prioritization.

### 🔋 Robot Battery Model
Introducing energy constraints could simulate real-world limitations and force strategic trade-offs:
- Robots would deplete energy as they move or carry waste.
- Charging stations or energy regeneration zones could be added to the map.
- Task planning would then consider both distance and battery levels, increasing complexity and realism.

### 🧱 Walls and Environmental Hazards
The current environment is open, but introducing **static and dynamic obstacles** would challenge pathfinding and cooperation:
- Walls that block movement, forcing detours and congestion.
- Hazard zones (e.g., leaks, fires) that may damage or disable robots temporarily.
- Randomized terrain or time-dependent threats to increase variability.

> These extensions aim to evolve the system into a more comprehensive testbed for decentralized AI, resilience, and adaptive planning under uncertainty.

---
