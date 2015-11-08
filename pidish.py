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
Usage:      sudo python pidish.py object_dir

    object_dir  Directory path with slice images

Ensure the lift is in the home position (the top) before running.

"""

OBJECT_PATH = None
GCODE_FILE = None
SLICE_PREFIX = None
CALIBRATE = False
SUPERCALI = False
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
Z_DISTANCE_PER_STEP     = 0.439453125 # microns
LIFT_LENGTH             = 103000    # microns
OPTIMUM_LIFT_SPEED      = 5280      # microns/s

# Resin vat maintenance
RESIN_TOP               = 25400     # microns
LIFT_PLATE_THICKNESS    = 5000      # microns

# Dip controls
DIP_DISTANCE            = 3000      # microns
DIP_WAIT                = 2.0       # seconds
DIP_SPEED_DOWN          = 1000       # microns/s
DIP_SPEED_UP            = DIP_SPEED_DOWN                # microns/s
RESIN_SETTLE            = 8.0       # seconds

SLOW_DIP_SPEED          = 20        # microns/s
SLOW_DIP_DIST           = 1000      # microns

# Exposure controls
SLICE_DISPLAY_TIME      = 18.0      # seconds
SLICE_THICKNESS         = 100       # microns

FIRST_SLICE_TIME        = 55.0      # seconds
FIRST_SLICE_NUM         = 3
FIRST_SLICE_THICKNESS   = SLICE_THICKNESS               # microns

SLICE_DIRECTIONS        = [
    #slice              method      display_time
    [0,                 "cont",     FIRST_SLICE_TIME    ],
    [FIRST_SLICE_NUM,   "cont",     SLICE_DISPLAY_TIME  ],
    [40,                "dip",      SLICE_DISPLAY_TIME  ],
]

# Calibration controls
CALIBRATE_MIN_TIME      = 7.0       # seconds
CALIBRATE_TIME_DELTA    = 0.5       # seconds
CALIBRATE_HEIGHT        = 5000      # microns

SUPERCALI_MIN_TIME      = 7.0       # seconds
SUPERCALI_TIME_DELTA    = 1.5       # seconds
SUPERCALI_BASE_HEIGHT   = 0000      # microns
SUPERCALI_POST_HEIGHT   = 5000      # microns


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
    lift.move_to(RESIN_TOP+DIP_DISTANCE, DIP_SPEED_DOWN)
    time.sleep(DIP_WAIT)
    lift.move_to(RESIN_TOP, DIP_SPEED_UP)

    print("Pop any bubbles that formed. Handle water spots.")
    adjust = 1
    while adjust != '':
        adjust = raw_input("Microns to adjust, or enter to start print: ")
        if adjust != '':
            lift.move_microns(int(adjust), DIP_SPEED_DOWN)


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
#   Expands SLICE_DIRECTIONS to give explicit directions per slice, as
#   SLICE_DIRECTIONS implies the same parameters are used between slices
#
#   @return tuple with directions for every slice
##
###############################################################################
def expand_slice_directions():
    global SLICE_DIRECTIONS

    step = 0
    slice_stats = []

    for i in xrange(NUM_SLICES):
        if step < len(SLICE_DIRECTIONS)-1:
            if i == SLICE_DIRECTIONS[step + 1][0]:
                step = step + 1

        slice_stats.append(SLICE_DIRECTIONS[step][1:])

    return slice_stats

###############################################################################
##
#   Calibration function of the printer
##
###############################################################################
def calibrate():
    display = projector()
    lift = BED_servo(Z_DISTANCE_PER_STEP)

    try:
        setup_resin(display, lift)
        start_time = time.time()

        for i in xrange(NUM_SLICES):
            display_status(start_time,i)

            lift.move_microns(DIP_DISTANCE, DIP_SPEED_DOWN)
            time.sleep(DIP_WAIT)
            lift.move_microns(-DIP_DISTANCE+SLICE_THICKNESS, DIP_SPEED_UP)
            time.sleep(RESIN_SETTLE)

            display.display(SLICE_PREFIX+"0000.png")

            if i < FIRST_SLICE_NUM:
                time.sleep(FIRST_SLICE_TIME)
            else:
                time.sleep(CALIBRATE_MIN_TIME)

                for j in xrange(1,9):
                    display.display(SLICE_PREFIX+"{:04d}.png".format(j))
                    time.sleep(CALIBRATE_TIME_DELTA)

            display.black()

        print "Print completed in " + time.strftime('%H:%M:%S', time.gmtime(time.time()-start_time))

    except:
        traceback.print_exception(*sys.exc_info())

    lift.home(OPTIMUM_LIFT_SPEED)
    lift.shutdown()
    display.shutdown()

###############################################################################
##
#   Super calibration function of the printer
##
###############################################################################
def supercali():
    display = projector()
    lift = BED_servo(Z_DISTANCE_PER_STEP)

    try:
        setup_resin(display, lift)
        start_time = time.time()

        base_num_slices = (SUPERCALI_BASE_HEIGHT-FIRST_SLICE_THICKNESS)/SLICE_THICKNESS + 1
        base_num_slices = 0

        #~ for i in xrange(base_num_slices):
            #~ display_status(start_time,i)

            #~ if i < FIRST_SLICE_NUM:
                #~ thickness = FIRST_SLICE_THICKNESS
                #~ display_time = FIRST_SLICE_TIME
            #~ else:
                #~ thickness = SLICE_THICKNESS
                #~ display_time = SLICE_DISPLAY_TIME

            #~ if i == FIRST_SLICE_NUM:
                #~ dip_speed = 100
            #~ else:
                #~ dip_speed = DIP_SPEED_DOWN

            #~ lift.move_microns(DIP_DISTANCE, dip_speed)
            #~ time.sleep(DIP_WAIT)
            #~ lift.move_microns(-DIP_DISTANCE+thickness, DIP_SPEED_UP)
            #~ time.sleep(RESIN_SETTLE)

            #~ display.display(SLICE_PREFIX+"base.png")
            #~ time.sleep(display_time)

            #~ display.black()

        post_num_slices = SUPERCALI_POST_HEIGHT/SLICE_THICKNESS

        for i in xrange(post_num_slices):
            display_status(start_time,i+base_num_slices)

            lift.move_microns(DIP_DISTANCE, DIP_SPEED_DOWN)
            time.sleep(DIP_WAIT)
            lift.move_microns(-DIP_DISTANCE+SLICE_THICKNESS, DIP_SPEED_UP)
            time.sleep(RESIN_SETTLE)

            display.display(SLICE_PREFIX+"0000.png")

            time.sleep(SUPERCALI_MIN_TIME)

            for j in xrange(1,9):
                display.display(SLICE_PREFIX+"{:04d}.png".format(j))
                time.sleep(SUPERCALI_TIME_DELTA)

            display.black()

        print "Print completed in " + time.strftime('%H:%M:%S', time.gmtime(time.time()-start_time))

    except:
        traceback.print_exception(*sys.exc_info())

    lift.home(OPTIMUM_LIFT_SPEED)
    lift.shutdown()
    display.shutdown()

###############################################################################
##
#   Prints an object
##
###############################################################################
def print_object():
    display = projector()
    lift = BED_servo(Z_DISTANCE_PER_STEP)

    try:
        slice_stats = expand_slice_directions()

        setup_resin(display, lift)
        start_time = time.time()

        for i in xrange(NUM_SLICES):

            display_status(start_time, i)

            method, display_time = slice_stats[i]

            slice_image = SLICE_PREFIX+"{:04d}.png".format(i)

            if method == "dip":

                display.black()

                lift.move_microns(DIP_DISTANCE, DIP_SPEED_DOWN)
                time.sleep(DIP_WAIT)
                lift.move_microns(-DIP_DISTANCE+SLICE_THICKNESS, DIP_SPEED_UP)

                time.sleep(RESIN_SETTLE)

                display.display(slice_image)
                time.sleep(display_time)

            elif method == "cont":
                display.display(slice_image)
                lift.move_microns(SLICE_THICKNESS, SLICE_THICKNESS / display_time)

            elif method == "bottom":
                display.display(slice_image)
                time.sleep(display_time)

            elif method == "slow dip":
                display.black()

                lift.move_microns(SLOW_DIP_DIST, SLOW_DIP_SPEED)
                time.sleep(DIP_WAIT)
                lift.move_microns(-SLOW_DIP_DIST+SLICE_THICKNESS, SLOW_DIP_SPEED)

                time.sleep(RESIN_SETTLE)

                display.display(slice_image)
                time.sleep(display_time)


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
    global CALIBRATE
    global SUPERCALI
    global NUM_SLICES

    for arg in arguments[1:]:
        if arg == "calibrate":
            CALIBRATE = True
        if arg == "supercali":
            SUPERCALI = True
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

    if CALIBRATE:
        NUM_SLICES = CALIBRATE_HEIGHT/SLICE_THICKNESS

    if SUPERCALI:
        NUM_SLICES = (SUPERCALI_BASE_HEIGHT - FIRST_SLICE_THICKNESS + SUPERCALI_POST_HEIGHT) / SLICE_THICKNESS + 1


if __name__ == '__main__':
    process_arguments(sys.argv)
    if CALIBRATE:
        calibrate()
    elif SUPERCALI:
        supercali()
    else:
        print_object()
