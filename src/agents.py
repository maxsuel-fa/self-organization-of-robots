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
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.knowledge = {}    # You can use this to store percepts and memory
        self.carrying = []     # List to hold wastes the robot has collected

    def compute_zone(self):
        # Determine zone based on the agent's x-coordinate
        x, y = self.pos
        grid_width = self.model.grid.width
        if x < grid_width / 3:
            return 'z1'
        elif x < 2 * grid_width / 3:
            return 'z2'
        else:
            return 'z3'

    def allowed_zones(self):
        # To be overridden by subclasses.
        return []

    def perceive(self):
        # You can extend this method to include a richer set of percepts.
        # Here we get information from all adjacent (including diagonal) cells.
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
        # Look through all cells of the grid to find the closest waste of an allowed type.
        best_target = None
        best_distance = float('inf')
        for cell in self.model.grid.coord_iter():
            cell_content, x, y = cell
            for obj in cell_content:
                if hasattr(obj, 'waste_type') and obj.waste_type in allowed_types:
                    # Check that the cell is in one of the allowed zones
                    cell_zone = self.model.get_zone((x, y))
                    if cell_zone in self.allowed_zones():
                        # Using Chebyshev distance (diagonals allowed)
                        dist = max(abs(x - self.pos[0]), abs(y - self.pos[1]))
                        if dist < best_distance:
                            best_distance = dist
                            best_target = (x, y)
        return best_target

    def move_towards(self, target):
        # Move one step toward the target (diagonally if needed)
        current_x, current_y = self.pos
        target_x, target_y = target
        step_x = 0
        step_y = 0
        if target_x > current_x:
            step_x = 1
        elif target_x < current_x:
            step_x = -1
        if target_y > current_y:
            step_y = 1
        elif target_y < current_y:
            step_y = -1
        new_position = (current_x + step_x, current_y + step_y)
        # Stay in place if the new position is out of bounds
        if self.model.grid.out_of_bounds(new_position):
            return self.pos
        return new_position

    def step(self):
        # By default, the robot looks for the closest waste of a given type
        # (the allowed type(s) should be defined in each subclass).
        allowed_waste = []  
        target = self.get_closest_waste(allowed_waste)
        if target is not None:
            new_pos = self.move_towards(target)
            self.model.grid.move_agent(self, new_pos)
        # If no target is found, the robot stays still (could add idle behavior here).

class GreenRobotAgent(BaseRobot):
    def allowed_zones(self):
        # Green robots are restricted to zone z1.
        return ['z1']

    def step(self):
        # For green robots, we are looking for green waste.
        allowed_waste = ['green']
        # You can later extend this to include pickup/transform actions.
        target = self.get_closest_waste(allowed_waste)
        if target is not None:
            new_pos = self.move_towards(target)
            self.model.grid.move_agent(self, new_pos)
        # Else: do nothing (stay still)

class YellowRobotAgent(BaseRobot):
    def allowed_zones(self):
        # Yellow robots can operate in zones z1 and z2.
        return ['z1', 'z2']

    def step(self):
        allowed_waste = ['yellow']
        target = self.get_closest_waste(allowed_waste)
        if target is not None:
            new_pos = self.move_towards(target)
            self.model.grid.move_agent(self, new_pos)

class RedRobotAgent(BaseRobot):
    def allowed_zones(self):
        # Red robots can operate in all zones: z1, z2, and z3.
        return ['z1', 'z2', 'z3']

    def step(self):
        allowed_waste = ['red']
        target = self.get_closest_waste(allowed_waste)
        if target is not None:
            new_pos = self.move_towards(target)
            self.model.grid.move_agent(self, new_pos)
