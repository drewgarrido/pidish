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

from multiprocessing import Process, Pipe
from subprocess import call
import threading
import printer
import time
import os
import re

class model(threading.Thread):
    def __init__(self):
        super(model, self).__init__()
        self.running = True
        self.title_status = "Awaiting printer status"
        self.sub_status = ""

        self.is_printing = False
        self.printer_received_cmd = False
        self.is_paused = False

        self.type_dict_regex = {
        "float":"([0-9]+\.?[0-9]+?)",
        "int":"([0-9]+)"
        }

        self.saved_variables = [
        ["lift_speed", 5280, "int"],
        ["lift_amount", 25400, "int"],
        ["cali_min_time", 6.0, "float"],
        ["cali_max_time", 17.0, "float"],
        ["exposure_time", 13.0, "float"],
        ]

        # default the variable values
        for some_var, default_val, var_type in self.saved_variables:
            exec("self."+some_var + "=" + str(default_val))

        self.load_printer_variables()

        self.object_paths = []
        self.refresh_list()

        self.printer_conn, child_conn = Pipe()
        self.printer_process = Process(target=printer.run, args=(child_conn,))
        self.printer_process.start()


    def run(self):
        try:
            while self.running:
                if self.printer_conn.poll():
                    self.title_status, self.sub_status = self.printer_conn.recv()
                if self.title_status == "SHUTDOWN":
                    self.shutdown()
                if self.title_status == "Ready" and self.printer_received_cmd:
                    self.is_printing = False
                if self.title_status != "Ready":
                    self.printer_received_cmd = True
                time.sleep(0.5)
        except:
            pass
        printer.shutdown()
        self.printer_process.join()

    def refresh_list(self):
        folder_listing = os.listdir(os.getcwd())

        self.object_paths = []

        for listing in folder_listing:
            if re.match(".+\.slice$",listing):
                self.object_paths.append(listing)

    def send_command(self, command):
        # Save any variables coming from the command
        for some_var, default_val, var_type in self.saved_variables:
            if some_var in command:
                if re.match(self.type_dict_regex[var_type]+"$", command[some_var]) != None:
                    exec("self.{0} = {1}(command['{0}'])".format(some_var,var_type))
                else:
                    # Argument is invalid, do not execute!
                    return
        
        self.save_printer_variables()

        if command["command"] == "calibration":
            self.is_printing = True
            self.printer_received_cmd = False

        if command["command"] == "print_object":
            command["object_path"] = os.getcwd() + '/' + command["object_path"]
            self.is_printing = True
            self.printer_received_cmd = False

        if command["command"] == "Pause":
            self.is_paused = True

        if command["command"] == "Unpause":
            self.is_paused = False

        if command["command"] == "Abort":
            self.is_printing = False
        
        if command["command"] == "refresh_list":
            self.refresh_list()
        elif command["command"] == ["upload"]:
            # command["object_name"] is a tuple?
            command["command"].pop()
            self.upload(command)
        else:
            self.printer_conn.send(command)

    def shutdown(self):
        self.save_printer_variables()
        self.is_printing = False
        self.running = False

    def upload(self, command):
        f = open("temp.zip",'w')
        f.write(command["datafile"][0])
        f.close()

        call(["unzip","-o","temp.zip"])

        call(["rm", "temp.zip"])

        self.refresh_list()

    def load_printer_variables(self):
        try:
            f = open('printer_variables.txt')
            all_var = f.read()
            f.close()
        except:
            return

        for some_var, default_val, var_type in self.saved_variables:
            match_type = some_var + ": " + self.type_dict_regex[var_type]
            check_search = re.search(match_type, all_var, re.MULTILINE)
            if check_search != None:
                exec("self.{0}={1}({2})".format(some_var, var_type, check_search.group(1)))

    def save_printer_variables(self):
        try:
            f = open('printer_variables.txt','w')
            for some_var, default_val, var_type in self.saved_variables:
                f.write("{0}: {1}\r\n".format(some_var, str(eval("self."+some_var))))
            f.close()
        except:
            pass
