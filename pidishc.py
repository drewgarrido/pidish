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

import os, sys, re, time, traceback

from servo import BED_servo
from projector import projector

usageStr = """
Usage:      sudo python pidishc.py object_dir

    object_dir  Directory path with slice images

Ensure the lift is in the home position (the top) before running.

"""

OBJECT_PATH = None
GCODE_FILE = None
SLICE_PREFIX = None
NUM_SLICES = 0

SERVO_ENABLE    = 40
SERVO_MS1       = 38
SERVO_MS2       = 37
SERVO_MS3       = 36
SERVO_RESET     = 35
SERVO_SLEEP     = 33
SERVO_STEP      = 32
SERVO_DIRECTION = 31

# Printer dimensions
Z_DISTANCE_PER_STEP     = 0.44      # microns
LIFT_LENGTH             = 103000    # microns
OPTIMUM_LIFT_SPEED      = 5280      # microns/s

# Resin vat maintenance
RESIN_TOP               = 25400     # microns
LIFT_PLATE_THICKNESS    = 5000      # microns

# Dip controls (Mostly setup_resin values)
DIP_DISTANCE            = 3000      # microns
DIP_WAIT                = 2.0       # seconds
DIP_SPEED               = 1000      # microns/s

# Exposure controls
SLICE_DISPLAY_TIME      = 1.5       # seconds
SLICE_THICKNESS         = 10        # microns
LIFT_SPEED              = SLICE_THICKNESS / SLICE_DISPLAY_TIME  # microns/sec

FIRST_SLICE_TIME        = 2.0       # seconds
FIRST_SLICE_NUM         = 10
FIRST_SLICE_THICKNESS   = SLICE_THICKNESS               # microns
FIRST_SLICE_LIFT_SPEED  = FIRST_SLICE_THICKNESS / FIRST_SLICE_TIME



###############################################################################
##
#   Sets up the printer to have the lift below the resin top without bubbles
#
#   @param  display     projector object
#   @param  lift        servo object
##
###############################################################################
def setup_resin(display, lift):

    display.black()

    # Quickly move to resin
    lift.move_to(RESIN_TOP-LIFT_PLATE_THICKNESS, OPTIMUM_LIFT_SPEED)

    # Slowly dip
    lift.move_to(RESIN_TOP+DIP_DISTANCE, DIP_SPEED)
    time.sleep(DIP_WAIT)
    lift.move_to(RESIN_TOP, DIP_SPEED)

    print("Pop any bubbles that formed. Handle water spots.")
    adjust = 1
    while adjust != '':
        adjust = raw_input("Microns to adjust, or enter to start print: ")
        if adjust != '':
            lift.move_microns(int(adjust), DIP_SPEED)


###############################################################################
##
#   Computes and displays the status of the printer
#
#   @param  start_time      Time at beginning of print
#   @param  current_slice   Current slice being cured
##
###############################################################################
def display_status(start_time, current_slice):
    if (current_slice > 0):
        delta = time.time() - start_time
        time_remain = ((NUM_SLICES+0.0)/current_slice - 1.0)*(delta)
        time_remain_str = time.strftime('%H:%M:%S', time.gmtime(time_remain))
        print "Layer {:d} of {:d}. {:s} Remaining.".format(current_slice, NUM_SLICES, time_remain_str)

###############################################################################
##
#   Prints an object
##
###############################################################################
def print_object():
    display = projector()
    lift = BED_servo(Z_DISTANCE_PER_STEP)

    try:
        setup_resin(display, lift)
        start_time = time.time()

        for i in xrange(NUM_SLICES):
            display_status(start_time, i)
            display.display(SLICE_PREFIX+"{:04d}.png".format(i))
            if i < FIRST_SLICE_NUM:
                lift.move_microns(SLICE_THICKNESS, FIRST_SLICE_LIFT_SPEED)
            else:
                lift.move_microns(SLICE_THICKNESS, LIFT_SPEED)

        print "Print completed in " + time.strftime('%H:%M:%S', time.gmtime(time.time()-start_time))
    except:
        traceback.print_exception(*sys.exc_info())

    display.black()
    lift.home(OPTIMUM_LIFT_SPEED)
    lift.shutdown()
    display.shutdown()

###############################################################################
##
#   Process arguments from the command line. Sets up global variables for the
#   script.
##
###############################################################################
def process_arguments(arguments):
    global OBJECT_PATH
    global GCODE_FILE
    global SLICE_PREFIX
    global NUM_SLICES

    for arg in arguments[1:]:
        if (os.path.isdir(arg)):
            OBJECT_PATH = os.path.abspath(arg)
        else:
            print(arg + " is not a directory!")
            exit()

    # Path not given
    if not OBJECT_PATH:
        print(usageStr)
        exit()

    # Look for slices
    for objs in os.listdir(OBJECT_PATH):
        total_path = OBJECT_PATH+"/"+objs

        slice_match = re.match("(.+?)[0-9]+\.png", total_path)
        if slice_match:
            NUM_SLICES += 1
            SLICE_PREFIX = slice_match.group(1)

    if not SLICE_PREFIX:
        print "Missing slices!"
        exit()

    print "Image path prefix: " + SLICE_PREFIX
    print "Found {:d} slice images.".format(NUM_SLICES)


if __name__ == '__main__':
    process_arguments(sys.argv)
    print_object()
