# gpib_example
Prototipo Leakage HV_Source_Measure_

version 1.2

Bug fixes:


News:

2. Reorganizado el orden en que se ejecuta la configuracion de los instrumentos para proteger el amperimertro


Next:

1. Ofrecer la posibilidad de un config.json exclusivo para parametros internos (no relacionados con el proceso de sweep propiamente dicho)
Parametros internos que pueden ser los delays en el envio de comandos gpib y lectura de instrumentos o delays en la 
frecuencia de lectura de la tension en la fuente de voltage, etc...

2. Configurar voltageStabilizationTimeout en funcion de la rampa de voltage de la fuente y el delta V
