from agents.navigation import basic_agent

"""
Inherits CARLA basic agent and adds function to go to a specified destination
"""
class DReyeVRAgent(basic_agent.BasicAgent):
    def __init__(self, vehicle):
        super().__init__(vehicle)
        self.vehicle = vehicle

    def go_to(self, destination, target_speed, starting_point=None):
        """Makes the automated ego vehicle drive to the specified destination with the specified target speed."""
        self.target_speed = target_speed
        self.set_destination(destination, starting_point)
        print("going to {} with speed {}".format(destination, target_speed))