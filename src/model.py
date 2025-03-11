"""
File: model.py
Group: 5 
Date of creation: 25/03/2024
Brief: Implements the model 
Authors: Mateus Goto, Maxsuel Fernandes, João Pedro Regazzi
"""

from mesa import Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from agents import GreenRobotAgent, YellowRobotAgent, RedRobotAgent
from objects import RadioactivityAgent, WasteAgent, WasteDisposalAgent
import random

class RobotMission(Model):
    # All parameters now have default values.
    def __init__(self, width=30, height=30, num_green=5, num_yellow=3, num_red=2, num_waste=10):
        super().__init__()
        self.width = width
        self.height = height
        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(width, height, torus=False)
        
        # Create a DataCollector to record waste count.
        self.datacollector = DataCollector(
            model_reporters={
                "WasteCount": lambda m: sum(1 for agent in m.schedule.agents if hasattr(agent, "waste_type"))
            }
        )
        
        # Place a RadioactivityAgent on each cell.
        for x in range(width):
            for y in range(height):
                radio = RadioactivityAgent(self, (x, y))
                self.grid.place_agent(radio, (x, y))
                self.schedule.add(radio)
        
        # Place the WasteDisposalAgent in a random cell on the easternmost column.
        eastern_x = width - 1
        disposal_y = random.randrange(height)
        self.waste_disposal = WasteDisposalAgent(self, (eastern_x, disposal_y))
        self.grid.place_agent(self.waste_disposal, (eastern_x, disposal_y))
        self.schedule.add(self.waste_disposal)
        
        # Add WasteAgent (green waste initially placed in zone z1).
        for _ in range(num_waste):
            x = random.randrange(0, width // 3)
            y = random.randrange(height)
            waste = WasteAgent(self, 'green', (x, y))
            self.grid.place_agent(waste, (x, y))
            self.schedule.add(waste)
        
        # Create and place robot agents.
        for _ in range(num_green):
            x = random.randrange(0, width // 3)
            y = random.randrange(height)
            agent = GreenRobotAgent(self)
            self.grid.place_agent(agent, (x, y))
            self.schedule.add(agent)
        
        for _ in range(num_yellow):
            x = random.randrange(0, 2 * (width // 3))
            y = random.randrange(height)
            agent = YellowRobotAgent(self)
            self.grid.place_agent(agent, (x, y))
            self.schedule.add(agent)
        
        for _ in range(num_red):
            x = random.randrange(width)
            y = random.randrange(height)
            agent = RedRobotAgent(self)
            self.grid.place_agent(agent, (x, y))
            self.schedule.add(agent)
    
    def get_zone(self, pos):
        x, y = pos
        if x < self.width / 3:
            return 'z1'
        elif x < 2 * self.width / 3:
            return 'z2'
        else:
            return 'z3'
    
    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()
