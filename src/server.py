"""
File: server.py
Group: 5 
Date of creation: 25/03/2024
Brief: Implements the server and communication with custom icon rendering, optimized grid update, and enlarged cell display
Authors: Mateus Goto, Maxsuel Fernandes, João Pedro Regazzi
"""

from mesa.visualization import SolaraViz
import solara
import matplotlib.image as mpimg
from matplotlib.figure import Figure
from matplotlib import colors as mcolors, pyplot as plt
from mesa.visualization.utils import update_counter
import numpy as np

# Import the model and agent classes
from model import RobotMission
from agents import GreenRobotAgent, YellowRobotAgent, RedRobotAgent
from objects import WasteAgent, WasteDisposalAgent, RadioactivityAgent, wallAgent

# === Icon image file paths ===
GREEN_ROBOT_ICON   = "image/botzgreen1.png"    # Green robot icon image
YELLOW_ROBOT_ICON  = "image/botzorange1.png"   # Yellow robot icon image
RED_ROBOT_ICON     = "image/botzred1.png"      # Red robot icon image
GREEN_WASTE_ICON   = "image/green_waste.png"   # Green waste icon image
YELLOW_WASTE_ICON  = "image/yellow_waste.png"  # Yellow waste icon image
RED_WASTE_ICON     = "image/red_waste.png"     # Red waste icon image
DISPOSAL_ICON      = "image/bomb4.png"         # Waste disposal unit icon image

# Define subtle zone colors for background:
# Zone 1: lightgreen, Zone 2: lightyellow, Zone 3: mistyrose (fading pink)
ZONE_COLORS = {"z1": "lightgreen", "z2": "lightyellow", "z3": "mistyrose", "wall" : "gray"}

# Define a scaling factor for cell size.
CELL_SIZE = 20  # Increase this value for larger cells.

# Global caches for images and background image
image_cache = {}
background_image = None

def get_image(image_path):
    """
    Returns a cached image if available; otherwise, loads and caches it.
    """
    if image_path in image_cache:
        return image_cache[image_path]
    try:
        img = mpimg.imread(image_path)
        image_cache[image_path] = img
        return img
    except Exception as e:
        print("Error loading image:", image_path, e)
        return None

def create_background_image(width, height, wall_positions):
    """
    Creates a NumPy array of shape (height, width, 3) representing the static background.
    Each column gets its color based on its zone.
    """
    img = np.zeros((height, width, 3))
    for x in range(width):
        if x < width / 3:
            zone = "z1"
        elif x < 2 * width / 3:
            zone = "z2"
        else:
            zone = "z3"
        rgb = mcolors.to_rgb(ZONE_COLORS[zone])
        img[:, x, :] = rgb

    """ for x, y in wall_positions:
        if 0 <= x < width and 0 <= y < height:
            img[y, x] = (0, 0, 0) """
    return img

def agent_portrayal(agent):
    """
    Return a portrayal dictionary for each dynamic agent.
    RadioactivityAgents are rendered in the static background.
    """
    if isinstance(agent, RadioactivityAgent):
        return None  # Skip dynamic drawing for background agents.
    if isinstance(agent, GreenRobotAgent):
        return {"shape": GREEN_ROBOT_ICON, "size": 50, "zorder": 1}
    if isinstance(agent, YellowRobotAgent):
        return {"shape": YELLOW_ROBOT_ICON, "size": 50, "zorder": 1}
    if isinstance(agent, RedRobotAgent):
        return {"shape": RED_ROBOT_ICON, "size": 50, "zorder": 1}
    if isinstance(agent, WasteAgent):
        if agent.waste_type == 'green':
            return {"shape": GREEN_WASTE_ICON, "size": 40, "zorder": 2}
        elif agent.waste_type == 'yellow':
            return {"shape": YELLOW_WASTE_ICON, "size": 40, "zorder": 2}
        elif agent.waste_type == 'red':
            return {"shape": RED_WASTE_ICON, "size": 40, "zorder": 2}
    if isinstance(agent, WasteDisposalAgent):
        return {"shape": DISPOSAL_ICON, "size": 50, "zorder": 3}
    """ if isinstance(agent, wallAgent):
        return """
    return {"marker": "o", "color": "gray", "size": 100, "zorder": 1}

