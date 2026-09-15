import adi
import cmath

# Falta cambiar el nombre de los pines
#Los nombres los uso para crear un eventual csv o mostrar datos
nom_electrodo = [
    "pin_0", "pin_1",
    "pin_2", "pin_3",
    "pin_4", "pin_5",
    "pin_6", "pin_7",
    "pin_8", "pin_9",
    "pin_10", "pin_11",
    "pin_12", "pin_13",
    "pin_14", "pin_15"
]

#TODO: preguntar a antonio si obligatoriamente se asocia cada electrodo con el que esta debajo de el, ej: E1 con E0
def seleccionar_electrodos():
    while True:
        try:
            elec_1 = int(input("Selecciona el electrodo: "))
            if 0 <= elec_1 <= 15:
                break
            else:
                print("ERROR: El pin no existe")
        except ValueError:
            print("ERROR: Numero invalido")

    #Agrupar pares contiguos (1-0, 3-2, 5-4,...)
    if elec_1 % 2 != 0:
        elec_2 = elec_1 - 1
    else:
        elec_2 = elec_1 + 1

    return elec_1, elec_2

def main():

    pos_elec_1, pos_elec_2 = seleccionar_electrodos()

    #NOTA: el puerto serial debe cambiarse dependiento el dispositivo
    try:
        cn0565 = adi.cn0565(uri="serial:COM7,230400,8n1n")
    except Exception as exc:
        print(f"ERROR: No se pudo conectar a la placa: {exc}")
        return

    amplitude = 100
    frequency = 10000
    baudrate = 230400

    cn0565.gpio1_toggle = True
    cn0565.excitation_amplitude = amplitude
    cn0565.excitation_frequency = frequency
    cn0565.magnitude_mode = False
    cn0565.impedance_mode = True

    print("--------------------------------------------------------------")
    print("Amplitude: " + str(amplitude) + "mV")
    print("Frequency: " + str(frequency) + " Hz")
    print("Baud Rate: " + str(baudrate))
    print("--------------------------------------------------------------\n")

    cn0565.immediate = True

    cn0565.add(0x71)
    cn0565.add(0x70)

    #Si tiene el atributo openall lo ejecuta, abriendo todos los circuitos
    if hasattr(cn0565, 'open_all'):
        cn0565.open_all()


    # TODO: preguntar a Antonio si los valores asignados a estas variables corresponden a la posicion de las salidas del ad5940 y porque estan invertidos en el codigo example.py
    # F+ F- inyectan
    # S+ S- Sensan
    F_PLUS = 0
    S_PLUS = 1
    S_MINUS = 2
    F_MINUS = 3

    #Conexion de electrodos F+, S+ con pin 1 y electrodos F-, S- con pin 0
    cn0565[pos_elec_1][F_PLUS] = True
    cn0565[pos_elec_1][S_PLUS] = True
    cn0565[pos_elec_2][S_MINUS] = True
    cn0565[pos_elec_2][F_MINUS] = True

    try:
        # Command CN0565 to measure impedance at specified electrodes using specified frequency
        res = cn0565.channel["voltage0"].raw
    except Exception as e:
        print(f"ERROR al intentar leer los datos: {e}")
        return

    (mag, radph) = cmath.polar(res)
    degph = radph * 180 / cmath.pi
    degphb = 360 + degph

    print("--------------------------------------------------------------")
    print("Electrode " + str(pos_elec_1) + " - Electrode " + str(pos_elec_2))
    print(nom_electrodo[pos_elec_1] + " - " + nom_electrodo[pos_elec_2])
    print("--------------------------------------------------------------")
    print("Rectangular: " + str(res))
    print(f"Polar: Magnitude:{mag} Phase(degrees): {degph} or {degphb}")
    print("Real Impedance: " + str(res.real))
    print("Imaginary Impedance: " + str(res.imag))
    print("--------------------------------------------------------------")
    print("\n")

main()
