"""
File: server.py
Group: 5 
Date of creation: 25/03/2024
Brief: Implements the server and communication
Authors: Mateus Goto, Maxsuel Fernandes, João Pedro Regazzi
"""

import mesa
import solara
from matplotlib.figure import Figure
from mesa.visualization import SolaraViz, make_plot_component, make_space_component
from mesa.visualization.utils import update_counter
from model import RobotMission

def agent_portrayal(agent):
    # Define visual properties based on agent type.
    if hasattr(agent, 'waste_type'):
        if agent.waste_type == "green":
            return {"Shape": "circle", "Color": "green", "r": 0.3}
        elif agent.waste_type == "yellow":
            return {"Shape": "circle", "Color": "yellow", "r": 0.3}
        elif agent.waste_type == "red":
            return {"Shape": "circle", "Color": "red", "r": 0.3}
    elif hasattr(agent, "knowledge"):
        if agent.__class__.__name__ == "GreenRobotAgent":
            return {"Shape": "circle", "Color": "lightgreen", "r": 0.5}
        elif agent.__class__.__name__ == "YellowRobotAgent":
            return {"Shape": "circle", "Color": "orange", "r": 0.5}
        elif agent.__class__.__name__ == "RedRobotAgent":
            return {"Shape": "circle", "Color": "darkred", "r": 0.5}
    elif hasattr(agent, "radioactivity"):
        shade = int(255 * (1 - agent.radioactivity))
        return {"Shape": "circle", "Color": f"rgb({shade}, {shade}, {shade})", "r": 0.1}
    else:
        return {"Shape": "rect", "Color": "black", "w": 1, "h": 1}

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

# Create a space visualization component.
SpaceGraph = make_space_component(
    agent_portrayal,
)

# Create a plot component for waste count.
def get_waste_count(model):
    waste_count = sum(1 for agent in model.custom_agents if hasattr(agent, "waste_type"))
    return {"Waste Count": waste_count}

WastePlot = make_plot_component(get_waste_count)

# Create an instance of the model using defaults from model_params.
model_instance = RobotMission(
    width=model_params["width"],
    height=model_params["height"],
    num_green=model_params["num_green"]["value"],
    num_yellow=model_params["num_yellow"]["value"],
    num_red=model_params["num_red"]["value"],
    num_waste=model_params["num_waste"]["value"]
)

page = SolaraViz(
    model=model_instance,
    components=[SpaceGraph, WastePlot, WasteCountHistogram],
    model_params=model_params,
    name="Self-Organization of Robots"
)
