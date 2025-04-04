"""
File: objects.py
Group: 5 
Date of creation: 25/03/2024
Brief: Implements the objects in the grid
Authors: Mateus Goto, Maxsuel Fernandes, João Pedro Regazzi
"""

from mesa import Agent
import random

class RadioactivityAgent(Agent):
    def __init__(self, model, pos):
        super().__init__(model)
        # Do not assign self.pos here—this is managed by the grid.
        self.initial_pos = pos  # Store the initial position.
        self.zone = self.model.get_zone(pos)
        self.radioactivity = self.generate_radioactivity()

    def generate_radioactivity(self):
        if self.zone == 'z1':
            return random.uniform(0, 0.33)
        elif self.zone == 'z2':
            return random.uniform(0.33, 0.66)
        elif self.zone == 'z3':
            return random.uniform(0.66, 1)

    def step(self):
        pass

class WasteAgent(Agent):
    def __init__(self, model, waste_type, pos):
        super().__init__(model)
        self.waste_type = waste_type  # 'green', 'yellow', or 'red'
        self.initial_pos = pos  # Store the initial position.

    def step(self):
        pass

class WasteDisposalAgent(Agent):
    def __init__(self, model, pos):
        super().__init__(model)
        self.initial_pos = pos  # Store the initial position.

    def step(self):
        pass

#create a wall that robots cannot go
class wallAgent(Agent):
    def __init__(self, model, pos):
        super().__init__(model)
        self.initial_pos = pos
    
    def step(self):
        pass

