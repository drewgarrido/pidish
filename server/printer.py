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

import os, time, sys, inspect, traceback, re

###############################################################################
#
#   Set server_test to True if running on a PC without the RPi
#
###############################################################################
SERVER_TEST = False

if SERVER_TEST:
    from servo_test import BED_servo
    from projector_test import projector
else:
    from servo import BED_servo
    from projector import projector

# CONSTANTS ####################################################################

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
DIP_SPEED_DOWN          = 1000       # microns/s
DIP_SPEED_UP            = DIP_SPEED_DOWN                # microns/s

if SERVER_TEST:
    DIP_WAIT            = 0.25
    RESIN_SETTLE        = 0.25
else:
    DIP_WAIT            = 2.0       # seconds
    RESIN_SETTLE        = 8.0       # seconds

SLOW_DIP_SPEED          = 20        # microns/s
SLOW_DIP_DIST           = 1000      # microns

# Exposure controls
SLICE_DISPLAY_TIME      = 18.0      # seconds
SLICE_THICKNESS         = 100       # microns

FIRST_SLICE_TIME_FACTOR = 2.5       # multiplier of slice display time
FIRST_SLICE_THICKNESS   = SLICE_THICKNESS               # microns

SLICE_DIRECTIONS        = [
    #slice              method      display_time_factor
    [0,                 "dip",      FIRST_SLICE_TIME_FACTOR     ],
    [3,                 "dip",      1.0                         ],
]



## GLOBALS #####################################################################

IS_RUNNING = True
ABORT_PRINT = False
SERVER_CONN = None

DISPLAY = projector()
LIFT = BED_servo(Z_DISTANCE_PER_STEP)


def run(conn):
    global IS_RUNNING
    global SERVER_CONN

    IS_RUNNING = True
    SERVER_CONN = conn

    # Keep the servo running cool
    LIFT.off()

    module_functions = {}
    items = inspect.getmembers(sys.modules[__name__], inspect.isfunction)
    for item in items:
        module_functions[item[0]]=item[1]

    update_status("Ready", "")

    try:
        while IS_RUNNING:
            if SERVER_CONN.poll():
                command_list = SERVER_CONN.recv()
                command = command_list.pop("command").replace('+','_').lower()
                if command in module_functions:
                    if len(command_list) > 0:
                        module_functions[command](command_list)
                    else:
                        module_functions[command]()
                update_status("Ready","")
            time.sleep(0.5)
    except:
        shutdown()
        SERVER_CONN.send(["SHUTDOWN", None])

def lift_move(args):
    update_status("Lift moving %s" % (args['dir']), "%d microns at %d microns/s" % (int(args['lift_amount']),int(args['lift_speed'])))

    LIFT.on()

    amount = float(args['lift_amount'])
    if args['dir'] == "Up":
        amount = -amount
    LIFT.move_microns(amount, float(args['lift_speed']))

    LIFT.off()

def blank():
    DISPLAY.black()

def focus():
    DISPLAY.display('focus1024.png')

def home():
    update_status("Home","")
    LIFT.on()
    LIFT.home(OPTIMUM_LIFT_SPEED)
    LIFT.off()

def reset_zero():
    LIFT.reset_home()

def print_object(args):
    global ABORT_PRINT
    num_slices = 0

    ABORT_PRINT = False
    update_status("Printing", "Starting " + args['object_path'])

    try:
        # Path not passed correctly
        if os.path.isdir(args['object_path']):
            object_path = args['object_path']
        else:
            return
            
        exposure_time = float(args['exposure_time'])

        # Look for slices
        for objs in os.listdir(object_path):
            total_path = object_path+"/"+objs

            slice_match = re.match("(.+?)[0-9]+\.png", total_path)
            if slice_match:
                num_slices += 1
                slice_prefix = slice_match.group(1)

        if not slice_prefix:
            print "Missing slices!"
            exit()

        print "Image path prefix: " + slice_prefix
        print "Found {:d} slice images.".format(num_slices)

        LIFT.on()

        slice_stats = expand_slice_directions(num_slices)
        start_time = time.time()

        layer = 0
        while layer < num_slices and ABORT_PRINT == False:

            # Update status
            if (layer > 0):
                delta = time.time() - start_time
                time_remain = ((num_slices+0.0)/layer - 1.0)*(delta)
                time_remain_str = time.strftime('%H:%M:%S', time.gmtime(time_remain))
                update_status("Printing", "{:s}<br>Layer {:d} of {:d}. {:s} Remaining.".format(object_path, layer, num_slices, time_remain_str))

            method, display_time_factor = slice_stats[layer]
            display_time = display_time_factor * exposure_time

            slice_image = slice_prefix+"{:04d}.png".format(layer)

            if method == "dip":

                DISPLAY.black()

                LIFT.move_microns(DIP_DISTANCE, DIP_SPEED_DOWN)
                time.sleep(DIP_WAIT)
                LIFT.move_microns(-DIP_DISTANCE+SLICE_THICKNESS, DIP_SPEED_UP)

                time.sleep(RESIN_SETTLE)

                DISPLAY.display(slice_image)
                time.sleep(display_time)

            elif method == "cont":
                DISPLAY.display(slice_image)
                LIFT.move_microns(SLICE_THICKNESS, SLICE_THICKNESS / display_time)

            elif method == "bottom":
                DISPLAY.display(slice_image)
                time.sleep(display_time)

            elif method == "slow dip":
                DISPLAY.black()

                LIFT.move_microns(SLOW_DIP_DIST, SLOW_DIP_SPEED)
                time.sleep(DIP_WAIT)
                LIFT.move_microns(-SLOW_DIP_DIST+SLICE_THICKNESS, SLOW_DIP_SPEED)

                time.sleep(RESIN_SETTLE)

                DISPLAY.display(slice_image)
                time.sleep(display_time)

            poll_server_command(args)
            layer += 1

        print "Print completed in " + time.strftime('%H:%M:%S', time.gmtime(time.time()-start_time))
    except:
        traceback.print_exception(*sys.exc_info())
        shutdown()
        SERVER_CONN.send(["SHUTDOWN", None])
    finally:
        # End must also work for abort case
        DISPLAY.black()
        LIFT.home(OPTIMUM_LIFT_SPEED)
        LIFT.off()




