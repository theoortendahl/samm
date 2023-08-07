import zmq, threading, time, logging, traceback

from utl_sam_server import *

class SamServer:
    
    def __init__(self, port, callback, interv=0.02):
        self.port = port
        self.sock = None
        self.callback = callback
        self.workingThread = None
        self.shouldTerminate = False
        self.execThread = None
        self.interv = interv
        self.cacheExec = []

    def cleanup():
        pass

    def startWorking(self):
        self.shouldTerminate = False
        self.workingThread = threading.Thread(target=self.looping)
        self.workingThread.start()
        self.execThread = threading.Thread(target=self.execLooping)
        self.execThread.start()

    def stopWorking(self):
        self.shouldTerminate = True

    def looping(self):
        context = zmq.Context()
        self.sock = context.socket(zmq.REP)
        self.sock.bind("tcp://*:%s"%self.port)
        self.sock.setsockopt(zmq.RCVTIMEO, 100)

        while not self.shouldTerminate:
            try:
                cmd, msg = self.sock.recv_multipart()
                retMsg, lateExec = self.callback(cmd, msg)
                self.sock.send(retMsg)
                
                # print("[SAMM TEST] Start.")
                # print(retMsg)
                # print("[SAMM TEST] End.")

                if lateExec is not None:
                    time.sleep(0.1)
                    self.cacheExec.append(lateExec)

                # print("[SAMM TEST] Got Something.")

            except zmq.error.Again:
                continue
            except KeyboardInterrupt:
                self.cleanup()
            except Exception as e:
                logging.error(traceback.format_exc())
                time.sleep(self.interv)
                continue

            time.sleep(self.interv)

        self.sock.close()

    def execLooping(self):
        while not self.shouldTerminate:
            if len(self.cacheExec) > 0:
                # print("[SAMM TEST] Execute Something.")
                execFunc = self.cacheExec.pop(0)
                execFunc()
            else:
                time.sleep(self.interv)
                continue


def main():
    srv = SamServer(8799, sammProcessingCallBack, 0.001)
    srv.startWorking()

if __name__=="__main__":
    main()