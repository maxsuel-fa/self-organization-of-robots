"""
File: model.py
Group: 5 
Date of creation: 25/03/2024
Brief: Implements the model 
Authors: Mateus Goto, Maxsuel Fernandes, João Pedro Regazzi
"""

from mesa import Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from agents import GreenRobotAgent, YellowRobotAgent, RedRobotAgent
from objects import RadioactivityAgent, WasteAgent, WasteDisposalAgent, wallAgent
import random
import threading

class RobotMission(Model):
    def __init__(self, width=30, height=30, num_green=5, num_yellow=3, num_red=2, num_waste=10):
        super().__init__()
        self.width = width
        self.height = height
        self.grid = MultiGrid(width, height, torus=False)
        
        self.custom_agents = []
        # Initialize counters for performance metrics.
        self.waste_delivered_count = 0
        self.step_count = 0

        self.datacollector = DataCollector(
            model_reporters={
                "WasteCount": lambda m: sum(1 for agent in m.custom_agents if hasattr(agent, "waste_type")),
                "StepCount": lambda m: m.step_count,
                "DeliveredWaste": lambda m: m.waste_delivered_count,
                "TotalDistance": lambda m: sum(getattr(agent, "distance_traveled", 0)
                                              for agent in m.custom_agents if hasattr(agent, "distance_traveled")),
                "TimeToZeroWaste": lambda m: m.step_count if sum(1 for agent in m.custom_agents if hasattr(agent, "waste_type")) == 0 else None,
            }
        )
        
        # Initialize unassigned waste sets and locks.
        self.unassigned_green_wastes = set()
        self.unassigned_yellow_wastes = set()
        self.unassigned_red_wastes = set()
        self.green_lock = threading.Lock()
        self.yellow_lock = threading.Lock()
        self.red_lock = threading.Lock()
        
        # Place a RadioactivityAgent on each cell.
        for x in range(width):
            for y in range(height):
                radio = RadioactivityAgent(self, (x, y))
                self.grid.place_agent(radio, (x, y))
                self.custom_agents.append(radio)
        
        # Place the WasteDisposalAgent in a random cell on the easternmost column.
        eastern_x = width - 1
        disposal_y = random.randrange(height)
        self.waste_disposal = WasteDisposalAgent(self, (eastern_x, disposal_y))

        # Define gate positions.
        gate_y_positions = [5, 4, 3, 15, 14, 13, 25, 24, 23]

        # Add vertical wall between z1 and z2.
        wall_x1 = self.width // 3
        for y in range(self.height):
            if y not in gate_y_positions:
                wall = wallAgent(self, (wall_x1, y))
                self.grid.place_agent(wall, (wall_x1, y))
                self.custom_agents.append(wall)

        # Add vertical wall between z2 and z3.
        wall_x2 = 2 * self.width // 3
        for y in range(self.height):
            if y not in gate_y_positions:
                wall = wallAgent(self, (wall_x2, y))
                self.grid.place_agent(wall, (wall_x2, y))
                self.custom_agents.append(wall)
                self.grid.place_agent(self.waste_disposal, (eastern_x, disposal_y))
                self.custom_agents.append(self.waste_disposal)
        
        # Add WasteAgent (green waste initially placed in zone z1).
        for _ in range(num_waste):
            x = random.randrange(0, width // 3)
            y = random.randrange(height)
            waste = WasteAgent(self, 'green', (x, y))
            self.grid.place_agent(waste, (x, y))
            self.custom_agents.append(waste)
            with self.green_lock:
                self.unassigned_green_wastes.add(waste)
        
        # Create and place robot agents.
        for _ in range(num_green):
            x = random.randrange(0, width // 3)
            y = random.randrange(height)
            agent = GreenRobotAgent(self, heuristic="astar")
            self.grid.place_agent(agent, (x, y))
            self.custom_agents.append(agent)
        
        for _ in range(num_yellow):
            x = random.randrange(0, 2 * (width // 3))
            y = random.randrange(height)
            agent = YellowRobotAgent(self, heuristic="astar")
            self.grid.place_agent(agent, (x, y))
            self.custom_agents.append(agent)
        
        for _ in range(num_red):
            x = random.randrange(width)
            y = random.randrange(height)
            agent = RedRobotAgent(self, heuristic="astar")
            self.grid.place_agent(agent, (x, y))
            self.custom_agents.append(agent)

        print(f"[INIT] RobotMission initialized with grid {width}x{height} and {len(self.custom_agents)} agents.")
        print()

    def get_zone(self, pos):
        x, y = pos
        if x < self.width / 3:
            return 'z1'
        elif x < 2 * self.width / 3:
            return 'z2'
        else:
            return 'z3'
    
    def step(self):
        self.step_count += 1
        print(f"\n=== Step {self.step_count} start ===")
        waste_count = sum(1 for agent in self.custom_agents if hasattr(agent, "waste_type"))
        print(f"[MODEL] Waste Count: {waste_count}")
        for agent in self.custom_agents:
            # Debug prints for dynamic agents.
            from objects import WasteAgent, RadioactivityAgent, WasteDisposalAgent
            if not isinstance(agent, (WasteAgent, RadioactivityAgent, WasteDisposalAgent)):
                print(f"[MODEL] Stepping agent {agent} at position {agent.pos}")
            agent.step()
        print(f"=== Step {self.step_count} complete ===")
        self.datacollector.collect(self)
        
        # Add these lines to print the current dataframe from the DataCollector:
        df = self.datacollector.get_model_vars_dataframe()
        print("DataCollector contents after this step:")
        print("DataCollector contents after this step:")
        print("DataCollector contents after this step:")
        print(df)
