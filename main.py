#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os  # standard library
import sys
from time import sleep
import pyvisa
from termcolor import colored
from watchDog import Watchdog
from fileUtilities import readConfigFile
from exceptionHandlers import voltageStabilizationTimeoutHandler
# pyvisa.log_to_screen()

voltageStabilizationTimeout = 10  # in s
HVSourceSettingOFFTimeout = 60  # in s

def getInstruments(k2400_gpibAddress, hvSource_gpibAddress):
    delay = 0.1
    rm = pyvisa.ResourceManager()

    l_resources = rm.list_resources()

    printMessage("Looking for pyVisa Resources......", "*", "*")
    printMessage(l_resources, "*", "*")

    hv_source = None
    k2400 = None

    k2400 = rm.open_resource("GPIB0::" + str(k2400_gpibAddress) + "::INSTR", send_end=True)
    sleep(delay)

    sendCommandToInstrument(k2400, "*IDN?", "", 0, delay)
    response = k2400.read_raw()  # type(response) =--> bytes
    decoded_response = response.decode(encoding='ascii', errors='ignore')
    print(decoded_response)

    hv_source = rm.open_resource("GPIB0::" + str(hvSource_gpibAddress) + "::INSTR", send_end=True)
    sleep(delay)

    sendCommandToInstrument(hv_source, "ID", "", 0, delay)
    response = hv_source.read_raw()  # type(response) =--> bytes
    decoded_response = response.decode(encoding='ascii', errors='ignore')
    print(decoded_response)

    return k2400, hv_source


def sendCommandToInstrument(instrument, command, terminator, delayBefore, delayAfter):
    sleep(delayBefore)
    instrument.write_raw(command + terminator)
    sleep(delayAfter)


def printMessage(message, headerStr, footerStr):
    print(colored(len(message) * headerStr,"magenta"))
    print(colored(message,"magenta"))
    print(colored(len(message) * footerStr,"magenta"))


