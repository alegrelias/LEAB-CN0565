# Como usar correctamente el script impedance_measure_processor

En esta carpeta vas a encontrar:

- carpeta "data"
- freq.txt
- nombres.txt
- impedance_measure_processor.py

## Carpeta "data"
En esta carpeta debes subir los archivos xlsx que genera la herramienta LCRmeter luego de realizar las mediciones.

## freq.txt
En este archivo de texto debes escribir la lista de frecuencias que utilizaste para realizar las mediciones, separandolas con un ENTER y utilizando la notacion de punto en caso de que sea un numero de punto flotante.

## nombre.txt
En este archivo de texto debes escribir la lista de nombres que llevarán los encabezados al momento de generarse el archivo final, dichos nombres deben separarse con un ENTER

## impedance_measure_processor.py
Este archivo es el script de python propiamente dicho, en el cual pueden cambiarse:
- los nombres de las rutas
- el orden de mediciones sobre un mismo elemento
- el nombre del archivo resultante
- los numeros de los archivos en la carpeta "data"
- que archivos deben ignorarse por errores

