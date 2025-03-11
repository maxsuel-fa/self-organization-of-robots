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
from agents import GreenRobotAgent, YellowRobotAgent, RedRobotAgent
from objects import RadioactivityAgent, WasteAgent, WasteDisposalAgent
import random

class RobotMission(Model):
    def __init__(self, width, height, num_green, num_yellow, num_red, num_waste):
        self.width = width
        self.height = height
        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(width, height, torus=False)
        
        # Add a radioactivity agent to each cell.
        for x in range(width):
            for y in range(height):
                radio = RadioactivityAgent(self.next_id(), self, (x, y))
                self.grid.place_agent(radio, (x, y))
                self.schedule.add(radio)
        
        # Place the Waste Disposal Agent in a random cell of the most eastern column.
        eastern_x = width - 1
        disposal_y = random.randrange(height)
        self.waste_disposal = WasteDisposalAgent(self.next_id(), self, (eastern_x, disposal_y))
        self.grid.place_agent(self.waste_disposal, (eastern_x, disposal_y))
        self.schedule.add(self.waste_disposal)
        
        # Add waste agents (initially green waste in zone z1).
        for _ in range(num_waste):
            x = random.randrange(0, width // 3)  # zone z1
            y = random.randrange(height)
            waste = WasteAgent(self.next_id(), self, 'green', (x, y))
            self.grid.place_agent(waste, (x, y))
            self.schedule.add(waste)
        
        # Create and place robot agents.
        for _ in range(num_green):
            # Place green robots in zone z1.
            x = random.randrange(0, width // 3)
            y = random.randrange(height)
            agent = GreenRobotAgent(self.next_id(), self)
            self.grid.place_agent(agent, (x, y))
            self.schedule.add(agent)
        
        for _ in range(num_yellow):
            # Place yellow robots in zones z1 or z2.
            x = random.randrange(0, 2 * (width // 3))
            y = random.randrange(height)
            agent = YellowRobotAgent(self.next_id(), self)
            self.grid.place_agent(agent, (x, y))
            self.schedule.add(agent)
        
        for _ in range(num_red):
            # Place red robots anywhere (zones z1, z2, or z3).
            x = random.randrange(width)
            y = random.randrange(height)
            agent = RedRobotAgent(self.next_id(), self)
            self.grid.place_agent(agent, (x, y))
            self.schedule.add(agent)
    
    def get_zone(self, pos):
        # Determine the zone based on the x-coordinate.
        x, y = pos
        if x < self.width / 3:
            return 'z1'
        elif x < 2 * self.width / 3:
            return 'z2'
        else:
            return 'z3'
    
    def step(self):
        self.schedule.step()
