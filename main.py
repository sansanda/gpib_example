#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
os.system('color')

from time import sleep
import time

import pyvisa

from termcolor import colored
from fileUtilities import readConfigFile

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
    k2400.timeout = 25000 #si configuramos el k2400 con filtro y nplcs altos, necesitaremos tiempos de timeout altos tambien
    #sleep(delay)

    sendCommandToInstrument(k2400, "*IDN?", "", 0, delay)
    response = k2400.read_raw()  # type(response) =--> bytes
    decoded_response = response.decode(encoding='ascii', errors='ignore')
    print(decoded_response)

    hv_source = rm.open_resource("GPIB0::" + str(hvSource_gpibAddress) + "::INSTR", send_end=True)
    #sleep(delay)

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
    print(colored(len(message) * headerStr, "magenta"))
    print(colored(message, "magenta"))
    print(colored(len(message) * footerStr, "magenta"))


def initializeK2400(k2400, compliance, nplcs, range):
    delay = 0.25 #seconds
    term = ""

    message = "Initializing the K2400 as Ampermeter....."
    printMessage(message, "*", "*")

    sendCommandToInstrument(k2400, "*CLS", term, 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, "*SRE 4", term, 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, "*ESE 0", term, 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":STAT:OPER:ENAB 0", term, 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":STAT:MEAS:ENAB 0", term, 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":STAT:QUES:ENAB 0", term, 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":FORM:SREG ASC", term, 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, "*RST", term, 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":SYST:BEEP:STAT ON", term, 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":SOUR:FUNC VOLT", term, 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":SOUR:VOLT:LEV 0", term, 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":SOUR:VOLT:RANG 0.2", term, 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":FORM:ELEM VOLT, CURR, TIME", term, 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":SENS:FUNC:CONC ON", term, 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":SENS:FUNC:OFF:ALL", term, 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":SENS:FUNC:ON 'VOLT','CURR'", term, 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400, ":SENS:CURR:NPLC " + str(int(nplcs)), term, 0, delay)
    sleep(delay)


    sendCommandToInstrument(k2400,":SENSe:AVERage:TCONtrol REPeat", term, 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400,":SENSe:AVERage:COUNt 8", term, 0, delay)
    sleep(delay)
    sendCommandToInstrument(k2400,":SENSe:AVERage ON", term, 0, delay)
    sleep(delay)

    sendCommandToInstrument(k2400, ":SENS:CURR:PROT " + "{:.4f}".format(compliance), term, 0, delay)  # AMPS
    sleep(delay)
    sendCommandToInstrument(k2400, ":SENS:CURR:RANG " + "{:.4f}".format(range), term, 0, delay)  # AMPS
    sleep(delay)
    sendCommandToInstrument(k2400, ":ROUTE:TERM REAR", term, 0, delay)
    sleep(delay)
    # K2400 ON
    sendCommandToInstrument(k2400, ":OUTP:STAT ON", term, 0, delay)

    # :SENSe: AVERage:TCONtrol < type >
    # :SENSe: AVERage:COUNt < n >
    # :SENSe: AVERage < state >

    message = "Initializing done!!!"
    printMessage(message, "*", "*")


def initializeHVSource(hv_source, rampVoltage, outputCurrentLimit, enableKill):
    delay = 0.25
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

    # Setting output voltage to zero
    setHVOutputVoltage(hv_source, 0, 60)

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
            print(colored("Lectura de voltage correcta en la fuente de HV. Voltage = " + str(voltage) + "V", "green"))

        else:
            # la lectura del voltage ha fallado, esperamos y volvemos a pedir
            print(colored(
                "Fallo en la lectura de voltage a la fuente de HV. Esperamos un tiempo y solicitamos de nuevo...",
                "red"))
            sleep(1)

    return voltage

