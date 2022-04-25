# gpib_example
Prototipo Leakage HV_Source_Measure_

version 1.1

Bug fixes:

1. Problema de loop infinito en la llamada a la funcion waitForVoltageStabilization.

News:

1. Añadida funcion setHVOutputVoltage(hv_source, targetVoltage, voltageStabilizationTimeout=10)
para ordenar y simplificar el mantenimiento del código

Next:

1. Ofrecer la posibilidad de un config.json exclusivo para parametros internos (no relacionados con el proceso de sweep propiamente dicho)
Parametros internos que pueden ser los delays en el envio de comandos gpib y lectura de instrumentos o delays en la 
frecuencia de lectura de la tension en la fuente de voltage, etc...

2. Configurar voltageStabilizationTimeout en funcion de la rampa de voltage de la fuente y el delta V
