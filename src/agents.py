"""
File: agents.py
Group: 5 
Date of creation: 25/03/2024
Brief: Implements the Robot agents classes
Authors: Mateus Goto, Maxsuel Fernandes, João Pedro Regazzi
"""

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
        # Search grid cells for a waste agent whose waste_type is in allowed_types.
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

    def pick_up_if_present(self, target_type):
        """
        Checks the current cell for a waste of the given target_type.
        If found, the waste is picked up (added to self.carrying) and removed from the grid.
        """
        cell_contents = self.model.grid.get_cell_list_contents([self.pos])
        for obj in cell_contents:
            if hasattr(obj, "waste_type") and obj.waste_type == target_type:
                print(f"    {self.__class__.__name__} at {self.pos} picking up {target_type} waste.")
                self.carrying.append(target_type)
                self.model.grid.remove_agent(obj)
                if obj in self.model.custom_agents:
                    self.model.custom_agents.remove(obj)
                return True
        return False

    def step(self):
        # Default behavior: move toward any allowed waste.
        allowed_waste = []
        target = self.get_closest_waste(allowed_waste)
        if target is not None:
            new_pos = self.move_towards(target)
            if new_pos != self.pos:
                self.model.grid.move_agent(self, new_pos)

class GreenRobotAgent(BaseRobot):
    def allowed_zones(self):
        return ['z1']

    def step(self):
        print(f"[Green] at {self.pos} carrying: {self.carrying}")
        # If carrying a yellow waste, transport it east within z1.
        if "yellow" in self.carrying:
            current_x, current_y = self.pos
            if current_x < (self.model.width // 3) - 1:
                new_pos = (current_x + 1, current_y)
                self.model.grid.move_agent(self, new_pos)
                print(f"    [Green] Transporting yellow waste east to {new_pos}")
            else:
                # At eastern boundary of z1: drop the yellow waste.
                print(f"    [Green] At eastern boundary of z1, dropping yellow waste at {self.pos}.")
                self.carrying.remove("yellow")
                from objects import WasteAgent
                new_waste = WasteAgent(self.model, 'yellow', self.pos)
                self.model.grid.place_agent(new_waste, self.pos)
                self.model.custom_agents.append(new_waste)
            return

        # Otherwise, try to pick up green waste.
        green_count = self.carrying.count("green")
        if green_count < 2:
            if self.pick_up_if_present("green"):
                green_count += 1

        if green_count == 2:
            print(f"    [Green] Transforming 2 green wastes into 1 yellow waste at {self.pos}")
            for _ in range(2):
                self.carrying.remove("green")
            self.carrying.append("yellow")
            return

        # If not carrying enough green waste, move toward a green waste.
        target = self.get_closest_waste(["green"])
        if target:
            new_pos = self.move_towards(target)
            if new_pos != self.pos:
                self.model.grid.move_agent(self, new_pos)
            print(f"    [Green] Moving towards green waste at {target}, new position {new_pos}")
        else:
            print(f"    [Green] No green waste found.")

class YellowRobotAgent(BaseRobot):
    def allowed_zones(self):
        return ['z1', 'z2']

    def step(self):
        print(f"[Yellow] at {self.pos} carrying: {self.carrying}")
        # If carrying a red waste, transport it east within zones z1 and z2.
        if "red" in self.carrying:
            current_x, current_y = self.pos
            if current_x < (2 * self.model.width // 3) - 1:
                new_pos = (current_x + 1, current_y)
                self.model.grid.move_agent(self, new_pos)
                print(f"    [Yellow] Transporting red waste east to {new_pos}")
            else:
                print(f"    [Yellow] At eastern boundary of allowed zones, dropping red waste at {self.pos}.")
                self.carrying.remove("red")
                from objects import WasteAgent
                new_waste = WasteAgent(self.model, 'red', self.pos)
                self.model.grid.place_agent(new_waste, self.pos)
                self.model.custom_agents.append(new_waste)
            return

        # Otherwise, try to pick up yellow waste.
        yellow_count = self.carrying.count("yellow")
        if yellow_count < 2:
            if self.pick_up_if_present("yellow"):
                yellow_count += 1

        if yellow_count == 2:
            print(f"    [Yellow] Transforming 2 yellow wastes into 1 red waste at {self.pos}")
            for _ in range(2):
                self.carrying.remove("yellow")
            self.carrying.append("red")
            return

        # If not carrying enough yellow waste, move toward a yellow waste.
        target = self.get_closest_waste(["yellow"])
        if target:
            new_pos = self.move_towards(target)
            if new_pos != self.pos:
                self.model.grid.move_agent(self, new_pos)
            print(f"    [Yellow] Moving towards yellow waste at {target}, new position {new_pos}")
        else:
            # Reposition: if no yellow waste found, move west until reaching zone z1.
            if self.compute_zone() != 'z1':
                new_pos = (self.pos[0] - 1, self.pos[1])
                if not self.model.grid.out_of_bounds(new_pos):
                    self.model.grid.move_agent(self, new_pos)
                    print(f"    [Yellow] No yellow waste; repositioning west to {new_pos}")
            else:
                new_pos = (self.pos[0] + 1, self.pos[1])
                if not self.model.grid.out_of_bounds(new_pos):
                    self.model.grid.move_agent(self, new_pos)
                    print(f"    [Yellow] No yellow waste; repositioning east to {new_pos}")

class RedRobotAgent(BaseRobot):
    def allowed_zones(self):
        return ['z1', 'z2', 'z3']

    def step(self):
        print(f"[Red] at {self.pos} carrying: {self.carrying}")
        # If carrying a red waste, transport it east toward disposal.
        if "red" in self.carrying:
            if self.pos == self.model.waste_disposal.pos:
                print(f"    [Red] At disposal cell {self.pos}, dropping red waste.")
                self.carrying.remove("red")
            else:
                new_pos = self.move_towards(self.model.waste_disposal.pos)
                if new_pos != self.pos:
                    self.model.grid.move_agent(self, new_pos)
                    print(f"    [Red] Moving toward disposal cell at {self.model.waste_disposal.pos}, new position {new_pos}")
            return

        # Otherwise, try to pick up red waste.
        if self.pick_up_if_present("red"):
            print(f"    [Red] Picked up red waste at {self.pos}")
            return

        # If no red waste is found, reposition: move west until reaching zone z2.
        target = self.get_closest_waste(["red"])
        if target:
            new_pos = self.move_towards(target)
            if new_pos != self.pos:
                self.model.grid.move_agent(self, new_pos)
            print(f"    [Red] Moving towards red waste at {target}, new position {new_pos}")
        else:
            if self.compute_zone() == 'z3':
                new_pos = (self.pos[0] - 1, self.pos[1])
                if not self.model.grid.out_of_bounds(new_pos):
                    self.model.grid.move_agent(self, new_pos)
                    print(f"    [Red] No red waste; repositioning west to {new_pos}")
            else:
                new_pos = (self.pos[0] + 1, self.pos[1])
                if not self.model.grid.out_of_bounds(new_pos):
                    self.model.grid.move_agent(self, new_pos)
                    print(f"    [Red] No red waste; repositioning east to {new_pos}")
