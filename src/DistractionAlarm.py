import carla
import pygame

"""
A class for alarms that can have both sound and visual HMI elements
"""
class Alarm():
    def __init__(self, client, vehicle, icon, icon_location, alarm_type="baseline", escalation_levels=0, sound_paths=[]):
        self.client = client
        self.world = client.get_world()
        self.vehicle = vehicle

        self.alarm_type = alarm_type
        self.levels = escalation_levels
        assert self.alarm_type not in ['escalating', 'non-escalating'] or len(sound_paths) == self.levels + 1, "Check that paths list has one entry per escalation level." 

        self.current_alarm = None

        self.icon = icon
        self.icon_location = icon_location
        self.icon_list = []

        if self.alarm_type in ['escalating', 'non-escalating']:
            pygame.mixer.init()  # Initialize the mixer module (for playing sounds)
            self.sound_library = [pygame.mixer.Sound(p) for p in sound_paths]

        self.is_level=None

    def play(self, level=0):
        # The baseline for this experiment has no alarm
        if self.alarm_type in ['escalating', 'non-escalating']:
            self.current_alarm = self.sound_library[level]
            # play the alarm sound file
            self.current_alarm.play()
            # and display the visual icon
            self.spawned_icon = self.world.spawn_actor(self.icon, self.icon_location, attach_to=self.vehicle)
            self.icon_list.append(self.spawned_icon)
            self.is_level = level

    def stop(self):
        if self.current_alarm is not None and self.alarm_type in ['escalating', 'non-escalating']:
            # stop the sound
            self.current_alarm.stop()
            # undisplay the alarm icon
            self.client.apply_batch([carla.command.DestroyActor(x) for x in self.icon_list])
        self.current_alarm = None
        self.is_level = None

