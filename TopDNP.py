##################################################################
#
# Sets up an ODNP and T1 series experiment based on user input and template experiments.
# by M. Hadi Timachi
#
##################################################################


# Adjust things here
# To control B12 set controlB12 to True
controlB12 = True
python27Path = 'C:\\Python27\\python.exe'
b12CodePath = 'C:\\Bruker\\TopSpin3.2\\exp\\stan\\nmr\\py\\user\\imports\\b12.py'
b12TempFile = 'C:\\Users\\nmrsu\\Desktop\\tempTopSpin'
b12RunTime = '300'  # The time that the external code for B12 should keep running in minutes
# IP address of gpib to etherenet converter connected to power meter
# To control power meter, set controlPowerMeter to True
controlPowerMeter = True
pMeterIP = '134.147.197.144'
# General parameters
scriptPath = 'C:\Bruker\TopSpin3.2\exp\stan\\nmr\py\user'  # The path this code is in
expsPath = 'C:\NMRUserData\HadiTimachi'
waitTime = 4  # Time to wait after giving order to B12
powerReadoutAverage = 50  # The number of averages made to get the real power readout
powerMeterCalib = 19.46  # The T connection calibration value. This will be added to dBm readout

import os
import datetime
import math
import time
import imports.gpib_eth as g

if controlB12:
    import subprocess

    # Start code to control B12
    # initializing the process kill for previous python sessions
    b12File = open(b12TempFile, 'r+')
    b12File.write("break \n")
    b12File.close()
    # Start code to control B12
    b12Script = subprocess.Popen('%s %s %s %s' % (python27Path, b12CodePath, b12TempFile, str(waitTime)))
    status = subprocess.Popen.poll(b12Script)


