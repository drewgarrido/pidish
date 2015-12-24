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

import time
from string import Template

INDEX_TEMPLATE = ""
INDEX_PRINTING_TEMPLATE = ""
INDEX_PAUSED_TEMPLATE = ""
STATUS_TEMPLATE = ""
SYNC_MODEL = None

def load(model):
    global INDEX_TEMPLATE
    global INDEX_PAUSED_TEMPLATE
    global INDEX_PRINTING_TEMPLATE
    global STATUS_TEMPLATE
    global SYNC_MODEL

    SYNC_MODEL = model

    f = open('index.htm')
    INDEX_TEMPLATE = Template(f.read())
    f.close()

    f = open('index_pause.htm')
    INDEX_PAUSED_TEMPLATE = Template(f.read())
    f.close()

    f = open('index_printing.htm')
    INDEX_PRINTING_TEMPLATE = Template(f.read())
    f.close()

    f = open('status.htm')
    STATUS_TEMPLATE = Template(f.read())
    f.close()

def index():

    if SYNC_MODEL.is_paused:
        page_temp = INDEX_PAUSED_TEMPLATE
        page = page_temp.safe_substitute()

    elif SYNC_MODEL.is_printing:
        page_temp = INDEX_PRINTING_TEMPLATE
        page = page_temp.safe_substitute()

    else:
        page_temp = INDEX_TEMPLATE

        temp_object_path_options = ""
        for p in SYNC_MODEL.object_paths:
            temp_object_path_options += "<option>" + p + "</option>"

        page = page_temp.safe_substitute(lift_amount=SYNC_MODEL.lift_amount,
                                         lift_speed=SYNC_MODEL.lift_speed,
                                         cali_min_time=SYNC_MODEL.cali_min_time,
                                         cali_max_time=SYNC_MODEL.cali_max_time,
                                         exposure_time=SYNC_MODEL.exposure_time,
                                         object_path_options=temp_object_path_options)

    return page

def status():
    page_temp = STATUS_TEMPLATE
    page = page_temp.safe_substitute(title_status=SYNC_MODEL.title_status,
                                     sub_status=SYNC_MODEL.sub_status,
                                     curtime=time.strftime("%H:%M:%S"))

    return page
