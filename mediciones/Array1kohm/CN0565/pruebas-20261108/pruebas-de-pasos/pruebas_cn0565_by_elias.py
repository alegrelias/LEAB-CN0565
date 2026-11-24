import adi
import cmath
import time
import json
import datetime

electrode_name = [
    "R26_C56_C57", "R24_C54_C56", "R22_C52_C54", "R18_C50_C52",
    "R16_C48_C50", "R14_C46_C48", "R12_C44_C46", "R10_C42_C44",
    "R8_C40_C42", "R9_C38_C40", "R4_C36_C38", "R2_C29_C36",
    "R1_C29_C33", "R3_C33_C37", "R5_C37_C39", "R7_C39_C41",
]

def measure_cn0565(count, freq, amp):
    print("Entra al measure_cn0565")
    print(f"Amplitud seleccionada durante la medicion: {amp}")

    cn0565 = adi.cn0565(uri="serial:COM3,230400,8n1n")

    cn0565.gpio1_toggle = True
    cn0565.excitation_amplitude = amp
    cn0565.excitation_frequency = freq
    cn0565.magnitude_mode = False
    cn0565.impedance_mode = True
    cn0565.immediate = True
    cn0565.add(0x71)
    cn0565.add(0x70)

    # Variables locales para guardar resultados generales
    all_real_parts = []
    all_imag_parts = []

    for i in range(count):
        # Listas temporales que se reinician en cada iteración
        iter_real = []
        iter_imag = []

        Electrode_Iter = iter(range(0, 26))
        for neg_e in Electrode_Iter:
            pos_e = next(Electrode_Iter)

            cn0565.open_all()
            cn0565[pos_e][0] = True
            cn0565[pos_e][1] = True
            cn0565[neg_e][2] = True
            cn0565[neg_e][3] = True

            res = cn0565.channel["voltage0"].raw

            iter_real.append(res.real)
            iter_imag.append(res.imag)

        # Guarda la pasada completa
        all_real_parts.append(iter_real)
        all_imag_parts.append(iter_imag)

    # Limpieza final del hardware y memoria
    cn0565.open_all()
    del cn0565

    return all_real_parts, all_imag_parts


def save_data(datos_guardar):
    board = datos_guardar.get('Board#')
    z_test = datos_guardar.get('Z_board')
    freq = datos_guardar.get('Frequency')

    # Formato del nombre
    fecha_actual = datetime.datetime.now()
    nom_date = (fecha_actual.strftime('%Y%m%d%H%M%S'))
    nombre = nom_date + '_' + board + '_' + z_test + '_' + str(freq)
    ext = '.json'

    nom_archivo = nombre + ext

    # Creación y escritura del archivo json
    with open(nom_archivo, 'x') as outfile:
        json.dump(datos_guardar, outfile, indent=4)

    return nom_archivo


def main():
    board = "placa_2"
    z_test = "resis_mix"
    
    count = 5
    ampl = 100
    freq = 100 * 1000
    print(f"--- Midiendo a Frecuencia: {freq} Hz y amplitud: {ampl}mV ---")

    inicio = time.time()
    
    fin = time.time()
    real_part, imag_part = measure_cn0565(count, freq, ampl)
    duracion_med = fin - inicio
    
    datos_guardar = {
        'Board#': board, 
        'Z_board': z_test, 
        'Count': count, 
        'Frequency': freq, 
        'Amplitude': ampl, 
        'Real Impedance': real_part, 
        'Imaginary Impedance': imag_part, 
        'Delay [seg]': duracion_med
    }
    
    # Guarda un JSON distinto por cada escalón de frecuencia
    nombre_archivo = save_data(datos_guardar)
    print(f"Guardado en: {nombre_archivo}")

    print(f"\n--- Barrido Completo finalizado en {duracion_med:.2f} segundos ---")

if __name__ == "__main__":
    main()