"""
File: agents.py
Group: 5 
Date of creation: 25/03/2024
Brief: Implements the Robot agents classes with waste assignment and targeting based on distance
Authors: Mateus Goto, Maxsuel Fernandes, João Pedro Regazzi
"""

from mesa import Agent

class BaseRobot(Agent):
    def __init__(self, model):
        super().__init__(model)
        self.knowledge = {}    # For storing percepts and memory
        self.carrying = []     # For wastes that have been picked up
        self.assigned_wastes = set()  # Waste objects this robot is assigned to collect

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
        for cell in self.model.grid.coord_iter():
            cell_content, (x, y) = cell  
            for obj in cell_content:
                if hasattr(obj, 'waste_type') and obj.waste_type in allowed_types:
                    cell_zone = self.model.get_zone((x, y))
                    if cell_zone in self.allowed_zones():
                        dist = max(abs(x - self.pos[0]), abs(y - self.pos[1]))
                        if dist < best_distance:
                            best_distance = dist
                            best_target = (x, y)
        return best_target

    def get_closest_assigned_waste(self, target_type):
        """Return the assigned waste object of the given type that is closest to this agent (based on Chebyshev distance)."""
        best_waste = None
        best_distance = float('inf')
        for waste in self.assigned_wastes:
            if hasattr(waste, "waste_type") and waste.waste_type == target_type:
                d = max(abs(waste.pos[0] - self.pos[0]), abs(waste.pos[1] - self.pos[1]))
                if d < best_distance:
                    best_distance = d
                    best_waste = waste
        return best_waste

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
        Only picks it up if that waste is assigned to this robot.
        """
        cell_contents = self.model.grid.get_cell_list_contents([self.pos])
        for obj in cell_contents:
            if hasattr(obj, "waste_type") and obj.waste_type == target_type:
                if obj in self.assigned_wastes:
                    print(f"    {self.__class__.__name__} at {self.pos} picking up assigned {target_type} waste.")
                    self.carrying.append(target_type)
                    self.assigned_wastes.remove(obj)
                    self.model.grid.remove_agent(obj)
                    if obj in self.model.custom_agents:
                        self.model.custom_agents.remove(obj)
                    return True
        return False

    def step(self):
        # Default behavior: move toward any allowed waste (not used by robot subclasses)
        allowed_waste = []
        target = self.get_closest_waste(allowed_waste)
        if target is not None:
            new_pos = self.move_towards(target)
            if new_pos != self.pos:
                self.model.grid.move_agent(self, new_pos)

class GreenRobotAgent(BaseRobot):
    def allowed_zones(self):
        return ['z1']

    def assign_wastes(self):
        if self.assigned_wastes:
            return
        # Green robots require 2 green wastes.
        required = 2
        with self.model.green_lock:
            if len(self.model.unassigned_green_wastes) < required:
                print(f"    [Green] Not enough unassigned green wastes available.")
                return
            # Sort available wastes by distance from the robot.
            available = list(self.model.unassigned_green_wastes)
            available.sort(key=lambda waste: max(abs(waste.pos[0] - self.pos[0]), abs(waste.pos[1] - self.pos[1])))
            for waste in available[:required]:
                self.assigned_wastes.add(waste)
                self.model.unassigned_green_wastes.remove(waste)
        print(f"    [Green] Assigned green wastes: {self.assigned_wastes}")

    def step(self):
        print(f"[Green] at {self.pos} carrying: {self.carrying}, assigned: {self.assigned_wastes}")
        self.assign_wastes()
        # If carrying a yellow waste, transport it east within z1.
        if "yellow" in self.carrying:
            current_x, current_y = self.pos
            if current_x < (self.model.width // 3) - 1:
                new_pos = (current_x + 1, current_y)
                self.model.grid.move_agent(self, new_pos)
                print(f"    [Green] Transporting yellow waste east to {new_pos}")
            else:
                print(f"    [Green] At eastern boundary of z1, dropping yellow waste at {self.pos}.")
                self.carrying.remove("yellow")
                from objects import WasteAgent
                new_waste = WasteAgent(self.model, 'yellow', self.pos)
                self.model.grid.place_agent(new_waste, self.pos)
                self.model.custom_agents.append(new_waste)
                with self.model.yellow_lock:
                    self.model.unassigned_yellow_wastes.add(new_waste)
            return

        # If not carrying enough green waste, target the closest assigned green waste.
        if self.carrying.count("green") < 2:
            assigned = self.get_closest_assigned_waste("green")
            if assigned:
                target = assigned.pos
                new_pos = self.move_towards(target)
                if new_pos != self.pos:
                    self.model.grid.move_agent(self, new_pos)
                print(f"    [Green] Moving towards assigned green waste at {target}, new position {new_pos}")
            else:
                print(f"    [Green] No assigned green waste found.")
            # Attempt pick-up if present.
            self.pick_up_if_present("green")
            # Check again after pick-up.
            if self.carrying.count("green") == 2:
                print(f"    [Green] Transforming 2 green wastes into 1 yellow waste at {self.pos}")
                for _ in range(2):
                    self.carrying.remove("green")
                self.carrying.append("yellow")
            return

class YellowRobotAgent(BaseRobot):
    def allowed_zones(self):
        return ['z1', 'z2']

    def assign_wastes(self):
        if self.assigned_wastes:
            return
        # Yellow robots require 2 yellow wastes.
        required = 2
        with self.model.yellow_lock:
            if len(self.model.unassigned_yellow_wastes) < required:
                print(f"    [Yellow] Not enough unassigned yellow wastes available.")
                return
            available = list(self.model.unassigned_yellow_wastes)
            available.sort(key=lambda waste: max(abs(waste.pos[0]-self.pos[0]), abs(waste.pos[1]-self.pos[1])))
            for waste in available[:required]:
                self.assigned_wastes.add(waste)
                self.model.unassigned_yellow_wastes.remove(waste)
        print(f"    [Yellow] Assigned yellow wastes: {self.assigned_wastes}")

    def step(self):
        print(f"[Yellow] at {self.pos} carrying: {self.carrying}, assigned: {self.assigned_wastes}")
        self.assign_wastes()
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
                with self.model.red_lock:
                    self.model.unassigned_red_wastes.add(new_waste)
            return

        # If not carrying enough yellow waste, target the closest assigned yellow waste.
        if self.carrying.count("yellow") < 2:
            assigned = self.get_closest_assigned_waste("yellow")
            if assigned:
                target = assigned.pos
                new_pos = self.move_towards(target)
                if new_pos != self.pos:
                    self.model.grid.move_agent(self, new_pos)
                print(f"    [Yellow] Moving towards assigned yellow waste at {target}, new position {new_pos}")
                self.pick_up_if_present("yellow")
            else:
                # If no yellow waste found
                if self.get_closest_assigned_waste("yellow") is None:
                    # Reposition: move west until reaching zone z1.
                    if self.compute_zone() == 'z2':
                        new_pos = (self.pos[0] - 1, self.pos[1])
                        if not self.model.grid.out_of_bounds(new_pos):
                            self.model.grid.move_agent(self, new_pos)
                            print(f"    [Yellow] No assigned yellow waste; repositioning west to {new_pos} (aiming for zone z1)")
                    # Reposition: move west until reaching zone z2.
                    else:
                        new_pos = (self.pos[0] + 1, self.pos[1])
                        if not self.model.grid.out_of_bounds(new_pos):
                            self.model.grid.move_agent(self, new_pos)
                            print(f"    [Yellow] No assigned yellow waste; repositioning east to {new_pos} (aiming for zone z2)")
                        print(f"    [Yellow] No assigned yellow waste found.")

        if self.carrying.count("yellow") == 2:
            print(f"    [Yellow] Transforming 2 yellow wastes into 1 red waste at {self.pos}")
            for _ in range(2):
                self.carrying.remove("yellow")
            self.carrying.append("red")
        return

        

class RedRobotAgent(BaseRobot):
    def allowed_zones(self):
        return ['z1', 'z2', 'z3']

    def assign_wastes(self):
        if self.assigned_wastes:
            return
        # Red robots require 1 red waste.
        required = 1
        with self.model.red_lock:
            if len(self.model.unassigned_red_wastes) < required:
                print(f"    [Red] Not enough unassigned red wastes available.")
                return
            available = list(self.model.unassigned_red_wastes)
            available.sort(key=lambda waste: max(abs(waste.pos[0]-self.pos[0]), abs(waste.pos[1]-self.pos[1])))
            self.assigned_wastes.add(available[0])
            self.model.unassigned_red_wastes.remove(available[0])
        print(f"    [Red] Assigned red waste: {self.assigned_wastes}")

    def step(self):
        print(f"[Red] at {self.pos} carrying: {self.carrying}, assigned: {self.assigned_wastes}")
        self.assign_wastes()
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

        # If not carrying red waste, target the closest assigned red waste.
        assigned = self.get_closest_assigned_waste("red")
        if assigned:
            target = assigned.pos
            new_pos = self.move_towards(target)
            if new_pos != self.pos:
                self.model.grid.move_agent(self, new_pos)
            print(f"    [Red] Moving towards assigned red waste at {target}, new position {new_pos}")
            self.pick_up_if_present("red")
        # If no assigned red waste is found
        else:
            # Reposition: move west until reaching zone z2.
            if self.compute_zone() == 'z3':
                new_pos = (self.pos[0] - 1, self.pos[1])
                if not self.model.grid.out_of_bounds(new_pos):
                    self.model.grid.move_agent(self, new_pos)
                    print(f"    [Red] No assigned red waste; repositioning west to {new_pos} (aiming for zone z2)")
            # Reposition: move east until reaching zone z3.
            else:
                new_pos = (self.pos[0] + 1, self.pos[1])
                if not self.model.grid.out_of_bounds(new_pos):
                    self.model.grid.move_agent(self, new_pos)
                    print(f"    [Red] No assigned red waste; repositioning east to {new_pos} (aiming for zone z3)")
                print(f"    [Red] In zone z2 and no assigned red waste found, waiting.")
