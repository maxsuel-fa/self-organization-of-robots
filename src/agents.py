"""
File: agents.py
Group: 5 
Date of creation: 25/03/2024
Brief: Implements the Robot agents classes
Authors: Mateus Goto, Maxsuel Fernandes, João Pedro Regazzi
"""
### A MUDAR ( ZONAS N PRECISAM SER 1/3 1/3 1/3)

from mesa import Agent

class BaseRobot(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.knowledge = {}    # For storing percepts and memory
        self.carrying = []     # For holding wastes

    def compute_zone(self):
        x, y = self.pos
        grid_width = self.model.grid.width
        if x < grid_width / 3:
            return 'z1'
        elif x < 2 * grid_width / 3:
            return 'z2'
        else:
            return 'z3'

    def allowed_zones(self):
        # To be defined in subclasses.
        return []

    def perceive(self):
        adjacent_info = {}
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                new_pos = (self.pos[0] + dx, self.pos[1] + dy)
                if self.model.grid.out_of_bounds(new_pos):
                    continue
                adjacent_info[new_pos] = self.model.grid.get_cell_list_contents([new_pos])
        return adjacent_info

    def get_closest_waste(self, allowed_types):
        best_target = None
        best_distance = float('inf')
        # Note: In Mesa 3.0.3, coord_iter() returns (cell_contents, (x, y))
        for cell in self.model.grid.coord_iter():
            cell_content, (x, y) = cell  
            for obj in cell_content:
                if hasattr(obj, 'waste_type') and obj.waste_type in allowed_types:
                    cell_zone = self.model.get_zone((x, y))
                    if cell_zone in self.allowed_zones():
                        # Use Chebyshev distance (diagonals allowed)
                        dist = max(abs(x - self.pos[0]), abs(y - self.pos[1]))
                        if dist < best_distance:
                            best_distance = dist
                            best_target = (x, y)
        return best_target

    def move_towards(self, target):
        current_x, current_y = self.pos
        target_x, target_y = target
        step_x = 1 if target_x > current_x else (-1 if target_x < current_x else 0)
        step_y = 1 if target_y > current_y else (-1 if target_y < current_y else 0)
        new_position = (current_x + step_x, current_y + step_y)
        if self.model.grid.out_of_bounds(new_position):
            return self.pos
        return new_position

    def step(self):
        allowed_waste = []  # By default, no specific waste is targeted.
        target = self.get_closest_waste(allowed_waste)
        if target is not None:
            new_pos = self.move_towards(target)
            # Only move if the new position is different.
            if new_pos != self.pos:
                self.model.grid.move_agent(self, new_pos)

class GreenRobotAgent(BaseRobot):
    def allowed_zones(self):
        return ['z1']

    def step(self):
        print(f"[Robot Step] GreenRobotAgent at {self.pos} is stepping.")
        allowed_waste = ['green']
        target = self.get_closest_waste(allowed_waste)
        if target is not None:
            new_pos = self.move_towards(target)
            print(f"    GreenRobotAgent at {self.pos} found target {target} and moving to {new_pos}.")
            if new_pos != self.pos:
                self.model.grid.move_agent(self, new_pos)
        else:
            print(f"    GreenRobotAgent at {self.pos} found no target.")

class YellowRobotAgent(BaseRobot):
    def allowed_zones(self):
        return ['z1', 'z2']

    def step(self):
        #print(f"[Robot Step] YellowRobotAgent at {self.pos} is stepping.")
        allowed_waste = ['yellow']
        target = self.get_closest_waste(allowed_waste)
        if target is not None:
            new_pos = self.move_towards(target)
            #print(f"    YellowRobotAgent at {self.pos} found target {target} and moving to {new_pos}.")
            if new_pos != self.pos:
                self.model.grid.move_agent(self, new_pos)
        #else:
        #    print(f"    YellowRobotAgent at {self.pos} found no target.")

class RedRobotAgent(BaseRobot):
    def allowed_zones(self):
        return ['z1', 'z2', 'z3']

    def step(self):
        #print(f"[Robot Step] RedRobotAgent at {self.pos} is stepping.")
        allowed_waste = ['red']
        target = self.get_closest_waste(allowed_waste)
        if target is not None:
            new_pos = self.move_towards(target)
            #print(f"    RedRobotAgent at {self.pos} found target {target} and moving to {new_pos}.")
            if new_pos != self.pos:
                self.model.grid.move_agent(self, new_pos)
        #else:
        #    print(f"    RedRobotAgent at {self.pos} found no target.")