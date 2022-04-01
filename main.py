#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os  # standard library
import sys
from time import sleep
import pyvisa


# pyvisa.log_to_screen()

def getInstruments(k2400_gpibAddress, hvSource_gpibAddress):

    delay = 1
    rm = pyvisa.ResourceManager()

    l_resources = rm.list_resources()

    printMessage("Looking for pyVisa Resources......","*","*")
    printMessage(l_resources,"*","*")

    hv_source = None
    k2400 = None

    k2400 = rm.open_resource("GPIB0::" + str(k2400_gpibAddress) + "::INSTR", send_end=True)
    sleep(delay)

    sendCommandToInstrument(k2400,"*IDN?", "", 0, delay)
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

    print(len(message) * headerStr)
    print(message)
    print(len(message) * footerStr)

def initializeK2400(k2400, compliance, nplcs, range):

    delay = 0.5

    message = "Initializing the K2400 as Ampermeter....."
    printMessage(message,"*","*")

    sendCommandToInstrument(k2400,"*CLS", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400,"*SRE 4", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400,"*ESE 0", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400,":STAT:OPER:ENAB 0", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400,":STAT:MEAS:ENAB 0", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400,":STAT:QUES:ENAB 0", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400,":FORM:SREG ASC", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400,"*RST", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400,":SYST:BEEP:STAT ON", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400,":SOUR:FUNC VOLT", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400,":SOUR:VOLT:LEV 0", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400,":SOUR:VOLT:RANG 0.2", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400,":FORM:ELEM VOLT, CURR, TIME", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400,":SENS:FUNC:CONC ON", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400,":SENS:FUNC:OFF:ALL", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400,":SENS:FUNC:ON 'VOLT','CURR'", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400,":ROUTE:TERM REAR", "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400,":SENS:CURR:PROT " + "{:.4f}".format(compliance), "", 0, delay)  # AMPS
    sleep(delay)
    sendCommandToInstrument(k2400,":SENS:VOLT:NPLC " + str(int(nplcs)), "", 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400,":SENS:CURR:RANG " + "{:.4f}".format(range), "", 0, delay)  # AMPS
    sleep(delay)

    message = "Initializing done!!!"
    printMessage(message,"*","*")

def initializeHVSource(hv_source, rampVoltage, outputCurrentLimit, enableKill):

    delay = 1
    term = ""

    message = "Initializing the HV Source....."
    printMessage(message,"*","*")

    outputCurrentLimitInMilliamps = int(outputCurrentLimit*1000)

    sendCommandToInstrument(hv_source,"*RST", term, 0, delay)
    sleep(delay)
    sendCommandToInstrument(hv_source,"*CLS", term, 0, delay)
    sleep(delay)
    #set output current limit
    sendCommandToInstrument(hv_source,"I," + str(outputCurrentLimitInMilliamps) + "mA", term, 0, delay)
    sleep(delay)
    #set ramp
    sendCommandToInstrument(hv_source,"RAMP," + str(int(rampVoltage)) + "V/s", term, 0, delay)
    sleep(delay)
    # set kill enable
    sendCommandToInstrument(hv_source,"KILL," + 'EN' if enableKill else 'DIS', term, 0, delay)
    sleep(delay)
    #set the actual voltage value to zero
    sendCommandToInstrument(hv_source,"U," + "{:.3f}".format(0) + "kV", term, 0, delay)
    sleep(delay)
    waitForVoltageStabilization(hv_source, 0, 10)

    message = "Initializing done!!!"
    printMessage(message,"*","*")

def readVoltageFromHVSource(hv_source):

    delay = 0.75
    term = ""

    sendCommandToInstrument(hv_source,"STATUS,MU", term, 0, delay)
    response = hv_source.read_raw()  # response should be in format UM, RANGE=3000V, VALUE=2.458kV

    decoded_response = response.decode(encoding='ascii', errors='ignore')
    decoded_response = decoded_response[:-1]
    decoded_response = decoded_response.split(", ")

    # de esto "UM, RANGE=3000V, VALUE=2.458kV\x00"
    # debemos obtener esto otro 2.458

    # print(decoded_response)

    voltageString = decoded_response[2].removeprefix("VALUE=")
    voltageString = voltageString.removesuffix("kV")

    voltage = float(voltageString) * 1000
    return voltage

def waitForVoltageStabilization(hv_source, desiredVoltage, maxAbsolutePermissibleError):

    stable = False

    while not stable:
        readedVoltage = readVoltageFromHVSource(hv_source)
        error = abs(readedVoltage - desiredVoltage)
        # print("Error --> " + str(error) + "V. Max abs permissible error in volts is " + str(maxAbsolutePermissibleError) + "V.")
        if error<abs(maxAbsolutePermissibleError):
            stable = True
        sleep(0.5)
    sleep(1)

def getHVSourceStatus(hv_source):

    delay = 1
    term = ""

    sendCommandToInstrument(hv_source,"STATUS,DI", term, 0, delay)
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

    delay = 0.5
    term = ""

    k2400, hv_source = getInstruments(K2400_gpibAddress, HVSource_gpibAddress)

    initializeK2400(k2400, ammeterCompliance, ammeterNPLCs, ammeterRange)
    initializeHVSource(hv_source, rampVoltage, outputCurrentLimit, enableKill)


    # #calculo del step voltage
    stepVoltage = (finalVoltage - initialVoltage)/pointsVoltage
    nextVoltage = initialVoltage

    finalProcess = False

    # HV source ON
    sendCommandToInstrument(hv_source,"HV,ON", term, 0, delay)
    # K2400 ON
    sendCommandToInstrument(k2400,":OUTP:STAT ON", term, 0, delay)

    # Here you have to write to file
    f = open(resultsFilePath, "a")
    f.truncate(0)

    while not finalProcess:

        if nextVoltage > finalVoltage:
            finalProcess = True
        else:
            #Actualizamos la tension en la fuente
            print("Setting the H Source to --> " + "U," + "{:.3f}".format(nextVoltage/1000) + "kV")
            sendCommandToInstrument(hv_source,"U," + "{:.3f}".format(nextVoltage/1000) + "kV", term, 0, delay)
            actualVoltage = nextVoltage
            waitForVoltageStabilization(hv_source,actualVoltage, 10) #maxAbsolutePermissibleError is 2V

            #Here you have to measure the hv_source volatge
            hv_source_voltage = readVoltageFromHVSource(hv_source)
            print("Voltage source --> " + str(hv_source_voltage))
            #Here you have to measure the current of the k2400
            sendCommandToInstrument(k2400,":READ?",term,0,0.5)
            ammeter_response = k2400.read_raw()

            ammeter_decoded_response = ammeter_response.decode(encoding='ascii', errors='ignore')
            ammeter_decoded_response = ammeter_decoded_response[:-1]
            ammeter_decoded_response = ammeter_decoded_response.split(",")

            ammeter_current = float(ammeter_decoded_response[1])
            print("Ammeter Current --> " + str(ammeter_current))

            #Here you have to write to file
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

    # HV source off
    sendCommandToInstrument(hv_source,"HV,OFF", term, 0, delay)

    waitForVoltageStabilization(hv_source, 0, 10)  # maxAbsolutePermissibleError is 10V

    message = "Now HV Source is safe!!!!"
    printMessage(message, "*", "*")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    K2400_gpibAddress = 25
    HVSource_gpibAddress = 20
    initialVoltage = 0       #Volts
    finalVoltage = 2000         #Volts
    pointsVoltage = 10
    rampVoltage = 200           #Volts/second
    outputCurrentLimit = 0.025  #Amps
    enableKill = True
    ammeterRange = 0.000001     #Amps
    ammeterCompliance = 0.001 #Amps
    ammeterNPLCs = 10
    resultsFilePath = "test"
    resultsFilePathExtension = "csv"

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
        counter+=1


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