def waitForVoltageStabilization(hv_source, desiredVoltage, maxAbsolutePermissibleError, checkPeriod, lastDelay,
                                 voltageStabilizationTimeout=10):
    """
    Funcion sincrona cuya funcion basica es esperar a que la salida de tension de una fuente de alimentacion (en nuestro caso una hv_voltage)
    entre dentro del rango de error permisible. Una vez la salida se encuentra dentro de dicho rango de error la funcion retorna True.
    Por ejemplo: Si deriredVoltage = 1000V y nuestro maxAbsolutePermissibleError = 10V entonces la funcion retornara True en el momento
    de leer un voltage en la fuente de alimentacion que se encuentre dentro del rango (990V,1010V). En nuestro caso un valor leido
    en la salida de la fuente igual a 995V haría retornar True a la fuencion, por el contrario un valor leido a la salida de la fuente
    igual a 880V mantendria a la funcion dentro del bucle de lectura de tension a la salida de la fuente.\n
    Args:
        hv_source (pyvisa.resource.resource): Instrumento
        desiredVoltage (float): Voltaje nominal deseado a la salida de la fuente. Volts
        maxAbsolutePermissibleError (float): Maximo error (absoluto) permitido a la salida de la fuente. Volts
        checkPeriod (float): Periodo de chequeo del valor de voltaje a la salida de la fuente. Seconds
        lastDelay (float): Tiempo de espera de seguridad una vez que la salida de la fuente se encuentra dentro del rango. Seconds
        (desiredVoltage-maxAbsolutePermissibleError, desiredVoltage+maxAbsolutePermissibleError)
        voltageStabilizationTimeout (long): Tiempo máximo dado a la funcion para chequear la salida de la fuente de alimentacion. Seconds
    Returns:
        True si el valor leido a la salida de la fuente de alimentacion se encuentra dentro del rango
        (desiredVoltage-maxAbsolutePermissibleError, desiredVoltage+maxAbsolutePermissibleError) \n
        False si el valor leido a la salida de la fuente de alimentación no llega a situarse dentro del rango
        (desiredVoltage-maxAbsolutePermissibleError, desiredVoltage+maxAbsolutePermissibleError) y el tiempo de ejecucion
        de la funcion supera o iguala el valor dado por el voltageStabilizationTimeout
    """

    initialTime = time.time() * 1000
    deadTime = initialTime + voltageStabilizationTimeout * 1000

    permissibleRange = (desiredVoltage - maxAbsolutePermissibleError, desiredVoltage + maxAbsolutePermissibleError)

    while True:
        sleep(checkPeriod)

        # primero chequeamos el timeout
        actualTime = time.time() * 1000
        if actualTime >= deadTime:
            return False  # Se ha cumplido el timeout

        # si no se ha cumplido el timeout miramos la tension a la salida de la fuente y comprobamos si se encuentra
        # dentro del rango permitido
        readedVoltage = readVoltageFromHVSource(hv_source)
        if permissibleRange[0] < readedVoltage < permissibleRange[1]:
            break

    sleep(lastDelay)
    return True


def getHVSourceStatus(hv_source):
    delay = 1
    term = ""

    sendCommandToInstrument(hv_source, "STATUS,DI", term, 0, delay)
    response = hv_source.read_raw()

    return response


def setHVOutputVoltage(hv_source, targetVoltage, voltageStabilizationTimeout=10):
    """
    Funcion sincrona que permite settear una determinada tension (targetVoltage) en la fuente de alimentacion (hv_source) y
    espera a la estabiizacion de esta segun unos criterios definidos por un error, una frecuencia de actualizacion y un tiempo de timeout.\n
    :param hv_source: pyvisa.resource.resorce como la fuente de alimentacion
    :param voltage:   float con el voltage deseado a la salida de la fuente de alimentacion. Kv
    :param voltageStabilizationTimeout: Tiempo de espera que toma la funcion para comprobar qe la salida de
    la fuente de alimentacion ofrece el voltage deseado. Seconds
    :return: None
    """
    term = ""
    hvSource_OutputVoltageStabilization_Success = False

    while not hvSource_OutputVoltageStabilization_Success:
        # Actualizamos la tension en la fuente
        print(colored("Setting the H Source to --> " + "U," + "{:.3f}".format(targetVoltage) + "kV", "yellow"))
        sendCommandToInstrument(hv_source, "U," + "{:.3f}".format(targetVoltage) + "kV", term, 0, 0.5)
        print(colored("Waiting for voltage stabilization...", "grey", "on_white"))
        hvSource_OutputVoltageStabilization_Success = waitForVoltageStabilization(hv_source, targetVoltage*1000, 10, 1, 1,
                                                                                   voltageStabilizationTimeout)  # maxAbsolutePermissibleError is 10V
        if not hvSource_OutputVoltageStabilization_Success:
            print(colored(
                "Voltage Stabilization WatchDog has raised an exception. Voltage stabilization is taking too much time...",
                "red"))


