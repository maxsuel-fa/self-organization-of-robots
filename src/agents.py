"""
File: agents.py
Group: 5 
Date of creation: 25/03/2024
Brief: Implements the Robot agents classes with waste assignment and targeting based on distance
Authors: Mateus Goto, Maxsuel Fernandes, João Pedro Regazzi
"""

from mesa import Agent
from objects import wallAgent
import heapq
# Heuristic zone


class BaseRobot(Agent):
    def __init__(self, model, heuristic="closest"):
        super().__init__(model)
        self.knowledge = {}    # For storing percepts and memory
        self.carrying = []     # For wastes that have been picked up
        self.assigned_wastes = set()  # Waste objects this robot is assigned to collect
        self.heuristic = heuristic

    def sort_by_closest(self, available):
        return sorted(available, key=lambda waste: max(abs(waste.pos[0] - self.pos[0]), abs(waste.pos[1] - self.pos[1])))

    def sort_randomly(self, available):
        import random
        random.shuffle(available)
        return available

    def sort_by_min_total_distance(self, available, target_point):
        """
        Sort available wastes by the sum of the distance from the robot to the waste 
        plus the distance from the waste to the target_point.

        Target point is eastern boundary of zone for green and yellow robots and the waste disposal
        for red robots.
        """
        return sorted(available, key=lambda waste: max(abs(waste.pos[0] - self.pos[0]), abs(waste.pos[1] - self.pos[1])) +
                      max(abs(waste.pos[0] - target_point[0]), abs(waste.pos[1] - target_point[1])))

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
    #Try new method of moving
    def follow_path(self, path):
        if path:
            print(f"[DEBUG] Following A* path: {path}")
            next_pos = path[0]
            if next_pos != self.pos:
                self.model.grid.move_agent(self, next_pos)
                return next_pos
        return self.pos
    def astar_path(self, start, goal):
        def heuristic(a, b):
            return max(abs(a[0] - b[0]), abs(a[1] - b[1]))  # Chebyshev

        open_set = []
        heapq.heappush(open_set, (0 + heuristic(start, goal), 0, start, []))
        visited = set()

        while open_set:
            est_total, cost, current, path = heapq.heappop(open_set)
            if current in visited:
                continue
            visited.add(current)
            path = path + [current]

            if current == goal:
                return path[1:]  # Skip start

            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    neighbor = (current[0] + dx, current[1] + dy)
                    if self.model.grid.out_of_bounds(neighbor):
                        continue
                    contents = self.model.grid.get_cell_list_contents([neighbor])
                    if any(isinstance(obj, wallAgent) for obj in contents):
                        print("in fact i really avoid the all")
                        continue
                    if neighbor not in visited:
                        new_cost = cost + 1
                        priority = new_cost + heuristic(neighbor, goal)
                        heapq.heappush(open_set, (priority, new_cost, neighbor, path))
        return []  # No path found

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
        
        # Avoid moving into walls
        cell_contents = self.model.grid.get_cell_list_contents([new_position])
        if any(isinstance(obj, wallAgent) for obj in cell_contents):
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
            target = (self.pos[0] + 1, self.pos[1])
            new_pos = self.move_towards(target)
            if new_pos != self.pos:
                self.model.grid.move_agent(self, new_pos)

