import time
from string import Template

INDEX_TEMPLATE = ""
STATUS_TEMPLATE = ""
SYNC_MODEL = None

def load(model):
    global INDEX_TEMPLATE
    global STATUS_TEMPLATE
    global SYNC_MODEL

    SYNC_MODEL = model

    f = open('index.htm')
    INDEX_TEMPLATE = Template(f.read())
    f.close()

    f = open('status.htm')
    STATUS_TEMPLATE = Template(f.read())
    f.close()

def index():
    page_temp = INDEX_TEMPLATE
    page = page_temp.safe_substitute()

    return page

def status():
    title_data = SYNC_MODEL.get_title_status()
    sub_data = SYNC_MODEL.get_sub_status()

    page_temp = STATUS_TEMPLATE
    page = page_temp.safe_substitute(title_status=title_data,
                                    sub_status=sub_data,
                                    curtime=time.strftime("%H:%M:%S"))

    return page
