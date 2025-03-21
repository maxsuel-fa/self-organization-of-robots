"""
File: server.py
Group: 5 
Date of creation: 25/03/2024
Brief: Implements the server and communication
Authors: Mateus Goto, Maxsuel Fernandes, João Pedro Regazzi
"""

from matplotlib import pyplot as plt
import mesa
import solara
from matplotlib.figure import Figure
from mesa.visualization import SolaraViz, make_plot_component, make_space_component
from mesa.visualization.utils import update_counter
from model import RobotMission
from agents import RedRobotAgent, GreenRobotAgent, YellowRobotAgent
from objects import RadioactivityAgent, WasteAgent, WasteDisposalAgent

def agent_portrayal(agent):
    agent_type = agent.__class__.__name__

    if agent_type == "RadioactivityAgent":
        # Use the model's zone method to determine the background color.
        zone = agent.model.get_zone(agent.pos)
        zone_color_map = {
            "z1": "#d0f0fd",  # light blue
            "z2": "#d0fbd0",  # light green
            "z3": "#fdd0d0"   # light red/pink
        }
        color = zone_color_map.get(zone, "white")
        # Return a rectangle that fills the cell as the background.
        return {"shape": "rect", "color": color, "w": 1, "h": 1, "layer": 0}

    elif agent_type == "WasteDisposalAgent":
        # Display as a blue square on top of the background.
        return {"shape": "rect", "color": "blue", "w": 1, "h": 1, "layer": 2}

    elif agent_type == "WasteAgent":
        color_map = {"green": "green", "yellow": "yellow", "red": "red"}
        color = color_map.get(getattr(agent, "waste_type", "green"), "green")
        return {"shape": "circle", "color": color, "r": 0.3, "layer": 3}

    elif agent_type in ["GreenRobotAgent", "YellowRobotAgent", "RedRobotAgent"]:
        color_map = {
            "GreenRobotAgent": "lightgreen",
            "YellowRobotAgent": "orange",
            "RedRobotAgent": "darkred"
        }
        color = color_map.get(agent_type, "gray")
        return {"shape": "circle", "color": color, "r": 0.5, "layer": 4}

    else:
        # Fallback portrayal for any agent that is not explicitly handled.
        return {"shape": "rect", "color": "black", "w": 1, "h": 1, "layer": 0}
# Create a space visualization component using the updated agent_portrayal.
SpaceGraph = make_space_component(agent_portrayal)

def get_waste_count(model):
    waste_count = sum(1 for agent in model.custom_agents if hasattr(agent, "waste_type"))
    return {"Waste Count": waste_count}

WastePlot = make_plot_component(get_waste_count)

# Define interactive model parameters.
model_params = {
    "width": 30,
    "height": 30,
    "num_green": {
        "type": "SliderInt",
        "value": 5,
        "label": "Number of Green Robots:",
        "min": 1,
        "max": 10,
        "step": 1,
    },
    "num_yellow": {
        "type": "SliderInt",
        "value": 3,
        "label": "Number of Yellow Robots:",
        "min": 1,
        "max": 10,
        "step": 1,
    },
    "num_red": {
        "type": "SliderInt",
        "value": 2,
        "label": "Number of Red Robots:",
        "min": 1,
        "max": 10,
        "step": 1,
    },
    "num_waste": {
        "type": "SliderInt",
        "value": 10,
        "label": "Number of Waste Items:",
        "min": 0,
        "max": 20,
        "step": 1,
    }
}

@solara.component
def WasteCountHistogram(model: RobotMission):
    update_counter.get()  # Ensures thread-safe updates.
    fig = Figure()
    ax = fig.subplots()
    df = model.datacollector.get_model_vars_dataframe()
    if not df.empty:
        last_value = df["WasteCount"].iloc[-1]
        ax.bar(["Waste Count"], [last_value])
    else:
        ax.bar(["Waste Count"], [0])
    return solara.FigureMatplotlib(fig)

# Create an instance of the model using the defined parameters.
model_instance = RobotMission(
    width=model_params["width"],
    height=model_params["height"],
    num_green=model_params["num_green"]["value"],
    num_yellow=model_params["num_yellow"]["value"],
    num_red=model_params["num_red"]["value"],
    num_waste=model_params["num_waste"]["value"]
)

# Combine the components into the SolaraViz page.
page = SolaraViz(
    model=model_instance,
    components=[SpaceGraph, WastePlot, WasteCountHistogram],
    model_params=model_params,
    name="Self-Organization of Robots"
)