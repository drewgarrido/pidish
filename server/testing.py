from multiprocessing import Process, Pipe
import time

def f(conn):
    conn.send([42, None, 'hello'])
    conn.send([35, None, 'yello'])
    conn.close()

if __name__ == '__main__':
    parent_conn, child_conn = Pipe()
    p = Process(target=f, args=(child_conn,))
    p.start()
    time.sleep(0.5)
    print parent_conn.recv()   # prints "[42, None, 'hello']"
    print parent_conn.recv()   # prints "[42, None, 'hello']"
    p.join()
