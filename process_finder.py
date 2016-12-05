"""process_finder.py: has a dict of PIDs with the ports they are listening on, and a lookup dict of port->pid"""

__author__ = "Alex 'Chozabu' P-B"
__copyright__ = "Copyright 2016, Chozabu"


import subprocess

process_info = {}
port_lookup = {}

def run(commands):
    process = subprocess.Popen('/bin/bash', stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    return process.communicate(commands.encode())


def refresh_port_info():
    out, err = run("lsof -i -F cpn")
    out = out.decode()
    out = out.split("\n")
    currentUID = -1
    currentCMD = "unknown"
    currentPID = -1
    for line in out:
        if not line: continue
        if line[0]=='c':
            currentCMD=line[1:]
        if line[0]=='p':
            currentPID=int(line[1:])
        if line[0]=='f':
            currentUID=int(line[1:])
        if line[0]=='n':
            port = line.split(":")[-1]
            if port == "http":
                port=80
            elif port == "https":
                port = 443
            else:
                try:
                    port=int(port)
                except:
                    pass
            process_info[currentPID] = {
                "PID": currentPID,
                "UID": currentUID,
                "CMD": currentCMD,
                "NAME": line[1:],
                "PORT": port
            }
            port_lookup[port] = currentPID


    #print("done\n", out)

if __name__ == '__main__':
    refresh_port_info()
    #print(process_info)

