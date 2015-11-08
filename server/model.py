from multiprocessing import Process, Pipe
import threading
import printer
import time

class model(threading.Thread):
    def __init__(self):
        super(model, self).__init__()
        self.running = True
        self.title_status = "Awaiting printer status"
        self.sub_status = ""

        self.printer_conn, child_conn = Pipe()
        self.printer_process = Process(target=printer.run, args=(child_conn,))
        self.printer_process.start()


    def run(self):
        try:
            while self.running:
                if self.printer_conn.poll():
                    self.title_status, self.sub_status = self.printer_conn.recv()
                time.sleep(0.5)
        except:
            pass
        printer.shutdown()
        self.printer_process.join()

    def get_sub_status(self):
        return self.sub_status

    def get_title_status(self):
        return self.title_status

    def send_command(self, command):
        self.printer_conn.send(command)

    def shutdown(self):
        self.running = False