def poll_server_command(args):
    global ABORT_PRINT
    if SERVER_CONN.poll():
        command_list = SERVER_CONN.recv()
        if command_list['command']=="Abort":
            ABORT_PRINT = True
            return
        elif command_list['command']=="Pause":
            DISPLAY.black()
            update_status("Paused",args['object_path'])
            while True:
                time.sleep(0.5)
                if SERVER_CONN.poll():
                    command_list = SERVER_CONN.recv()
                    if command_list['command']=="Abort":
                        ABORT_PRINT = True
                        return
                    elif command_list['command']=="Unpause":
                        return



def calibration(args):
    global ABORT_PRINT
    num_slices = 0

    ABORT_PRINT = False
    update_status("Calibrating", "Starting...")

    try:
        args['object_path'] = "Calibration"
        object_path = os.getcwd() + '/calibrate'
        slice_prefix = object_path + '/calibrate'
        num_slices = 5000 / SLICE_THICKNESS    # 5 mm
        cali_min_time = float(args['cali_min_time'])
        cali_max_time = float(args['cali_max_time'])
        cali_time_delta = (cali_max_time - cali_min_time) / 8.0

        LIFT.on()

        start_time = time.time()

        layer = 0
        while layer < num_slices and ABORT_PRINT == False:

            # Update status
            if (layer > 0):
                delta = time.time() - start_time
                time_remain = ((num_slices+0.0)/layer - 1.0)*(delta)
                time_remain_str = time.strftime('%H:%M:%S', time.gmtime(time_remain))
                update_status("Calibrating", "{:s}<br>Layer {:d} of {:d}. {:s} Remaining.".format(object_path, layer, num_slices, time_remain_str))

            LIFT.move_microns(DIP_DISTANCE, DIP_SPEED_DOWN)
            time.sleep(DIP_WAIT)
            LIFT.move_microns(-DIP_DISTANCE+SLICE_THICKNESS, DIP_SPEED_UP)
            time.sleep(RESIN_SETTLE)

            DISPLAY.display(slice_prefix+"0000.png")

            if layer < 3:
                time.sleep(cali_min_time * FIRST_SLICE_TIME_FACTOR)
            else:
                time.sleep(cali_min_time)

            for j in xrange(1,9):
                DISPLAY.display(slice_prefix+"{:04d}.png".format(j))
                if layer < 3:
                    time.sleep(cali_time_delta * FIRST_SLICE_TIME_FACTOR)
                else:
                    time.sleep(cali_time_delta)

            DISPLAY.black()

            poll_server_command(args)
            layer += 1

        print "Completed in " + time.strftime('%H:%M:%S', time.gmtime(time.time()-start_time))
    except:
        traceback.print_exception(*sys.exc_info())
        shutdown()
        SERVER_CONN.send(["SHUTDOWN", None])
    finally:
        # End must also work for abort case
        DISPLAY.black()
        LIFT.home(OPTIMUM_LIFT_SPEED)
        LIFT.off()


###############################################################################
##
#   Expands SLICE_DIRECTIONS to give explicit directions per slice, as
#   SLICE_DIRECTIONS implies the same parameters are used between slices
#
#   @return tuple with directions for every slice
##
###############################################################################
def expand_slice_directions(num_slices):
    global SLICE_DIRECTIONS

    step = 0
    slice_stats = []

    for i in xrange(num_slices):
        if step < len(SLICE_DIRECTIONS)-1:
            if i == SLICE_DIRECTIONS[step + 1][0]:
                step = step + 1

        slice_stats.append(SLICE_DIRECTIONS[step][1:])

    return slice_stats


def update_status(title_stat, sub_stat):
    print title_stat, sub_stat
    SERVER_CONN.send([title_stat, sub_stat])

def shutdown():
    global IS_RUNNING
    if IS_RUNNING:
        LIFT.shutdown()
        DISPLAY.shutdown()
    IS_RUNNING = False
