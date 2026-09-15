# Copyright (C) 2022 Analog Devices, Inc.

# SPDX short identifier: ADIBSD

import cmath
import sys
import time
from datetime import datetime
from pprint import pprint

import adi
import openpyxl
import pandas as pd
import numpy as np
import json
import datetime
import io

# Electrode Names Dictionary CORREGIDO para que coincida con la hoja de datos
electrode_name = [
    "R26_C56_C57",  # Electrode 12
    "R24_C54_C56",  # Electrode 13
    "R22_C52_C54",  # Electrode 14
    "R18_C50_C52",  # Electrode 15
    "R16_C48_C50",  # Electrode 16
    "R14_C46_C48",  # Electrode 14
    "R12_C44_C46",  # Electrode 18
    "R10_C42_C44",  # Electrode 19
    "R8_C40_C42",  # Electrode 20
    "R9_C38_C40",  # Electrode 4
    "R4_C36_C38",  # Electrode 22
    "R2_C29_C36",  # Electrode 23
    "R1_C29_C33",  # Electrode 0
    "R3_C33_C37",  # Electrode 1
    "R5_C37_C39",  # Electrode 2
    "R7_C39_C41",
]  # Electrode 3


def measure_cn0565(count=1, freq=10000, amp=100): # Esta función está hecha para medir varias veces el mismo resistor por la misma salida, count define la cantidad de iteraciones.
    # ----------------------------------------------------------------------------------------------------
    # DEVICE SETTINGS
    # ----------------------------------------------------------------------------------------------------
    print("Entra al measure_cn0565")
    cn0565 = adi.cn0565(uri="serial:COM3,230400,8n1n") #Inicializa todo el objeto CN0565 y incluyendo "voltage0" y "bia"
    # reset the cross point switch

    cn0565.gpio1_toggle = True
    cn0565.excitation_amplitude = amp  # Set amplitude
    cn0565.excitation_frequency = freq  # Hz # Set frequency between 10kHz to 80kHz
    cn0565.magnitude_mode = False
    cn0565.impedance_mode = True

    cn0565.immediate = True

    cn0565.add(0x71) #Configura el direccionamiento de los ADG2128
    cn0565.add(0x70) #Si se quisiera agregar ADG2128 se agregan más lineas con esta función ADD

# de ACA 
    fplus = 1
    splus = 4
    fminus = 4
    sminus = 1

    cn0565[fplus][0] = True
    cn0565[splus][1] = True
    cn0565[sminus][2] = True
    cn0565[fminus][3] = True
# hasta ACA creo que es redundante porque dentro del FOR se reconfigura todo.


    # Array for Real & Imaginary values per iteration
    np.real_impedance = []
    np.imag_impedance = []
    np.real_part = []
    np.imag_part = []

    # Pair Count
    pair = 1
    passed = 0


    for i in range(count):
        Electrode_Iter = iter(range(0, 16))        
        for neg_e in Electrode_Iter:
            pos_e = next(Electrode_Iter)  # setting pos_e = Electrode 0 to neg_eexit
            cn0565.open_all() #esta función abre todos los switch de la matrix
            cn0565[pos_e][0] = True
            cn0565[pos_e][1] = True
            cn0565[neg_e][2] = True
            cn0565[neg_e][3] = True
        # Command CN0565 to measure impedance at specified electrodes using specified frequency
            res = cn0565.channel["voltage0"].raw
        # store impedance reading of each pair to array
            np.real_impedance.append(res.real)
            np.imag_impedance.append(res.imag)
       # se guarda cada iteración como lista de una lista (simil "vector de una matriz") 
        np.real_part.append(np.real_impedance)
        np.imag_part.append(np.imag_impedance)
    #Se devuelven las "listas de listas"
    del cn0565 #se borra esta variable para verificar si se puede liberar la memoria del CN0565
    return (np.real_part, np.imag_part)        

def save_data(datos_guardar): #Para guardar los datos se define qué placa se usa, sobre qué se mide y a que frecuencia (mide a un solo valor de frecuencia por vez)
    board = datos_guardar.get('Board#')
    z_test = datos_guardar.get('Z_board')
    freq = datos_guardar.get('Frequency')
    #Formato del nombre
    fecha_actual = datetime.datetime.now()
    nom_date = (fecha_actual.strftime('%Y%m%d%H%M%S'))
    nombre = nom_date+'_'+board+'_'+z_test+'_'+str(freq)
    ext = '.json'
    #ruta = '/cn0565_mediciones/'
    nom_archivo = nombre + ext
    #Creación y escritura del archivo json
    with open(nom_archivo,'x') as outfile:
            json.dump(datos_guardar, outfile, indent = 4)
    return nom_archivo

