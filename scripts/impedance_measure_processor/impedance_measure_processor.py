import numpy as np
import pandas as pd
import os

def cargar_datos(ruta):
    #Usamos la funcion de numpy que nos permite leer csv, utilizando solo las columnas 0 y 1 e ignorando las que tienen error de formato
    datos = np.genfromtxt(ruta, delimiter=',', usecols=(0, 1))
    complejos = datos[:,0] + datos[:,1] * 1j
    return complejos

if __name__ == "__main__":

    # Cantidad de veces que se va a medir sobre un mismo electrodo/componente
    orden = 1
    
    ruta_freq = "freq.txt"
    ruta_elemento = "nombres.txt"

    # Usamos la manera nativa de leer archivos
    with open(ruta_freq, "r") as f:
        frecuencias = np.array([float(linea.strip()) for linea in f if linea.strip()])

    with open(ruta_elemento, "r") as archivo:
        elem_medido = [linea.strip() for linea in archivo]

    # Lista de archivos descartados por errores (ejemplo)
    archivos_ignorados = []

    # Creamos una lista de los archivos que si vamos a usar
    # Cambiar por numeros correspondientes
    primer_archivo = 814
    ultimo_archivo = 825
    archivos_validos = [n for n in range(primer_archivo, ultimo_archivo + 1) if n not in archivos_ignorados]

    nombre_excel = "Resultados.xlsx"

    print(f"Generando archivo excel: {nombre_excel}")

    with pd.ExcelWriter(nombre_excel, engine="openpyxl") as writer:
       
       #En caso de haber realizado una medicion por componente guardamos todo en la misma hoja
       if orden == 1:

        columnas_tabla = {'Frecuencia (Hz)': frecuencias}
        # Recorremos los archivos validos desde el primero, haciendo tandas que dependen del orden
        for i in range(0, len(archivos_validos), orden):

            grupo_mediciones = archivos_validos[i:i + orden]

            if len(grupo_mediciones) < orden:
                print(f"\n[!] Aviso: Los últimos archivos {grupo_mediciones} no completan el oden de medida. Se ignoran.")
                break

            #Cambiar por el path correspondiente
            rutas = [f"data/E498x{n}.csv" for n in grupo_mediciones]

            # Verificamos que tengamos todos los archivos
            archivos_faltantes = [ruta for ruta in rutas if not os.path.exists(ruta)]
            if archivos_faltantes:
                print(f"\n[!] Error: Faltan los archivos {archivos_faltantes}. Saltando...")
                continue

            # Cargamos los datos y forzamos a que midan exactamente lo mismo que las frecuencias
            tandas = [cargar_datos(ruta)[:len(frecuencias)] for ruta in rutas]
            mediciones_totales = np.array(tandas)

            tanda = tandas[0]
            
            nombre_elemento = elem_medido[i]
            nombre_elem_limpio = nombre_elemento.replace("(", "").replace(")", "").replace(", ", "-")

            columnas_tabla[f'{nombre_elem_limpio} Real'] = tanda.real
            columnas_tabla[f'{nombre_elem_limpio} Imag'] = tanda.imag

            
        tabla = pd.DataFrame(columnas_tabla)

        nombre_hoja = "Medicion"

        tabla.to_excel(writer, sheet_name=nombre_hoja, index=False)

        print(f"-> Datos de {grupo_mediciones} guardados en la hoja: {nombre_hoja}")
       else:
        # Recorremos los archivos validos desde el primero, haciendo tandas que dependen del orden
        for i in range(0, len(archivos_validos), orden):

            grupo_mediciones = archivos_validos[i:i + orden]

            if len(grupo_mediciones) < orden:
                print(f"\n[!] Aviso: Los últimos archivos {grupo_mediciones} no completan el oden de medida. Se ignoran.")
                break

            #Cambiar por el path correspondiente
            rutas = [f"E498x{n}.csv" for n in grupo_mediciones]

            # Verificamos que tengamos todos los archivos
            archivos_faltantes = [ruta for ruta in rutas if not os.path.exists(ruta)]
            if archivos_faltantes:
                print(f"\n[!] Error: Faltan los archivos {archivos_faltantes}. Saltando...")
                continue

            tandas = [cargar_datos(ruta) for ruta in rutas]
            mediciones_totales = np.array(tandas)

            columnas_tabla = {'Frecuencia (Hz)': frecuencias}

            for idx, tanda in enumerate(tandas):
                columnas_tabla[f'Tanda {idx + 1} Real'] = tanda.real
                columnas_tabla[f'Tanda {idx + 1} Imag'] = tanda.imag

            # Calculamos datos estadisticos de la tanda (promedio y desvio)
            promedios = np.mean(mediciones_totales, axis=0)
            desvios = np.std(mediciones_totales, axis=0)
            columnas_tabla['Promedio Real'] = promedios.real
            columnas_tabla['Promedio Imag'] = promedios.imag
            columnas_tabla['Desvio Estandar'] = desvios

            tabla = pd.DataFrame(columnas_tabla)

            indice_nombre = i // orden
            nombre_elemento = elem_medido[indice_nombre]
            nombre_elem_limpio = nombre_elemento.replace("(", "").replace(")", "").replace(", ", "-")
            nombre_hoja = f"par{nombre_elem_limpio}_{indice_nombre}"

            tabla.to_excel(writer, sheet_name=nombre_hoja, index=False)

            print(f"-> Datos de {grupo_mediciones} guardados en la hoja: {nombre_hoja}")
