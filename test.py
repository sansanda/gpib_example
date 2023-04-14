import time
import winsound
from time import sleep

import pyvisa
from termcolor import colored
from pyvisa import constants
import numpy as np


def printMessage(message, headerStr, footerStr):
    print(colored(len(message) * headerStr, "magenta"))
    print(colored(message, "magenta"))
    print(colored(len(message) * footerStr, "magenta"))


def sendCommandToInstrument(instrument, command, terminator, delayBefore, delayAfter):
    sleep(delayBefore)
    instrument.write_raw(command + terminator)
    sleep(delayAfter)


def main():
    delay = 0.5

    rm = pyvisa.ResourceManager()

    l_resources = rm.list_resources()

    printMessage("Looking for pyVisa Resources......", "*", "*")
    printMessage(l_resources, "*", "*")

    hv_source = rm.open_resource("GPIB0::" + str(20) + "::INSTR", send_end=True,
                                 write_termination="\n",
                                 read_termination="",
                                 access_mode=constants.AccessModes.no_lock)
    sleep(delay)

    sendCommandToInstrument(hv_source, "ID", "", 0, delay)
    response = hv_source.read_raw()  # type(response) =--> bytes
    decoded_response = response.decode(encoding='ascii', errors='ignore')
    print(decoded_response)

    # sendCommandToInstrument(hv_source, "U,0.5kV", "\n", 0, delay)
    time.sleep(2)
    sendCommandToInstrument(hv_source, "*RST", "", delay, delay)
    time.sleep(2)
    sendCommandToInstrument(hv_source, "*CLS", "", 0, delay)
    time.sleep(2)

    frequency = 1000  # Set Frequency To 2500 Hertz
    duration = 1000  # Set Duration To 1000 ms == 1 second
    winsound.Beep(frequency, duration)

    # time.sleep(1)
    # sendCommandToInstrument(hv_source, "HV,ON", "", 0, delay)
    #
    # startVolage = 0.0
    # stopVoltage = 1.0
    # step = 0.1
    # sweep = np.arange(startVolage,stopVoltage,step)
    # print(sweep)
    # for v in sweep:
    #     print("sending command...")
    #     sendCommandToInstrument(hv_source, "U,"+str(v)+"kV", "\n", 0, 0)
    #     time.sleep(5)
    #
    # sendCommandToInstrument(hv_source, "U," + str(0.0) + "kV", "\n", 0, 0)
    # sendCommandToInstrument(hv_source, "HV,OFF", "", 0, delay)
    #
    # # response = hv_source.read_raw()  # type(response) =--> bytes
    # # decoded_response = response.decode(encoding='ascii', errors='ignore')
    # # print(decoded_response)


if __name__ == "__main__":
    main()