def start_process(K2400_gpibAddress,
                  HVSource_gpibAddress,
                  initialVoltage,
                  finalVoltage,
                  pointsVoltage,
                  measureDelay_ms,
                  rampVoltage,
                  outputCurrentLimit,
                  enableKill,
                  ammeterRange,
                  ammeterCompliance,
                  ammeterNPLCs,
                  resultsFilePath):

    delay = 0.5  # in s
    term = ""

    k2400, hv_source = getInstruments(K2400_gpibAddress, HVSource_gpibAddress)


    #!!!!!!!!!MUY IMPORTANTE. PARA PROTEGER LA TENSION QUE VEN LOS BORNES DEL AMPERIMETRO!!!!!!!!!!!!!!
    #SIEMPRE AMMETER ON ANTES DE APLICAR VOLTAJE O INICIALIZAR LA FUENTE QUE PUEDE TENER VOLTAJE ALTO ANTES DE EMPEZAR EL PROCESO

    # K2400 ON
    sendCommandToInstrument(k2400, ":OUTP:STAT ON", term, 0, delay)

    #importante inicializar primero la fuente de voltage para bajar a cero antes de inicializar el amperimetro
    initializeHVSource(hv_source, rampVoltage, outputCurrentLimit, enableKill)
    initializeK2400(k2400, ammeterCompliance, ammeterNPLCs, ammeterRange)


    # #calculo del step voltage
    stepVoltage = (finalVoltage - initialVoltage) / pointsVoltage
    nextVoltage = initialVoltage

    finalProcess = False

    # HV source ON
    sendCommandToInstrument(hv_source, "HV,ON", term, 0, delay)

    # Here you have to write to file
    f = open(resultsFilePath, "a")
    f.truncate(0)

    #mean_current calculation
    previous_current = 0.0
    sum_current = 0.0
    mean_current = 0.0
    n_steps = 0

    #current threshold in percent of current value
    current_threshold = 5000
    current_overflow = False

    #file format
    sep = "\t"

    while not finalProcess:

        if nextVoltage > finalVoltage or current_overflow:
            finalProcess = True

        else:

            setHVOutputVoltage(hv_source, nextVoltage/1000, voltageStabilizationTimeout)

            print(colored("Waiting for measure delay = " + str(measureDelay_ms/1000) + " seconds", "grey", "on_white"))
            sleep(measureDelay_ms/1000)

            # Una vez el voltaje de la fuente es estable a su salida podremos considerar que actualvoltage = nextvoltage
            actualVoltage = nextVoltage

            # Here you have to measure the hv_source volatge
            hv_source_voltage = readVoltageFromHVSource(hv_source)
            print(colored("Voltage source --> " + str(hv_source_voltage) + "V", "cyan"))
            # Here you have to measure the current of the k2400
            sendCommandToInstrument(k2400, ":READ?", term, 0, 0.5)
            ammeter_response = k2400.read_raw()

            ammeter_decoded_response = ammeter_response.decode(encoding='ascii', errors='ignore')
            ammeter_decoded_response = ammeter_decoded_response[:-1]
            ammeter_decoded_response = ammeter_decoded_response.split(",")

            ammeter_current = float(ammeter_decoded_response[1])
            if n_steps == 0:
                previous_current = ammeter_current

            print(colored("Previous Current --> " + str(previous_current) + "A", "cyan"))
            print(colored("Ammeter Current --> " + str(ammeter_current) + "A", "cyan"))
            print(colored("Current Delta --> " + str(abs(ammeter_current - previous_current)) + "A", "cyan"))
            print(colored("Max Current Delta --> " + str(abs((current_threshold / 100.0) * previous_current)) + "A", "cyan"))

            # Here you have to write to file
            f.write(str(hv_source_voltage) + sep + str(abs(ammeter_current)) + "\n")
            f.flush()

            #check if the ammeter_current overflows
            if abs(ammeter_current-previous_current) > abs((current_threshold / 100.0) * previous_current):
                #ammeter_currrent overflow
                current_overflow = True
                print(colored("CURRENT OVERFLOW!!!!!!!","red"))
            else:
                nextVoltage = actualVoltage + stepVoltage
                previous_current = ammeter_current
                n_steps = n_steps + 1

    message = "Closing the results file!!!"
    printMessage(message, "*", "*")
    f.close()

    message = "Process Complete!!!"
    printMessage(message, "*", "*")

    message = "Powering off instruments!!!"
    printMessage(message, "*", "*")

    # Setting output voltage to zero
    setHVOutputVoltage(hv_source, 0, 60)

    # HV source off
    sendCommandToInstrument(hv_source, "HV,OFF", term, 0, delay)

    message = "Now HV Source is safe!!!!"
    printMessage(message, "*", "*")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    process_config_file_path = "process_config_file.json"

    K2400_gpibAddress, \
    HVSource_gpibAddress, \
    initialVoltage, \
    finalVoltage, \
    pointsVoltage, \
    measureDelay_ms, \
    rampVoltage, \
    outputCurrentLimit, \
    enableKill, \
    ammeterRange, \
    ammeterCompliance, \
    ammeterNPLCs, \
    resultsFilePath, \
    resultsFilePathExtension = readConfigFile(process_config_file_path)

    # print(measureDelay_ms)
    # exit(0)

    # counter = 0
    #
    # while True:
    #     start_process(K2400_gpibAddress,
    #                   HVSource_gpibAddress,
    #                   initialVoltage,
    #                   finalVoltage,
    #                   pointsVoltage,
    #                   measureDelay_ms,
    #                   rampVoltage,
    #                   outputCurrentLimit,
    #                   enableKill,
    #                   ammeterRange,
    #                   ammeterCompliance,
    #                   ammeterNPLCs,
    #                   resultsFilePath + str(counter) + "." + resultsFilePathExtension)
    #     counter += 1

    dut_reference = ""
    start_process(K2400_gpibAddress,
                  HVSource_gpibAddress,
                  initialVoltage,
                  finalVoltage,
                  pointsVoltage,
                  measureDelay_ms,
                  rampVoltage,
                  outputCurrentLimit,
                  enableKill,
                  ammeterRange,
                  ammeterCompliance,
                  ammeterNPLCs,
                  resultsFilePath + str(dut_reference) + "." + resultsFilePathExtension)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
