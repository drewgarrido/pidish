import time

is_running = True

SERVER_CONN = None

def run(conn):
    global is_running
    global SERVER_CONN

    is_running = True
    SERVER_CONN = conn

    update_status("Ready", "")

    while is_running:
        if SERVER_CONN.poll():
            command_list = SERVER_CONN.recv()
            command = command_list.pop("command").replace('+','_').lower()
            if len(command_list) > 0:
                eval(command + "(command_list)")
            else:
                eval(command + "()")
            update_status("Ready","")
        time.sleep(0.5)

def lift_move(args):
    update_status("Lift moving %s" % (args['dir']), "%d microns at %d microns/s" % (int(args['amount']),int(args['speed'])))
    amount = float(args['amount'])
    if args['dir'] == "Up":
        amount = -amount
    time.sleep(5.0)

def blank():
    update_status("Blank","")
    time.sleep(5.0)

def focus():
    update_status("Focus","")
    time.sleep(5.0)

def home():
    update_status("Home","")
    time.sleep(5.0)

def update_status(title_stat, sub_stat):
    print title_stat, sub_stat
    SERVER_CONN.send([title_stat, sub_stat])

def shutdown():
    global is_running
    is_running = False
