##################################################################
#
# Talks to Bridge12 MPS with commands received in tempFile file.
# A part of TopDNP
# by M. Hadi Timachi
#
##################################################################


import time
import serial
import serial.tools.list_ports
import sys

try:
    tempFile = sys.argv[1]
    runTime = sys.argv[2]
except Exception as e:
    print "Error {} occured when trying to get tempFile and runTime from argv".format(e)
    tempFile = "C:\\Users\\nmrsu\\Desktop\\tempTopSpin"
    runTime = 30


class Bridge12():
    def __init__(self, baudRate=115200, timeout=1):
        arduino_ports = [
            p.device
            for p in serial.tools.list_ports.comports()
            if 'Arduino' in p.description
        ]
        if not arduino_ports:
            raise IOError("No Arduino found")
        if len(arduino_ports) > 1:
            warnings.warn('Multiple Arduinos found - using the first')
        self.con = serial.Serial(arduino_ports[0], baudrate=baudRate, timeout=timeout)
        if not "MPS" in self.read():
            raise IOError("B12 does not reply")
        else:
            print "Successfully connected to B12"

    def send_command(self, cmd):
        self.con.write(cmd + "\n")
        return "Me: %s" % cmd

    def read(self):
        value = self.con.readline().decode('ascii')
        return "B12: %s" % value

    def close(self):
        return self.con.close()


print sys.version
try:
    bridge12_con = Bridge12()
    print "B12 connected. Ready for commands."
except Exception as e:
    print 'Error {} in connecting to B12.'.format(e)

commands = []
temp = tempFile
i = 0
while True:
    i += 1
    with open(temp, 'r') as tempFile:
        lines = tempFile.readlines()
        for line in lines:
            commands.append(line.strip())
    with open(temp, 'w') as delFile:
        delFile.write("")
    print commands
    if "break" in commands:
        print "Killing myself..."
        break
    else:
        for i, command in enumerate(commands):
            print "command received %s" % command
            bridge12_con.send_command(command)
            print bridge12_con.read()
            commands.pop(i)
    if i % 15 == 0:
        print "I'm waiting for commands in file {}".format(tempFile)
    time.sleep(1)
