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
    num_waste = 10

    model = RobotMission(width, height, num_green, num_yellow, num_red, num_waste)
    for i in range(100):
        model.step()