def initializeK2400(k2400, compliance, nplcs, range):
    delay = 0.1

    message = "Initializing the K2400 as Ampermeter....."
    printMessage(message, "*", "*")

    sendCommandToInstrument(k2400, "*CLS", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, "*SRE 4", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, "*ESE 0", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":STAT:OPER:ENAB 0", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":STAT:MEAS:ENAB 0", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":STAT:QUES:ENAB 0", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":FORM:SREG ASC", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, "*RST", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":SYST:BEEP:STAT ON", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":SOUR:FUNC VOLT", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":SOUR:VOLT:LEV 0", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":SOUR:VOLT:RANG 0.2", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":FORM:ELEM VOLT, CURR, TIME", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":SENS:FUNC:CONC ON", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":SENS:FUNC:OFF:ALL", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":SENS:FUNC:ON 'VOLT','CURR'", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":ROUTE:TERM REAR", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":SENS:CURR:PROT " + "{:.4f}".format(compliance), "", 0, delay)  # AMPS
    sleep(delay)
    sendCommandToInstrument(k2400, ":SENS:VOLT:NPLC " + str(int(nplcs)), "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":SENS:CURR:RANG " + "{:.4f}".format(range), "", 0, delay)  # AMPS
    sleep(delay)

    message = "Initializing done!!!"
    printMessage(message, "*", "*")


def initializeHVSource(hv_source, rampVoltage, outputCurrentLimit, enableKill):
    delay = 1
    term = ""

    message = "Initializing the HV Source....."
    printMessage(message, "*", "*")

    outputCurrentLimitInMilliamps = int(outputCurrentLimit * 1000)

    sendCommandToInstrument(hv_source, "*RST", term, 0, delay)
    sleep(delay)
    sendCommandToInstrument(hv_source, "*CLS", term, 0, delay)
    sleep(delay)
    # set output current limit
    sendCommandToInstrument(hv_source, "I," + str(outputCurrentLimitInMilliamps) + "mA", term, 0, delay)
    sleep(delay)
    # set ramp
    sendCommandToInstrument(hv_source, "RAMP," + str(int(rampVoltage)) + "V/s", term, 0, delay)
    sleep(delay)
    # set kill enable
    sendCommandToInstrument(hv_source, "KILL," + 'EN' if enableKill else 'DIS', term, 0, delay)
    sleep(delay)

    HVSource_OutputVoltageStabilization_Success = False

    while not HVSource_OutputVoltageStabilization_Success:

        # Actualizamos la tension en la fuente
        print(colored("Setting the H Source to --> " + "U," + "{:.3f}".format(0) + "kV", "yellow"))
        sendCommandToInstrument(hv_source, "U," + "{:.3f}".format(0) + "kV", term, 0, delay)
        sleep(delay)

        try:
            print(colored("Starting the WatchDog for preventing infinitive loop in voltage stabilization...", "grey",
                          "on_white"))
            watchdog = Watchdog(HVSourceSettingOFFTimeout)  # because we want to set the hv source to zero
            waitForVoltageStabilization(hv_source, 0, 10, 0.5, 1)  # maxAbsolutePermissibleError is 10V
            HVSource_OutputVoltageStabilization_Success = True

        except Watchdog:
            # handle watchdog error
            print(colored(
                "Voltage Stabilization WatchDog has raised an exception. Voltage stabilization is taking too much time...",
                "red"))

        watchdog.stop()

    message = "Initializing done!!!"
    printMessage(message, "*", "*")


def readVoltageFromHVSource(hv_source, delay=0.5):
    term = ""
    correctResponse = False
    voltage = 0.0

    while not correctResponse:

        sendCommandToInstrument(hv_source, "STATUS,MU", term, 0, delay)
        response = hv_source.read_raw()  # response should be in format "UM, RANGE=3000V, VALUE=2.458kV\x00"
        decoded_response = response.decode(encoding='ascii', errors='ignore')
        decoded_response = decoded_response.split(", ")
        print(decoded_response)

        if len(decoded_response) == 3:
            correctResponse = True
            voltageString = decoded_response[2][:-1]
            # de esto "UM, RANGE=3000V, VALUE=2.458kV\x00"
            # debemos obtener esto otro 2.458
            voltageString = voltageString.removeprefix("VALUE=")
            voltageString = voltageString.removesuffix("kV")
            voltage = float(voltageString) * 1000
            print(colored("Lectura de voltage correcta en la fuente de HV. Voltage = " + str(voltage) + "V","green"))

        else:
            #la lectura del voltage ha fallado, esperamos y volvemos a pedir
            print(colored("Fallo en la lectura de voltage a la fuente de HV. Esperamos un tiempo y solicitamos de nuevo...","red"))
            sleep(1)

    return voltage


def waitForVoltageStabilization(hv_source, desiredVoltage, maxAbsolutePermissibleError, checkPeriod, lastDelay):

    stable = False
    voltageStabilizationTimeout = 10000 #in ms

    #aqui deberiamos poner en marcha un timer a modo de watchdog con el voltageStabilizationTimeout
    #que fuerce a la funcion a devolver falso si este timer salta

    while not stable:
        readedVoltage = readVoltageFromHVSource(hv_source)
        error = abs(readedVoltage - desiredVoltage)
        # print("Error --> " + str(error) + "V. Max abs permissible error in volts is " + str(maxAbsolutePermissibleError) + "V.")
        if error < abs(maxAbsolutePermissibleError):
            stable = True
        sleep(checkPeriod)
    sleep(lastDelay)

    #aqui deberiamos eliminar el timer

def getHVSourceStatus(hv_source):
    delay = 1
    term = ""

    sendCommandToInstrument(hv_source, "STATUS,DI", term, 0, delay)
    response = hv_source.read_raw()

    return response


def start_process(K2400_gpibAddress,
                  HVSource_gpibAddress,
                  initialVoltage,
                  finalVoltage,
                  pointsVoltage,
                  rampVoltage,
                  outputCurrentLimit,
                  enableKill,
                  ammeterRange,
                  ammeterCompliance,
                  ammeterNPLCs,
                  resultsFilePath):

    delay = 0.5 # in s
    term = ""

    k2400, hv_source = getInstruments(K2400_gpibAddress, HVSource_gpibAddress)

    initializeK2400(k2400, ammeterCompliance, ammeterNPLCs, ammeterRange)
    initializeHVSource(hv_source, rampVoltage, outputCurrentLimit, enableKill)

    # #calculo del step voltage
    stepVoltage = (finalVoltage - initialVoltage) / pointsVoltage
    nextVoltage = initialVoltage

    finalProcess = False

    # HV source ON
    sendCommandToInstrument(hv_source, "HV,ON", term, 0, delay)
    # K2400 ON
    sendCommandToInstrument(k2400, ":OUTP:STAT ON", term, 0, delay)

    # Here you have to write to file
    f = open(resultsFilePath, "a")
    f.truncate(0)

    while not finalProcess:

        if nextVoltage > finalVoltage:
            finalProcess = True

        else:

            HVSource_OutputVoltageStabilization_Success = False

            while not HVSource_OutputVoltageStabilization_Success:

                # Actualizamos la tension en la fuente
                print(colored("Setting the H Source to --> " + "U," + "{:.3f}".format(nextVoltage / 1000) + "kV","yellow"))
                sendCommandToInstrument(hv_source, "U," + "{:.3f}".format(nextVoltage / 1000) + "kV", term, 0, delay)

                try:
                    print(colored("Starting the WatchDog for preventing infinitive loop in voltage stabilization...",
                                  "grey", "on_white"))
                    watchdog = Watchdog(voltageStabilizationTimeout)
                    waitForVoltageStabilization(hv_source, nextVoltage, 10, 0.5, 1)  # maxAbsolutePermissibleError is 2V
                    HVSource_OutputVoltageStabilization_Success = True

                except Watchdog:
                    # handle watchdog error
                    print(colored("Voltage Stabilization WatchDog has raised an exception. Voltage stabilization is taking too much time...", "red"))

                watchdog.stop()



            #Una vez el voltaje de la fuente es estable a su salida podremos considerar que actualvoltage = nextvoltage
            actualVoltage = nextVoltage

            # Here you have to measure the hv_source volatge
            hv_source_voltage = readVoltageFromHVSource(hv_source)
            print(colored("Voltage source --> " + str(hv_source_voltage) + "V","cyan"))
            # Here you have to measure the current of the k2400
            sendCommandToInstrument(k2400, ":READ?", term, 0, 0.5)
            ammeter_response = k2400.read_raw()

            ammeter_decoded_response = ammeter_response.decode(encoding='ascii', errors='ignore')
            ammeter_decoded_response = ammeter_decoded_response[:-1]
            ammeter_decoded_response = ammeter_decoded_response.split(",")

            ammeter_current = float(ammeter_decoded_response[1])
            print(colored("Ammeter Current --> " + str(ammeter_current) + "A","cyan"))

            # Here you have to write to file
            f.write(str(hv_source_voltage) + "," + str(abs(ammeter_current)) + "\n")
            f.flush()

            nextVoltage = actualVoltage + stepVoltage

    message = "Closing the results file!!!"
    printMessage(message, "*", "*")
    f.close()

    message = "Process Complete!!!"
    printMessage(message, "*", "*")

    message = "Powering off instruments!!!"
    printMessage(message, "*", "*")

    hvSource_SettingOFF_Success = False

    while not hvSource_SettingOFF_Success:

        # HV source off
        sendCommandToInstrument(hv_source, "HV,OFF", term, 0, delay)

        try:
            print(colored("Starting the WatchDog for preventing infinitive loop in HV OFF process...", "grey",
                          "on_white"))
            watchdog = Watchdog(HVSourceSettingOFFTimeout)
            waitForVoltageStabilization(hv_source, 0, 10, 0.5, 1)  # maxAbsolutePermissibleError is 10V
            hvSource_SettingOFF_Success = True

        except Watchdog:
            # handle watchdog error
            print(colored(
                "Voltage Stabilization WatchDog has raised an exception. Voltage OFF Process is taking too much time...",
                "red"))

        watchdog.stop()



    message = "Now HV Source is safe!!!!"
    printMessage(message, "*", "*")





# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    configFilePath = "config.json"

    K2400_gpibAddress, \
    HVSource_gpibAddress, \
    initialVoltage, \
    finalVoltage, \
    pointsVoltage, \
    rampVoltage, \
    outputCurrentLimit, \
    enableKill, \
    ammeterRange, \
    ammeterCompliance, \
    ammeterNPLCs, \
    resultsFilePath, \
    resultsFilePathExtension = readConfigFile(configFilePath)

    # K2400_gpibAddress = 25
    # HVSource_gpibAddress = 20
    # initialVoltage = 0       #Volts
    # finalVoltage = 1500         #Volts
    # pointsVoltage = 50
    # rampVoltage = 400           #Volts/second
    # outputCurrentLimit = 0.025  #Amps
    # enableKill = True
    # ammeterRange = 0.000001     #Amps
    # ammeterCompliance = 0.001 #Amps
    # ammeterNPLCs = 10
    # resultsFilePath = "test_mosfet"
    # resultsFilePathExtension = "csv"

    counter = 0

    while True:
        start_process(K2400_gpibAddress,
                      HVSource_gpibAddress,
                      initialVoltage,
                      finalVoltage,
                      pointsVoltage,
                      rampVoltage,
                      outputCurrentLimit,
                      enableKill,
                      ammeterRange,
                      ammeterCompliance,
                      ammeterNPLCs,
                      resultsFilePath + str(counter) + "." + resultsFilePathExtension)
        counter += 1

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