# Functions we need :
def dec_range_non_linear(x, y, steps, linFraction=2):
    """
    Calculates steps for DNP experiment. It divides the whole range with linFraction, takes the first part as linear
    and the second part as logarithmic :param x: start power (dBm) :param y: end power (dBm) :param steps: number of
    steps :param linFraction: the division factor :return: list of powers
    """
    xInc = float(x)
    x = float(x)
    y = float(y)
    linearStep = float(int(steps) // linFraction)
    logStep = steps - linearStep
    for i in range(0, linearStep):
        yield xInc
        # xInc += ((y -x)// linFraction) // linearStep
        xInc = w_to_dbm(dbm_to_w(xInc) + float((dbm_to_w(y / linFraction) - dbm_to_w(x)) / float(linearStep)))
    for i in range(linearStep, steps - 1):
        xInc = w_to_dbm(dbm_to_w(xInc) + float((dbm_to_w(y) - dbm_to_w(y / linFraction)) / float(logStep) / 2))
        yield float(xInc)
    for i in range(steps - 1, steps):
        xInc = w_to_dbm(float((dbm_to_w(y))))
        yield float(xInc)


def dec_range_linear(x, y, steps):
    """
    Calculates linear steps (for T1 experiments)
    :param x: start power (dBm)
    :param y: end power (dBm)
    :param steps: number of steps
    :return: list of powers
    """
    xInc = float(x)
    y = float(y)
    for i in range(0, steps):
        yield xInc
        xInc = w_to_dbm(dbm_to_w(xInc) + float((dbm_to_w(y) - dbm_to_w(x)) / float(steps)))


def dbm_to_w(dbmPower):
    return (10 ** (float(dbmPower) / 10)) / 1000.


def w_to_dbm(wPower):
    return (10. * math.log10(1000 * float(wPower)))


# Powermeter connection
def connect_to_power_meter(gpibaddr=14, ipaddr=pMeterIP):
    powerConn = g.gigatronics_powermeter(gpibaddress=gpibaddr, ip=ipaddr)
    return powerConn


# Initialize C:\tempTopSpin for B12 commands
# Unfortunately, we have to open and close the file every time we want B12 commands
b12File = open(b12TempFile, 'r+')
# initializing the process kill for previous python sessions
freqResult = INPUT_DIALOG("Frequency input",
                          "About to set the waveguide switch to DNP mode\n"
                          "Turn on nitrogen flow and unplug the mod. coil\n "
                          "AND\n"
                          "enter center frequency to set for B12.",
                          ["Frequency [kHz] = "], ["9800000"], [""], ["1"])
b12File.write("power 0 \n")
b12File.write("freq " + freqResult[0] + "\n")
b12File.write("wgstatus 1 \n")
b12File.close()

# datetime for experiment folder name
dT = datetime.date.today().strftime("%Y%m%d_CWODNP_")

if controlPowerMeter:
    # test connections:
    try:
        powerConn = connect_to_power_meter()
    except:
        ERRMSG("Error in connecting to power meter. Is it powered on?!", "TopDNP Power meter error")
        EXIT()

# Ask for exp. name and folder
expNameDia = dialogs.MultiLineInputDia("TopDNP",
                                       "Please enter parameters for the new DNP experiment:",
                                       ["Folder path", "Folder name"],
                                       [expsPath, dT],
                                       ["0", "1"], ["", ""],
                                       None, None, 0, 15, 0, None)
expNameDia.setExitUponEnter(0)
expNameDia.setVisible(1)
expNameResult = expNameDia.getValues()
expPath = os.path.join(expNameResult[0], expNameResult[1])
if not os.path.exists(expPath):
    os.makedirs(expPath)
else:
    MSG("It seems that folder %s exists. Please rename that if you want to have a new exp." %
        str(os.path.join(expNameResult[0], expNameResult[1])))
    EXIT()

MSG("Experiment path is going to be: \n %s" % str(expPath))

dia = dialogs.MultiLineInputDia("TopDNP",
                                "Please enter parameters for experiment:",
                                ["DNP steps calculation [0=manual, 1=auto]",
                                 "(if auto) Minimum power set for DNP [dBm] = ",
                                 "(if auto) Maximum power set for DNP [dBm] = ",
                                 "(if auto) Number of steps for DNP series = ",
                                 "Scan backwards too [0=No, 1=Yes]",
                                 "NS for DNP",
                                 "D1 for DNP (recommended 25s for NS>1)",
                                 "Do T1 series [0=No, 1=Yes]",
                                 "T1 steps calculation [0=manual, 1=auto]",
                                 "(if auto) Minimum power set for T1 [dBm] = ",
                                 "(if auto) Maximum power set for T1 [dBm] = ",
                                 "(if auto) Number of steps for T1 series = ",
                                 "Scan backwards too [0=No, 1=Yes]",
                                 "NS for T1",
                                 "D1 for T1",
                                 "Time to wait between exps. [s]"],
                                ["0", "0", "38", "20", "1", "1", "5", "1", "0", "0", "30", "4", "1", "1", "25", "5"],
                                ["1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1"],
                                ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
                                None, None, 0, 15, 0, None)
dia.setExitUponEnter(0)
dia.setVisible(1)
result = dia.getValues()

if result == None:  # Canceled by user
    EXIT()
else:
    dnpAuto, dnpMinP, dnpMaxP, dnpSteps, dnpBack, dnpNS, dnpD1, doT1, t1Auto, t1MinP, t1MaxP, t1Steps, t1Back, t1NS, t1D1, interExpDelay = result

interExpDelay = float(interExpDelay)
if int(dnpAuto) == 1:
    dnpPowerRange = [round(x, 1) for x in dec_range_linear(dnpMinP, dnpMaxP, int(dnpSteps))]
else:
    dnpRangeDia = dialogs.MultiLineInputDia("TopDNP",
                                            "Please enter power steps for DNP exps. separated by comma",
                                            ["Powers [dBm]"],
                                            ["0,6,12,18,24,30,31,32,33,34,35,36"],
                                            ["0"], [""],
                                            None, None, 0, 15, 0, None)
    dnpRangeDia.setExitUponEnter(1)
    dnpRangeDia.setVisible(1)
    dnpRangeDia = dnpRangeDia.getValues()
    try:
        dnpPowerRange = [float(dnpRangeDia[0].split(',')[i]) for i in range(0, len(dnpRangeDia[0].split(',')))]
    except:
        ERRMSG("Error in getting DNP power values.", "TopDNP DNP power series error")
        EXIT()
if int(t1Auto) == 1:
    t1PowerRange = [round(x, 1) for x in dec_range_linear(t1MinP, t1MaxP, int(t1Steps))]
else:
    t1RangeDia = dialogs.MultiLineInputDia("TopDNP",
                                           "Please enter power steps for T1 exps. separated by comma",
                                           ["Powers [dBm]"],
                                           ["0,32,35,37,38"],
                                           ["0"], [""],
                                           None, None, 0, 15, 0, None)
    t1RangeDia.setExitUponEnter(1)
    t1RangeDia.setVisible(1)
    t1RangeDia = t1RangeDia.getValues()
    try:
        t1PowerRange = [float(t1RangeDia[0].split(',')[i]) for i in range(0, len(t1RangeDia[0].split(',')))]
    except:
        ERRMSG("Error in getting T1 power values.", "TopDNP T1 power series error")
        EXIT()
if int(dnpBack) == 1:
    dnpPowerRange += dnpPowerRange[::-1][1::2]
if int(t1Back) == 1:
    t1PowerRange += t1PowerRange[::-1][1::2]
if int(doT1) == 1:
    if not CONFIRM("TopDNP confirmation", "About to do DNP and T1 series \n" +
                                          "DNP power range: %s" % str(dnpPowerRange) +
                                          "\n T1 power range: %s" % str(t1PowerRange) +
                                          "\n Is it correct?") == 1:
        EXIT()
    try:
        os.makedirs(os.path.join(expPath, "1"))
        os.makedirs(os.path.join(expPath, "50"))
        # This is not a good idea, but Bruker runs the code in another folder
        os.system("xcopy %s %s /E" % (os.path.join(scriptPath, "1"), os.path.join(expPath, "1")))
        os.system("xcopy %s %s /E" % (os.path.join(scriptPath, "50"), os.path.join(expPath, "50")))
    except:
        # ERRMSG("Error copying folders!", "Copy error")
        # EXIT()
        pass
else:
    if not CONFIRM("TopDNP confirmation", "About to do DNP\n" +
                                          "DNP power range: %s" % str(dnpPowerRange) +
                                          "\n Is it correct?") == 1:
        EXIT()
    try:
        os.makedirs(os.path.join(expPath, "1"))
        # This is not a good idea, but Bruker runs the code in another folder
        os.system("xcopy %s %s /E" % (os.path.join(scriptPath, "1"), os.path.join(expPath, "1")))
    except:
        pass

RE([str(expNameResult[1]), "1", "1", str(expNameResult[0])], "y")
# set NS & D1
XCMD("NS " + dnpNS)
XCMD("D1 " + dnpD1)
# Check the wobbling
MSG("Going to run wobbling. Please stop it manually once you're done.", "TopDNP wobb")
XCMD('wobb')
MSG("Please adjust frequency offset THEN click close to continue.", "TopDNP frequency adjustment")
# run freq adjustment
ZG()
EFP()
MSG("Please adjust frequency offset THEN click close to continue.", "TopDNP frequency adjustment")
ZG()
b12File = open(b12TempFile, 'r+')
b12File.write("rfstatus 1 \n")
b12File.close()
if not CONFIRM("TopDNP confirmation", "Is the MW on?") == 1:
    EXIT()
# DNP loop
for i, dnpSet in enumerate(dnpPowerRange):
    curExpNo = str(i + 2)
    prevExpNo = str(i + 1)
    curExpPath = os.path.join(expPath, curExpNo)
    prevExpPath = os.path.join(expPath, prevExpNo)
    powerAvg = 0
    # Set B12
    b12File = open(b12TempFile, 'r+')
    b12File.write("power %s \n" % str(int(dnpSet * 10)))
    b12File.close()
    # This should be optimized
    time.sleep(waitTime)

    if controlPowerMeter:
        for j in range(0, powerReadoutAverage):
            powerAvg += powerConn.read_power()
            time.sleep(.1)
        powerAvg /= float(powerReadoutAverage)
    else:
        powerAvg = dnpSet

    # MSG("power for exp %s powerset %s is %s" % (curExpNo, str(int(dnpSet * 10)), str(powerAvg)))
    try:
        os.makedirs(curExpPath)
        os.system("xcopy %s %s /E" % (prevExpPath, curExpPath))
        if os.path.isfile(os.path.join(curExpPath, "fid")):
            os.remove(os.path.join(curExpPath, "fid"))
        if os.path.exists(os.path.join(curExpPath, "pdata", "999")):
            os.system("RMDIR %s /s /q" % os.path.join(curExpPath, "pdata", "999"))
    except:
        ERRMSG("Error copying folders!", "TopDNP copy error")
        EXIT()
    try:
        if os.path.isfile(os.path.join(curExpPath, "pdata", "1", "title")):
            os.remove(os.path.join(curExpPath, "pdata", "1", "title"))
        titleFile = open(os.path.join(curExpPath, "pdata", "1", "title"), 'w')
        titleFile.write("CWODNP set %.3f dBm" % powerAvg)
        titleFile.close()
    except:
        ERRMSG("Error changing title!", "TopDNP title change error")
    RE([str(expNameResult[1]), curExpNo, "1", str(expNameResult[0])], "y")
    # run the experiment
    ZG()
    time.sleep(interExpDelay)
# Try to get O1 for offset
dnpO1 = GETPAR2("O1")
# MSG("O1 is: "+dnpO1 ,"O1")
t1O1 = float(dnpO1) - 50000
# Making power zero again
b12File = open(b12TempFile, 'r+')
b12File.write("power 0 \n")
b12File.close()
# I would wait 5 minutes
time.sleep(5)
# T1 loop
if doT1 and t1Steps > 0:
    for i, t1Set in enumerate(t1PowerRange):
        curExpNo = str(i + 50)
        prevExpNo = str(i + 49)
        curExpPath = os.path.join(expPath, curExpNo)
        prevExpPath = os.path.join(expPath, prevExpNo)
        powerAvg = 0
        # Set B12
        b12File = open(b12TempFile, 'r+')
        b12File.write("power %s \n" % str(int(t1Set * 10)))
        b12File.close()
        time.sleep(waitTime)
        if controlPowerMeter:
            for j in range(0, powerReadoutAverage):
                powerAvg += powerConn.read_power()
                time.sleep(.1)
            powerAvg /= float(powerReadoutAverage)
            powerAvg += float(powerMeterCalib)
        else:
            powerAvg = t1Set

        # MSG("power for exp %s powerset %s is %s" % (curExpNo, str(int(dnpSet * 10)), str(powerAvg)))
        if i != 0:
            try:
                os.makedirs(curExpPath)
                os.system("xcopy %s %s /E" % (prevExpPath, curExpPath))
                if os.path.isfile(os.path.join(curExpPath, "ser")):
                    os.remove(os.path.join(curExpPath, "ser"))
            except:
                ERRMSG("Error copying T1 folders!", "TopDNP copy error")
                EXIT()
        try:
            if os.path.isfile(os.path.join(curExpPath, "pdata", "1", "title")):
                os.remove(os.path.join(curExpPath, "pdata", "1", "title"))
            titleFile = open(os.path.join(curExpPath, "pdata", "1", "title"), 'w')
            titleFile.write("T1 set %.3f dBm" % powerAvg)
            titleFile.close()
        except:
            ERRMSG("Error changing T1 exp. title!", "TopDNP title change error")
        RE([str(expNameResult[1]), curExpNo, "1", str(expNameResult[0])], "y")
        # set NS & D1
        XCMD("NS " + t1NS)
        XCMD("D1 " + t1D1)
        # set O1
        XCMD("O1 " + str(t1O1))
        # run the experiment
        ZG()
        time.sleep(interExpDelay)
# Making power zero again
b12File = open(b12TempFile, 'r+')
b12File.write("power 0 \n")
b12File.write("rfstatus 0 \n")
b12File.close()

# Yay?
MSG("DNP exp. done!\n Turn off nitrogen flow!", "TopDNP done")
