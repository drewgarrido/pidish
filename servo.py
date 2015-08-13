# Copyright (C) 2015  Drew Garrido
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import RPi.GPIO as GPIO
from math import pi
import time

FULL_STEP      = [False, False, False, 1]
HALF_STEP      = [True,  False, False, 2]
QUARTER_STEP   = [False, True,  False, 4]
EIGHTH_STEP    = [True,  True,  False, 8]
SIXTEENTH_STEP = [True,  True,  True , 16]

class BED_servo:
    ###########################################################################
    ##
    #   Servo control is always through a GPIO pin.  This needs to be assigned
    #   at initialization.
    #
    #   @param  pin     Board GPIO pin servo is connected to.
    ##
    ###########################################################################
    def __init__(self,  microns_per_step = 0.44,
                        enable_pin = 40,
                        ms1_pin = 38,
                        ms2_pin = 37,
                        ms3_pin = 36,
                        reset_pin = 35,
                        sleep_pin = 33,
                        step_pin = 32,
                        dir_pin = 31):


        self.enable_pin = enable_pin
        self.ms1_pin    = ms1_pin
        self.ms2_pin    = ms2_pin
        self.ms3_pin    = ms3_pin
        self.reset_pin  = reset_pin
        self.sleep_pin  = sleep_pin
        self.step_pin   = step_pin
        self.dir_pin    = dir_pin

        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.enable_pin, GPIO.OUT)
        GPIO.setup(self.ms1_pin, GPIO.OUT)
        GPIO.setup(self.ms2_pin, GPIO.OUT)
        GPIO.setup(self.ms3_pin, GPIO.OUT)
        GPIO.setup(self.reset_pin, GPIO.OUT)
        GPIO.setup(self.sleep_pin, GPIO.OUT)
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.setup(self.dir_pin, GPIO.OUT)

        # Set the step mode
        mode = SIXTEENTH_STEP
        GPIO.output(self.ms1_pin, mode[0])
        GPIO.output(self.ms2_pin, mode[1])
        GPIO.output(self.ms3_pin, mode[2])
        self.steps_per_revolution = mode[3] * 200
        self.microns_per_step = (microns_per_step * 16.0) / mode[3]

        # Default the motion control pins
        GPIO.output(self.step_pin, False)
        GPIO.output(self.dir_pin, False)

        # The control pins are negative logic
        GPIO.output(self.sleep_pin, True)
        GPIO.output(self.reset_pin, True)
        GPIO.output(self.enable_pin, False)

        self.reset()

        self.location = 0   # home position


    ###########################################################################
    ##
    #   Destructor that shuts down the GPIO module.
    ##
    ###########################################################################
    def shutdown(self):
        self.off()
        GPIO.cleanup()

    ###########################################################################
    ##
    #   Resets the Big Easy Driver
    ##
    ###########################################################################
    def reset(self):
        GPIO.output(self.reset_pin, False)
        time.sleep(0.25)
        GPIO.output(self.reset_pin, True)

    ###########################################################################
    ##
    #   Turns on the servo
    ##
    ###########################################################################
    def on(self):
        GPIO.output(self.sleep_pin, True)

        # Required time for charging the BED chip
        time.sleep(0.002)

    ###########################################################################
    ##
    #   Turns off the servo
    ##
    ###########################################################################
    def off(self):
        GPIO.output(self.sleep_pin, False)

    ###########################################################################
    ##
    #   Tells the servo to move a specified step count at a particular speed
    #
    #   @param  steps   Number of steps to move.  Negative rotates the opposite
    #                   direction.
    #   @param  speed   Rotation rate in steps per second. Defaults to 3200/sec.
    ##
    ###########################################################################
    def move(self, steps=3200, speed=3200):

        delta_location = 1

        # Pulses must be held up for at least a microsecond
        if (speed > 1000000):
            speed = 1000000

        time_offset = 0.5/speed

        if (steps < 0):
            GPIO.output(self.dir_pin, False)
            steps = -steps
            delta_location = -1
        else:
            GPIO.output(self.dir_pin, True)

        for _ in xrange(steps):

            GPIO.output(self.step_pin, True)
            end_time = time.time()+time_offset
            while (time.time() < end_time):
                pass

            self.location += delta_location

            GPIO.output(self.step_pin, False)
            end_time = time.time()+time_offset
            while (time.time() < end_time):
                pass

    ###########################################################################
    ##
    #   Moves the servo a relative amount.
    #
    #   @param  distance    Distance, in microns, to move
    #   @param  speed       Lift speed in microns per second
    ##
    ###########################################################################
    def move_microns(self, distance, speed):
        self.move(int(distance / self.microns_per_step), speed / self.microns_per_step)

    ###########################################################################
    ##
    #   Moves the servo to an absolute location.
    #
    #   @param  location    Location, in microns, to move to
    #   @param  speed       Lift speed in microns per second
    ##
    ###########################################################################
    def move_to(self, location, speed):
        steps = int(float(location) / self.microns_per_step) - self.location
        self.move(steps, speed / self.microns_per_step)

    ###########################################################################
    ##
    #   Returns the servo to the home location
    #
    #   @param  speed   Lift speed in microns per second
    ##
    ###########################################################################
    def home(self, speed):
        self.move(-self.location, speed / self.microns_per_step)

    ###########################################################################
    ##
    #   Returns the location of the servo in microns
    #
    #   @return location    in microns
    ##
    ###########################################################################
    def get_location_microns(self):
        return self.location * self.microns_per_step

    ###########################################################################
    ##
    #   Returns the angle of the servo in radians
    #
    #   @return angle   in radians
    ##
    ###########################################################################
    def get_angle(self):
        return ((self.location % self.steps_per_revolution) * pi) / self.steps_per_revolution