def draw_agent(ax, portrayal, pos):
    """
    Draws an agent on the axes (ax) at grid position (pos) using its portrayal.
    Uses the cached image if a 'shape' key is provided.
    The drawing extent is scaled by CELL_SIZE.
    """
    if portrayal is None:
        return
    if "shape" in portrayal:
        img = get_image(portrayal["shape"])
        if img is not None:
            extent = [pos[0] * CELL_SIZE, (pos[0] + 1) * CELL_SIZE,
                      pos[1] * CELL_SIZE, (pos[1] + 1) * CELL_SIZE]
            ax.imshow(img, extent=extent, zorder=portrayal.get("zorder", 1))
    else:
        # If not an image, use scatter.
        ax.scatter(pos[0] * CELL_SIZE + CELL_SIZE/2, pos[1] * CELL_SIZE + CELL_SIZE/2,
                   s=portrayal.get("size", 20),
                   c=portrayal.get("color", "gray"),
                   marker=portrayal.get("marker", "o"),
                   zorder=portrayal.get("zorder", 1))

def post_process(ax, width, height):
    """
    Adjust the Matplotlib axes for equal scaling, clear appearance, and proper limits.
    """
    ax.set_aspect("equal", "box")
    ax.set_xlim(0, width * CELL_SIZE)
    ax.set_ylim(0, height * CELL_SIZE)
    ax.set_xticks([])
    ax.set_yticks([])

@solara.component
def CustomGrid(model):
    """
    Custom grid component that renders a static background and overlays dynamic agents.
    The update_counter triggers a re-render on each model update.
    """
    update_counter.get()  # Trigger re-render on model update.
    fig = Figure(figsize=(12, 12))
    ax = fig.subplots()

    global background_image
    wall_positions = {
        agent.initial_pos for agent in model.custom_agents
        if isinstance(agent, wallAgent)
    }
    # Create or update the background image if grid dimensions change.
    if background_image is None or background_image.shape[1] != model.width or background_image.shape[0] != model.height:
        background_image = create_background_image(model.width, model.height, wall_positions)
    
    # Draw the static background scaled by CELL_SIZE.
    ax.imshow(background_image, extent=[0, model.width * CELL_SIZE, 0, model.height * CELL_SIZE],
              zorder=0, interpolation='nearest')
    ax.grid(True, which='major', color='gray', linewidth=0.5)
    
    # Draw dynamic agents (skip RadioactivityAgents as they are part of the background).
    for x in range(model.width):
        for y in range(model.height):
            cell_agents = model.grid.get_cell_list_contents((x, y))
            for agent in cell_agents:
                portrayal = agent_portrayal(agent)
                if portrayal is not None:
                    draw_agent(ax, portrayal, (x, y))
    
    post_process(ax, model.width, model.height)
    return solara.FigureMatplotlib(fig)
