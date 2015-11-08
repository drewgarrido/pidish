
SYNC_MODEL = None

def load(model):
    global SYNC_MODEL
    SYNC_MODEL = model

def lift_move(args):
    print "Controller: Lift moving %s %d" % (args['dir'],int(args['amount']))
    amount = float(args['amount'])
    if args['dir'] == "Up":
        amount = -amount
    SYNC_MODEL.set_lift_move(amount)

def home():
    print "Controller: Lifting to home"
    SYNC_MODEL.set_home()

def blank():
    print "Controller: Blanking projector"
    SYNC_MODEL.set_blank()

def focus():
    print "Controller: Displaying focus"
    SYNC_MODEL.set_focus()