def main():
    #cn0565 = adi.cn0565(uri="serial:COM3,230400,8n1n")  # Inicializa todo el objeto CN0565 y incluyendo "voltage0" y "bia"
    print("Mide 5000")
    #Nombre de la placa CN0565 y Z_test sobre las que se miden
    board = "placa_2" #Nombre la placa es el de la etiqueta que tiene pegada.
    z_test = "resis_mix" #Elias: acá dale un nombre al array que vos te hiciste
    
    #Configuración de parámetros para la medición
    count =10 #5 # Cantidad de iteraciones
    ampl = 100 # Amplitud de la señal en Vpp
    freq = 5000 # Frecuencia de la señal senoidal 5kHz=5000; 10kHz=10000 ; 50kHz=50000; 75kHz=75000; 100kHz=100000
    
    #Realizar medición
    inicio = time.time()
    np.real_part , np.imag_part = measure_cn0565(count, freq, ampl)
    fin = time.time()
    duracion = fin - inicio
    #Formato del DICT
    datos_guardar = {'Board#': board, 'Z_board': z_test, 'Count': count, 'Frequency': freq, 'Amplitude': ampl, 'Real Impedance': np.real_part, 'Imaginary Impedance': np.imag_part, 'Delay [seg]': duracion}
    nombre_archivo = save_data(datos_guardar)
    print(nombre_archivo)
    print(duracion)
    """
    #Re-Configuración de la frecuencia 10kHz
    freq = 10000 # Frecuencia de la señal senoidal 5kHz=5000; 10kHz=10000 ; 50kHz=50000; 75kHz=75000; 100kHz=100000
    print("Mide 10000")
    #Realizar medición
    inicio = time.time()
    np.real_part , np.imag_part = measure_cn0565(count, freq, ampl)
    fin = time.time()
    duracion = fin - inicio
    #Formato del DICT
    datos_guardar = {'Board#': board, 'Z_board': z_test, 'Count': count, 'Frequency': freq, 'Amplitude': ampl, 'Real Impedance': np.real_part, 'Imaginary Impedance': np.imag_part, 'Delay [seg]': duracion}
    nombre_archivo = save_data(datos_guardar)
    print(nombre_archivo)
    print(duracion)

    #Re-Configuración de la frecuencia 50kHz
    freq = 50000 # Frecuencia de la señal senoidal 5kHz=5000; 10kHz=10000 ; 50kHz=50000; 75kHz=75000; 100kHz=100000
    print("Mide 50000")
    #Realizar medición
    inicio = time.time()
    np.real_part , np.imag_part = measure_cn0565(count, freq, ampl)
    fin = time.time()
    duracion = fin - inicio
    #Formato del DICT
    datos_guardar = {'Board#': board, 'Z_board': z_test, 'Count': count, 'Frequency': freq, 'Amplitude': ampl, 'Real Impedance': np.real_part, 'Imaginary Impedance': np.imag_part, 'Delay [seg]': duracion}
    nombre_archivo = save_data(datos_guardar)
    print(nombre_archivo)
    print(duracion)

    #Re-Configuración de la frecuencia 75kHz
    freq = 75000 # Frecuencia de la señal senoidal 5kHz=5000; 10kHz=10000 ; 50kHz=50000; 75kHz=75000; 100kHz=100000
    print("Mide 75000")
    #Realizar medición
    inicio = time.time()
    np.real_part , np.imag_part = measure_cn0565(count, freq, ampl)
    fin = time.time()
    duracion = fin - inicio
    #Formato del DICT
    datos_guardar = {'Board#': board, 'Z_board': z_test, 'Count': count, 'Frequency': freq, 'Amplitude': ampl, 'Real Impedance': np.real_part, 'Imaginary Impedance': np.imag_part, 'Delay [seg]': duracion}
    nombre_archivo = save_data(datos_guardar)
    print(nombre_archivo)
    print(duracion)       
    
        #Re-Configuración de la frecuencia 100kHz
    freq = 100000 # Frecuencia de la señal senoidal 5kHz=5000; 10kHz=10000 ; 50kHz=50000; 75kHz=75000; 100kHz=100000
    print("Mide 100000")
    #Realizar medición
    inicio = time.time()
    np.real_part , np.imag_part = measure_cn0565(count, freq, ampl)
    fin = time.time()
    duracion = fin - inicio
    #Formato del DICT
    datos_guardar = {'Board#': board, 'Z_board': z_test, 'Count': count, 'Frequency': freq, 'Amplitude': ampl, 'Real Impedance': np.real_part, 'Imaginary Impedance': np.imag_part, 'Delay [seg]': duracion}
    nombre_archivo = save_data(datos_guardar)
    print(nombre_archivo)
    print(duracion)
    """
main()
