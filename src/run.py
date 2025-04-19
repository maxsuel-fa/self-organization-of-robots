"""
File: run.py
Group: 5 
Date of creation: 25/03/2024
Brief: Implements the run object
Authors: Mateus Goto, Maxsuel Fernandes, João Pedro Regazzi
"""

from model import RobotMission

if __name__ == '__main__':
    width = 30
    height = 30
    num_green = 5
    num_yellow = 3
    num_red = 2
    num_green_waste = 1
    num_yellow_waste = 0
    num_red_waste = 2
    heuristic = "astar"

    model = RobotMission(width, height, num_green, num_yellow, num_red,
                         num_green_waste, num_yellow_waste, num_red_waste, heuristic=heuristic)
    
    MAX_STEPS = 10_000
    while not model.finished and model.step_count < MAX_STEPS:
        model.step()