class GreenRobotAgent(BaseRobot):
    def allowed_zones(self):
        return ['z1']

    def assign_wastes(self):
        if self.assigned_wastes:
            return
        required = 2
        with self.model.green_lock:
            if len(self.model.unassigned_green_wastes) < required:
                print("    [Green] Not enough unassigned green wastes available.")
                return
            available = list(self.model.unassigned_green_wastes)
            if self.heuristic == "closest":
                available = self.sort_by_closest(available)
            elif self.heuristic == "random":
                available = self.sort_randomly(available)
            elif self.heuristic == "min_total_distance":
                target_point = ((self.model.width // 3) - 1, self.pos[1])
                available = self.sort_by_min_total_distance(available, target_point)
            elif self.heuristic == "astar":
                def astar_cost(waste):
                    path = self.astar_path(self.pos, waste.pos)
                    if not path:
                        return float('inf')
                    delivery_target = ((self.model.width // 3) - 1, waste.pos[1])
                    delivery_dist = max(abs(waste.pos[0] - delivery_target[0]), abs(waste.pos[1] - delivery_target[1]))
                    return len(path) + delivery_dist
                available.sort(key=astar_cost)

            for waste in available[:required]:
                self.assigned_wastes.add(waste)
                self.model.unassigned_green_wastes.remove(waste)
        print(f"    [Green] Assigned green wastes: {self.assigned_wastes}")

    def step(self):
        print(f"[Green] at {self.pos} carrying: {self.carrying}, assigned: {self.assigned_wastes}")
        self.assign_wastes()

        # If carrying a yellow waste, transport it east within z1.
        if "yellow" in self.carrying:
            delivery_x = (self.model.width // 3) - 1
            delivery_target = (delivery_x, self.pos[1])

            if self.pos[0] < delivery_x:
                if self.heuristic == "astar":
                    path = self.astar_path(self.pos, delivery_target)
                    new_pos = self.follow_path(path)
                else:
                    new_pos = self.move_towards(delivery_target)
                    if new_pos != self.pos:
                        self.model.grid.move_agent(self, new_pos)
                if new_pos != self.pos:
                    print(f"    [Green] Transporting yellow waste east to {new_pos}")
                else:
                    print(f"    [Green] Blocked en route to drop yellow at {self.pos}")
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

        # If not carrying enough green waste, move to assigned waste
        if self.carrying.count("green") < 2:
            assigned = self.get_closest_assigned_waste("green")
            if assigned:
                target = assigned.pos
                if self.heuristic == "astar":
                    path = self.astar_path(self.pos, target)
                    new_pos = self.follow_path(path)
                else:
                    new_pos = self.move_towards(target)
                    if new_pos != self.pos:
                        self.model.grid.move_agent(self, new_pos)
                print(f"    [Green] Moving towards assigned green waste at {target}, new position {new_pos}")
            else:
                print("    [Green] No assigned green waste found.")

            self.pick_up_if_present("green")

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
                print("    [Yellow] Not enough unassigned yellow wastes available.")
                return
            available = list(self.model.unassigned_yellow_wastes)
            if self.heuristic == "closest":
                available = self.sort_by_closest(available)
            elif self.heuristic == "random":
                available = self.sort_randomly(available)
            elif self.heuristic == "min_total_distance":
                # Target is eastern boundary of zone z2: x = (2*self.model.width//3)-1, same y.
                target_point = ((self.model.width // 3) - 1, self.pos[1])
                available = self.sort_by_min_total_distance(available, target_point)
            elif self.heuristic == "astar":
            # Use path length (if any) + Chebyshev to target zone
                def astar_cost(waste):
                    path = self.astar_path(self.pos, waste.pos)
                    if not path:
                        return float('inf')
                    # Estimate distance to delivery target (right edge of z2)
                    delivery_target = ((2 * self.model.width // 3) - 1, waste.pos[1])
                    delivery_dist = max(abs(waste.pos[0] - delivery_target[0]), abs(waste.pos[1] - delivery_target[1]))
                    return len(path) + delivery_dist

                available.sort(key=astar_cost)
            for waste in available[:required]:
                self.assigned_wastes.add(waste)
                self.model.unassigned_yellow_wastes.remove(waste)
        print(f"    [Yellow] Assigned yellow wastes: {self.assigned_wastes}")

    def step(self):
        print(f"[Yellow] at {self.pos} carrying: {self.carrying}, assigned: {self.assigned_wastes}")
        self.assign_wastes()
        # If carrying a red waste, transport it east within zones z1 and z2.
        if "red" in self.carrying:
            delivery_x = (2 * self.model.width // 3) - 1
            delivery_target = (delivery_x, self.pos[1])

            if self.pos[0] < delivery_x:
                if self.heuristic == "astar":
                    path = self.astar_path(self.pos, delivery_target)
                    new_pos = self.follow_path(path)
                else:
                    new_pos = self.move_towards(delivery_target)
                    if new_pos != self.pos:
                        self.model.grid.move_agent(self, new_pos)
                if new_pos != self.pos:
                    print(f"    [Yellow] Transporting red waste to {new_pos}")
                else:
                    print(f"    [Yellow] Blocked en route to drop red at {self.pos}")
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
                if self.heuristic == "astar":
                    path = self.astar_path(self.pos, target)
                    new_pos = self.follow_path(path)
                else:
                    new_pos = self.move_towards(target)
                    if new_pos != self.pos:
                        self.model.grid.move_agent(self, new_pos)
                print(f"    [Yellow] Moving towards assigned yellow waste at {target}, new position {new_pos}")
                self.pick_up_if_present("yellow")
            # !!!! comment for now to test wall if i forgot in the future
            """ else:
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
                        print("    [Yellow] No assigned yellow waste found.") """

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
        required = 1
        with self.model.red_lock:
            if len(self.model.unassigned_red_wastes) < required:
                print("    [Red] Not enough unassigned red wastes available.")
                return
            available = list(self.model.unassigned_red_wastes)
            if self.heuristic == "closest":
                available = self.sort_by_closest(available)
            elif self.heuristic == "random":
                available = self.sort_randomly(available)
            elif self.heuristic == "min_total_distance":
                target_point = self.model.waste_disposal.pos
                available = self.sort_by_min_total_distance(available, target_point)
            elif self.heuristic == "astar":
                def astar_cost(waste):
                    path = self.astar_path(self.pos, waste.pos)
                    if not path:
                        return float('inf')
                    disposal = self.model.waste_disposal.pos
                    disposal_dist = max(abs(waste.pos[0] - disposal[0]), abs(waste.pos[1] - disposal[1]))
                    return len(path) + disposal_dist
                available.sort(key=astar_cost)
            self.assigned_wastes.add(available[0])
            self.model.unassigned_red_wastes.remove(available[0])
        print(f"    [Red] Assigned red waste: {self.assigned_wastes}")

    def step(self):
        print(f"[Red] at {self.pos} carrying: {self.carrying}, assigned: {self.assigned_wastes}")
        self.assign_wastes()

        # Step 1: Deliver if carrying red
        if "red" in self.carrying:
            disposal_pos = self.model.waste_disposal.pos
            if self.pos == disposal_pos:
                print(f"    [Red] At disposal cell {self.pos}, dropping red waste.")
                self.carrying.remove("red")
            else:
                if self.heuristic == "astar":
                    path = self.astar_path(self.pos, disposal_pos)
                    new_pos = self.follow_path(path)
                else:
                    new_pos = self.move_towards(disposal_pos)
                    if new_pos != self.pos:
                        self.model.grid.move_agent(self, new_pos)
                print(f"    [Red] Moving toward disposal at {disposal_pos}, new position {new_pos}")
            return

        # Step 2: Move to assigned red waste
        assigned = self.get_closest_assigned_waste("red")
        if assigned:
            target = assigned.pos
            if self.heuristic == "astar":
                path = self.astar_path(self.pos, target)
                new_pos = self.follow_path(path)
            else:
                new_pos = self.move_towards(target)
                if new_pos != self.pos:
                    self.model.grid.move_agent(self, new_pos)
            print(f"    [Red] Moving toward assigned red waste at {target}, new position {new_pos}")
            self.pick_up_if_present("red")
        # If no assigned red waste is found
        # !!!! comment for now to test wall if i forgot in the future
        """ else:
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
                print("    [Red] In zone z2 and no assigned red waste found, waiting.") """
