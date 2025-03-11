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
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)
        self.pos = pos
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
        # Radioactivity is static; no behavior required.
        pass

class WasteAgent(Agent):
    def __init__(self, unique_id, model, waste_type, pos):
        super().__init__(unique_id, model)
        self.waste_type = waste_type  # 'green', 'yellow', or 'red'
        self.pos = pos

    def step(self):
        # Waste does not move by itself.
        pass

class WasteDisposalAgent(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)
        self.pos = pos

    def step(self):
        # Waste disposal is static.
        pass
