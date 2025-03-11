"""
File: server.py
Group: 5 
Date of creation: 25/03/2024
Brief: Implements the server and comunication
Authors: Mateus Goto, Maxsuel Fernandes, João Pedro Regazzi
"""

# server.py
from mesa.visualization import SolaraViz, make_plot_component, make_space_component
from model import RobotMission

def portrayal_method(agent):
    # Define portrayals for different agents
    if hasattr(agent, 'waste_type'):
        # Waste agents portrayal
        if agent.waste_type == 'green':
            return {"Shape": "circle", "Color": "green", "r": 0.3}
        elif agent.waste_type == 'yellow':
            return {"Shape": "circle", "Color": "yellow", "r": 0.3}
        elif agent.waste_type == 'red':
            return {"Shape": "circle", "Color": "red", "r": 0.3}
    elif getattr(agent, "knowledge", None) is not None:
        # Robot agents portrayal
        if agent.__class__.__name__ == "GreenRobotAgent":
            return {"Shape": "circle", "Color": "lightgreen", "r": 0.5}
        elif agent.__class__.__name__ == "YellowRobotAgent":
            return {"Shape": "circle", "Color": "orange", "r": 0.5}
        elif agent.__class__.__name__ == "RedRobotAgent":
            return {"Shape": "circle", "Color": "darkred", "r": 0.5}
    elif hasattr(agent, "radioactivity"):
        # Radioactivity agents portrayal; using a grayscale based on value
        shade = int(255 * (1 - agent.radioactivity))
        return {"Shape": "circle", "Color": f"rgb({shade}, {shade}, {shade})", "r": 0.1}
    # Waste disposal or other agents can have a default portrayal
    return {}

# Create a space visualization component.
space_component = make_space_component(
    canvas_width=600,
    canvas_height=600,
    grid_width=30,
    grid_height=30,
    portrayal_method=portrayal_method
)

# Create a simple plot component. For example, plotting the total number of waste agents.
def get_waste_count(model):
    waste_count = sum(1 for agent in model.schedule.agents if hasattr(agent, "waste_type"))
    return {"Waste Count": waste_count}

plot_component = make_plot_component(
    get_waste_count,
    canvas_width=600,
    canvas_height=200
)

viz = SolaraViz(
    model=RobotMission,
    model_params={"width": 30, "height": 30, "num_green": 5, "num_yellow": 3, "num_red": 2, "num_waste": 10},
    visualization_components=[space_component, plot_component],
    title="Robot Mission Simulation"
)

if __name__ == '__main__':
    viz.launch()