@solara.component
def PerformanceGraph(model):
    from matplotlib.ticker import MaxNLocator       # ⬅️ for integer ticks
    update_counter.get()

    df = model.datacollector.get_model_vars_dataframe()
    if df.empty:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, "No data collected yet",
                ha="center", va="center", fontsize=16)
        ax.set_xticks([]); ax.set_yticks([])
        return solara.FigureMatplotlib(fig)

    # ── data ────────────────────────────────────────────────────────────────
    steps           = df["StepCount"].tolist()
    waste_delivered = df["DeliveredWaste"].tolist()
    total_distance  = df["TotalDistance"].tolist()

    # ── dual‑axis figure ────────────────────────────────────────────────────
    fig, ax_left = plt.subplots(figsize=(8, 6))

    # Left axis – total distance (red)
    ax_left.set_xlabel("Simulation Steps")
    ax_left.set_ylabel("Total Distance Traveled", color="tab:red")
    ln1 = ax_left.plot(steps, total_distance,
                       label="Total Distance Traveled",
                       color="tab:red")
    ax_left.tick_params(axis='y', labelcolor="tab:red")

    # Right axis – delivered waste (blue), integer scale 0 … max(5, current max)
    ax_right = ax_left.twinx()
    ax_right.set_ylabel("Delivered Waste", color="tab:blue")
    ln2 = ax_right.plot(steps, waste_delivered,
                        label="Delivered Waste",
                        color="tab:blue")
    ax_right.tick_params(axis='y', labelcolor="tab:blue")

    # integer, positive ticks starting at 0
    ymax = max(max(waste_delivered, default=0)+1, 5)
    ax_right.set_ylim(0, ymax)
    ax_right.yaxis.set_major_locator(MaxNLocator(integer=True))

    # Combined legend
    lines  = ln1 + ln2
    labels = [l.get_label() for l in lines]
    ax_left.legend(lines, labels, loc="upper left")

    fig.tight_layout()
    return solara.FigureMatplotlib(fig)

@solara.component
def GameStatus(model):
    update_counter.get()                     # redraw each tick
    if model.status == "running":
        return solara.Markdown("")           # show nothing
    if model.status == "win":
        return solara.Markdown("## 🎉 **YOU WIN!**")
    if model.status == "gameover":
        return solara.Markdown("## 💀 **GAME OVER**")

# Define interactive model parameters for the dashboard controls
model_params = {
    "num_green": {
        "type": "SliderInt", "value": 2, "min": 0, "max": 20, "step": 1,
        "label": "Number of Green Robots:"
    },
    "num_yellow": {
        "type": "SliderInt", "value": 1, "min": 0, "max": 20, "step": 1,
        "label": "Number of Yellow Robots:"
    },
    "num_red": {
        "type": "SliderInt", "value": 1, "min": 0, "max": 20, "step": 1,
        "label": "Number of Red Robots:"
    },
    "num_green_waste": {
        "type": "SliderInt", "value": 2, "min": 0, "max": 50, "step": 1,
        "label": "Initial Green Waste:"
    },
    "num_yellow_waste": {
        "type": "SliderInt", "value": 1, "min": 0, "max": 50, "step": 1,
        "label": "Initial Yellow Waste:"
    },
    "num_red_waste": {
        "type": "SliderInt", "value": 0, "min": 0, "max": 50, "step": 1,
        "label": "Initial Red Waste:"
    },
    "width": {
        "type": "SliderInt", "value": 30, "min": 0, "max": 100, "step": 1,
        "label": "width:"
    },
    "height": {
        "type": "SliderInt", "value": 30, "min": 0, "max": 100, "step": 1,
        "label": "height:"
    },
    "heuristic": {
        "type": "Select",
        "value": "closest",
        "values": [
            "closest",
            "farthest",
            "min_total_distance",
        ],
        "label": "Path‑finding heuristic:",
},
}


# Heuristic options:
# "astar", "closest", "random", "min_total_distance"

# Instantiate the model with initial parameters
initial_model = RobotMission(
    width             = model_params["width"]["value"],
    height            = model_params["height"]["value"],
    num_green         = model_params["num_green"]["value"],
    num_yellow        = model_params["num_yellow"]["value"],
    num_red           = model_params["num_red"]["value"],
    num_green_waste   = model_params["num_green_waste"]["value"],
    num_yellow_waste  = model_params["num_yellow_waste"]["value"],
    num_red_waste     = model_params["num_red_waste"]["value"],
    heuristic         = model_params["heuristic"]["value"],
)



# Create the SolaraViz page with the custom grid component and interactive controls
page = SolaraViz(
    initial_model,
    components=[CustomGrid, PerformanceGraph, GameStatus],
    model_params=model_params,
    name="Robot Cleanup Mission Dashboard"
)
page  # Render the dashboard
