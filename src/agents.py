"""
File: agents.py
Group: 5 
Date of creation: 25/03/2024
Brief: Implements the Robot agents classes with waste assignment and targeting based on distance
Authors: Mateus Goto, Maxsuel Fernandes, João Pedro Regazzi
"""

from mesa import Agent
from uuid import uuid4
from objects import wallAgent
import heapq

class BaseRobot(Agent):
    DEBUG = False                        # ← flip to False to mute all logs
    _uid_counter = 0                      # own id generator

    def __init__(self, model, heuristic="closest"):
        super().__init__(model)      

        # give every agent a *real* unique integer id
        self.unique_id = BaseRobot._uid_counter
        BaseRobot._uid_counter += 1
        self.locked_for_help   = False
        self.handshake_id      = None
        # common state ---------------------------------------------------
        self.heuristic         = heuristic
        self.carrying          = []
        self.assigned_wastes   = set()
        self.distance_traveled = 0

        # exploration helper
        self.scout_dir  = 1
        self.scout_hdir = 1
        self.scout_col  = None

        #blindofold
        self.vision_radius  = 4 

        # tiny logger
        self.log = (lambda *msg, **k: print(f"[{self.unique_id}]", *msg, **k)
                    if BaseRobot.DEBUG else (lambda *a, **k: None))


    #not cheating heuristics
    def sort_by_farthest(self, available):
        """Return the same list, farthest‑first."""
        return sorted(
            available,
            key=lambda w: -max(abs(w.pos[0] - self.pos[0]), abs(w.pos[1] - self.pos[1]))
        )
    #little communication betwen robots
    def _send(self, msg: dict) -> None:
        msg["step"] = self.model.step_count
        with self.model.message_lock:
            self.model.message_board.append(msg)
        self.log("SEND", msg)
        """ print("carrying :", self.carrying)
        print("assigned : ", self.assigned_wastes, "len:", len(self.assigned_wastes))  """              

    def _inbox(self, predicate):
        with self.model.message_lock:
            keep, target = [], []
            for m in self.model.message_board:
                (target if predicate(m) else keep).append(m)
            self.model.message_board = keep
        if target:                         
            self.log("RECV", target)
            """ print("carrying :", self.carrying)
            print("assigned : ", self.assigned_wastes, "len:", len(self.assigned_wastes))  """
        return target
    
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

    def follow_path(self, path):
        if path:
            #print(f"[DEBUG] Following A* path: {path}")
            next_pos = path[0]
            if next_pos != self.pos:
                self.model.grid.move_agent(self, next_pos)
                self.distance_traveled += 1  # Increment distance counter
                return next_pos
        return self.pos

    def astar_path(self, start, goal):
        def heuristic(a, b):
            return max(abs(a[0] - b[0]), abs(a[1] - b[1]))  # Chebyshev

        open_set = []
        heapq.heappush(open_set, (heuristic(start, goal), 0, start, []))
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
                        continue
                    if neighbor not in visited:
                        new_cost = cost + 1
                        priority = new_cost + heuristic(neighbor, goal)
                        heapq.heappush(open_set, (priority, new_cost, neighbor, path))
        return []  # No path found

    def get_closest_assigned_waste(self, target_type):
        """Return the assigned waste of the given type closest to this agent."""
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
        cell_contents = self.model.grid.get_cell_list_contents([self.pos])
        for obj in cell_contents:
            if getattr(obj, "waste_type", None) == target_type and obj in self.assigned_wastes:

                # add to backpack and clear the bookkeeping
                self.carrying.append(target_type)
                self.assigned_wastes.remove(obj)
                self.model.seen_wastes.discard(obj)        # ← keep global list clean

                # make sure no other robot will request it
                with getattr(self.model, f"{target_type}_lock"):
                    getattr(self.model, f"unassigned_{target_type}_wastes", set()).discard(obj)

                self.model.grid.remove_agent(obj)
                self.model.custom_agents.remove(obj)
                return True
        return False

    def step(self):
        self._update_seen_wastes()
        # Default behavior, not used by subclasses.
        allowed_waste = []
        target = self.get_closest_waste(allowed_waste)
        if target is not None:
            target = (self.pos[0] + 1, self.pos[1])
            new_pos = self.move_towards(target)
            if new_pos != self.pos:
                self.model.grid.move_agent(self, new_pos)
    
    def _update_seen_wastes(self):
        #Add wastes within < radius cells to model.seen_wastes.
        r = self.vision_radius
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                x, y = self.pos[0] + dx, self.pos[1] + dy
                if self.model.grid.out_of_bounds((x, y)):
                    continue
                for obj in self.model.grid.get_cell_list_contents((x, y)):
                    if hasattr(obj, "waste_type"):
                        self.model.seen_wastes.add(obj)


    def _scout_step(self):
        #solve teleportation bug
        zone_min, zone_max = {
            "z1": (0, self.model.width // 3 - 1),
            "z2": (self.model.width // 3, 2 * self.model.width // 3 - 1),
            "z3": (2 * self.model.width // 3, self.model.width - 1),
        }[self.allowed_zones()[-1]]

        x, y = self.pos

        # ── 0. walk horizontally until we are *inside* the zone ─────────
        if x < zone_min:
            self.model.grid.move_agent(self, (x + 1, y))
            self.distance_traveled += 1
            return
        if x > zone_max:
            self.model.grid.move_agent(self, (x - 1, y))
            self.distance_traveled += 1
            return

        # ── 1. once inside, run the normal serpentine scan ─────────────
        # first call: anchor the scan column
        if self.scout_col is None:
            self.scout_col = x

        next_y = y + self.scout_dir

        # turn at top / bottom edge and step horizontally
        if next_y < 0 or next_y >= self.model.height:
            self.scout_dir *= -1
            self.scout_col += self.scout_hdir

            # bounce at horizontal edges of the zone
            if self.scout_col > zone_max:
                self.scout_col = zone_max
                self.scout_hdir = -1
            elif self.scout_col < zone_min:
                self.scout_col = zone_min
                self.scout_hdir = 1

            next_y = y + self.scout_dir  # recompute after turn

        target = (self.scout_col, next_y)
        if not self.model.grid.out_of_bounds(target):
            self.model.grid.move_agent(self, target)
            self.distance_traveled += 1



class GreenRobotAgent(BaseRobot):
    def __init__(self, model, heuristic="closest"):
        super().__init__(model, heuristic)
        # hand‑off protocol state
        self.partner_id       = None
        self.offer_active     = False
        self.rendezvous_pos   = None

    def allowed_zones(self):
        return ['z1']

    def _compute_midpoint(self, other_pos):
        mx = (self.pos[0] + other_pos[0]) // 2
        my = (self.pos[1] + other_pos[1]) // 2
        self.rendezvous_pos = (mx, my)

    def _reset_handshake(self):
        self.partner_id     = None
        self.offer_active   = False
        self.rendezvous_pos = None

    def assign_wastes(self):
        need = 2 - self.carrying.count("green") \
                 - sum(1 for w in self.assigned_wastes if w.waste_type == "green")
        if need <= 0:
            return

        with self.model.green_lock:
            available = [w for w in self.model.unassigned_green_wastes
                         if w in self.model.seen_wastes]
            if not available:
                return
            if self.heuristic == "closest":
                available = self.sort_by_closest(available)
            elif self.heuristic == "farthest":
                available = self.sort_by_farthest(available)
            elif self.heuristic == "min_total_distance":
                tgt = ((self.model.width // 3) - 1, self.pos[1])
                available = self.sort_by_min_total_distance(available, tgt)

            for w in available[:need]:
                self.assigned_wastes.add(w)
                self.model.unassigned_green_wastes.remove(w)

    def step(self):
        # ── perception ───────────────────────────────────────
        self._update_seen_wastes()

        # ── 1. combine greens → yellow ───────────────────────
        if self.carrying.count("green") == 2:
            self.carrying = ["yellow"]
            self._reset_handshake()
            return

        # ── 2. deliver yellow → drop + spawn new waste ───────
        if "yellow" in self.carrying:
            delivery_x = (self.model.width // 3) - 1
            if self.pos[0] < delivery_x:
                self.model.grid.move_agent(self, self.move_towards((delivery_x, self.pos[1])))
            else:
                # drop and enqueue
                self.carrying.remove("yellow")
                from objects import WasteAgent
                new_w = WasteAgent(self.model, 'yellow', self.pos)
                self.model.grid.place_agent(new_w, self.pos)
                self.model.custom_agents.append(new_w)
                with self.model.yellow_lock:
                    self.model.unassigned_yellow_wastes.add(new_w)
                self._reset_handshake()
            return

        # ── 3. incoming transfer? ────────────────────────────
        for msg in self._inbox(lambda m: m.get("type")=="transfer"
                               and m["to"]==self.unique_id):
            self.carrying.extend(msg["items"])
            self._reset_handshake()
            return

        # ── 4. accept incoming offer ─────────────────────────
        if self.carrying==["green"] and not self.offer_active and not self.partner_id:
            offers = self._inbox(lambda m: m.get("type")=="offer"
                                 and m.get("waste_type")=="green")
            if offers:
                o = offers[0]
                self.partner_id = o["from"]
                # reply with ACCEPT + our pos
                self._send({
                    "type": "accept",
                    "from": self.unique_id,
                    "to":   self.partner_id,
                    "pos":  self.pos
                })
                # compute midpoint and lock
                self._compute_midpoint(o["pos"])
                self.offer_active = True
                return

        # ── 5. handle accept of my offer ─────────────────────
        if self.offer_active and not self.partner_id:
            acc = self._inbox(lambda m: m.get("type")=="accept"
                              and m.get("to")==self.unique_id)
            if acc:
                a = acc[0]
                self.partner_id = a["from"]
                self._compute_midpoint(a["pos"])
                return
            # timeout un­answered offer → reset
            self._reset_handshake()

        # ── 6. broadcast offer if holding one green ──────────
        if self.carrying==["green"] and not self.offer_active and not self.partner_id:
            # only if no other seen wastes to pick
            visible = [w for w in self.model.unassigned_green_wastes
                       if w in self.model.seen_wastes]
            if not visible and len(self.assigned_wastes) == 0:
                self.offer_active = True
                self._send({
                    "type":       "offer",
                    "from":       self.unique_id,
                    "waste_type": "green",
                    "pos":        self.pos
                })
                return

        # ── 7. move to rendezvous + transfer ───────────────────
        if self.offer_active and self.partner_id and self.rendezvous_pos:
            if self.pos != self.rendezvous_pos:
                self.model.grid.move_agent(self, self.move_towards(self.rendezvous_pos))
            else:
                # transfer and clear
                self._send({
                    "type":  "transfer",
                    "from":  self.unique_id,
                    "to":    self.partner_id,
                    "items": self.carrying.copy()
                })
                self.carrying.clear()
                self._reset_handshake()
            return

        # ── 8. normal hunt / scout ───────────────────────────
        self.assign_wastes()
        n = self.carrying.count("green")
        if n < 2:
            tgt = self.get_closest_assigned_waste("green")
            if tgt:
                if self.heuristic=="astar":
                    self.follow_path(self.astar_path(self.pos, tgt.pos))
                else:
                    self.model.grid.move_agent(self, self.move_towards(tgt.pos))
                self.pick_up_if_present("green")
            else:
                if n==0:
                    self._scout_step()
        return

class YellowRobotAgent(BaseRobot):
    def __init__(self, model, heuristic="closest"):
        super().__init__(model, heuristic)
        # hand‑off protocol state
        self.partner_id      = None
        self.offer_active    = False
        self.rendezvous_pos  = None

    def allowed_zones(self):
        return ['z1', 'z2']

    def _compute_midpoint(self, other_pos):
        mx = (self.pos[0] + other_pos[0]) // 2
        my = (self.pos[1] + other_pos[1]) // 2
        self.rendezvous_pos = (mx, my)

    def _reset_handshake(self):
        self.partner_id     = None
        self.offer_active   = False
        self.rendezvous_pos = None

    def assign_wastes(self):
        need = 2 - self.carrying.count("yellow") \
               - sum(1 for w in self.assigned_wastes if w.waste_type == "yellow")
        if need <= 0:
            return

        with self.model.yellow_lock:
            available = [w for w in self.model.unassigned_yellow_wastes
                         if w in self.model.seen_wastes]
            if not available:
                return

            if self.heuristic == "closest":
                available = self.sort_by_closest(available)
            elif self.heuristic == "farthest":
                available = self.sort_by_farthest(available)
            elif self.heuristic == "min_total_distance":
                tgt = ((2 * self.model.width // 3) - 1, self.pos[1])
                available = self.sort_by_min_total_distance(available, tgt)

            for w in available[:need]:
                self.assigned_wastes.add(w)
                self.model.unassigned_yellow_wastes.remove(w)

    def step(self):
        # ── perception ───────────────────────────────────────
        self._update_seen_wastes()

        # ── 1. combine yellows → red ─────────────────────────
        if self.carrying.count("yellow") == 2:
            self.carrying = ["red"]
            self._reset_handshake()
            return

        # ── 2. deliver red → drop + enqueue new red waste ────
        if "red" in self.carrying:
            delivery_x = (2 * self.model.width // 3) - 1
            if self.pos[0] < delivery_x:
                if self.heuristic == "astar":
                    self.follow_path(self.astar_path(self.pos, (delivery_x, self.pos[1])))
                else:
                    self.model.grid.move_agent(self, self.move_towards((delivery_x, self.pos[1])))
            else:
                # drop and re‑add as red waste
                self.carrying.remove("red")
                from objects import WasteAgent
                new_w = WasteAgent(self.model, 'red', self.pos)
                self.model.grid.place_agent(new_w, self.pos)
                self.model.custom_agents.append(new_w)
                with self.model.red_lock:
                    self.model.unassigned_red_wastes.add(new_w)
                self._reset_handshake()
            return

        # ── 3. incoming transfer? ────────────────────────────
        for msg in self._inbox(lambda m: m.get("type") == "transfer"
                               and m["to"] == self.unique_id):
            self.carrying.extend(msg["items"])
            self._reset_handshake()
            return

        # ── 4. accept incoming offer ─────────────────────────
        if self.carrying == ["yellow"] and not self.offer_active and not self.partner_id:
            offers = self._inbox(lambda m: m.get("type") == "offer"
                                 and m.get("waste_type") == "yellow")
            if offers:
                o = offers[0]
                self.partner_id = o["from"]
                # reply with ACCEPT + our pos
                self._send({
                    "type": "accept",
                    "from": self.unique_id,
                    "to":   self.partner_id,
                    "pos":  self.pos
                })
                # compute midpoint and lock
                self._compute_midpoint(o["pos"])
                self.offer_active = True
                return

        # ── 5. handle accept of my offer ─────────────────────
        if self.offer_active and not self.partner_id:
            acc = self._inbox(lambda m: m.get("type") == "accept"
                              and m.get("to") == self.unique_id)
            if acc:
                a = acc[0]
                self.partner_id = a["from"]
                self._compute_midpoint(a["pos"])
                return
            # timeout unanswered offer → reset
            self._reset_handshake()

        # ── 6. broadcast offer if holding one yellow ─────────
        if self.carrying == ["yellow"] and not self.offer_active and not self.partner_id:
            # only if no other seen wastes to pick
            visible = [w for w in self.model.unassigned_yellow_wastes
                       if w in self.model.seen_wastes]
            if not visible and len(self.assigned_wastes) == 0:
                self.offer_active = True
                self._send({
                    "type":       "offer",
                    "from":       self.unique_id,
                    "waste_type": "yellow",
                    "pos":        self.pos
                })
                return

        # ── 7. move to rendezvous + transfer ───────────────────
        if self.offer_active and self.partner_id and self.rendezvous_pos:
            if self.pos != self.rendezvous_pos:
                self.model.grid.move_agent(self, self.move_towards(self.rendezvous_pos))
            else:
                # transfer and clear
                self._send({
                    "type":  "transfer",
                    "from":  self.unique_id,
                    "to":    self.partner_id,
                    "items": self.carrying.copy()
                })
                self.carrying.clear()
                self._reset_handshake()
            return

        # ── 8. normal hunt / scout ───────────────────────────
        self.assign_wastes()
        n = self.carrying.count("yellow")
        if n < 2:
            tgt = self.get_closest_assigned_waste("yellow")
            if tgt:
                if self.heuristic == "astar":
                    self.follow_path(self.astar_path(self.pos, tgt.pos))
                else:
                    self.model.grid.move_agent(self, self.move_towards(tgt.pos))
                self.pick_up_if_present("yellow")
            else:
                if n == 0:
                    self._scout_step()
        return

class RedRobotAgent(BaseRobot):
    def allowed_zones(self):
        return ['z1', 'z2', 'z3']

    def assign_wastes(self):
        # need only one red bag in total
        need = 1 - self.carrying.count("red") \
                - sum(1 for w in self.assigned_wastes if w.waste_type == "red")
        if need <= 0:
            return

        with self.model.red_lock:
            available = [w for w in self.model.unassigned_red_wastes
                        if w in self.model.seen_wastes]

            if not available:
                return

            if self.heuristic == "closest":
                available = self.sort_by_closest(available)
            elif self.heuristic == "farthest":
                available = self.sort_by_farthest(available)
            elif self.heuristic == "min_total_distance":
                tgt = self.model.waste_disposal.pos   
                available = self.sort_by_min_total_distance(available, tgt)

            # for red robots we only ever need one bag
            picked = available[0]
            self.assigned_wastes.add(picked)
            self.model.unassigned_red_wastes.remove(picked)

    def step(self):
        self._update_seen_wastes()
        self.assign_wastes()
        if "red" in self.carrying:
            disposal_pos = self.model.waste_disposal.pos
            if self.pos == disposal_pos:
                #print(f"    [Red] At disposal cell {self.pos}, dropping red waste.")
                self.carrying.remove("red")
                # Increase the delivered waste counter.
                self.model.waste_delivered_count += 1
            else:
                if self.heuristic == "astar":
                    path = self.astar_path(self.pos, disposal_pos)
                    new_pos = self.follow_path(path)
                else:
                    new_pos = self.move_towards(disposal_pos)
                    if new_pos != self.pos:
                        self.model.grid.move_agent(self, new_pos)
                        self.distance_traveled += 1
                #print(f"    [Red] Moving toward disposal at {disposal_pos}, new position {new_pos}")
            return

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
                    self.distance_traveled += 1
            #print(f"    [Red] Moving toward assigned red waste at {target}, new position {new_pos}")
            self.pick_up_if_present("red")
        else:
            self._scout_step()
        return
