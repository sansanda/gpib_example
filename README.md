# gpib_example
Prototipo Leakage HV_Source_Measure_

version 1.2.1

Bug fixes:

1. Color no se ve cuando se ejecuta el programa fuera del IDE, en linea de comandos de windows
News:

Next:

1. Ofrecer la posibilidad de un config.json exclusivo para parametros internos (no relacionados con el proceso de sweep propiamente dicho)
Parametros internos que pueden ser los delays en el envio de comandos gpib y lectura de instrumentos o delays en la 
frecuencia de lectura de la tension en la fuente de voltage, etc...

2. Configurar voltageStabilizationTimeout en funcion de la rampa de voltage de la fuente y el delta V

3. Implementar boton de emergencia