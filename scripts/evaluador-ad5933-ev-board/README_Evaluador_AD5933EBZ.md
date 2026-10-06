# Evaluador AD5933EBZ

Aplicación de escritorio en Python para analizar **5 mediciones repetidas**
de un mismo resistor tomadas con la EVAL-AD5933EBZ.

## Configuración experimental esperada
- Frecuencia: 5 kHz a 100 kHz
- Paso: 1 kHz
- 5 repeticiones por resistor
- Se ingresa manualmente el valor de referencia del resistor

## Parámetros calculados por frecuencia
- Media de |Z|
- Desviación estándar
- Coeficiente de variación (CV %)
- Mínimo, máximo y rango
- IC 95 % de la media
- Bias en ohmios
- Error relativo (%)
- Error absoluto relativo (%)
- RMSE
- Fase media
- Desviación estándar de fase
- Error absoluto de fase respecto de 0°

## Resumen del barrido
- CV medio y máximo
- SD media
- Bias medio
- Error medio con signo
- MARE
- Error absoluto máximo
- RMSE global
- Indicadores de fase

## Gráficas
1. Cinco mediciones de impedancia + media ± 1 SD + referencia
2. Error relativo vs frecuencia
3. CV vs frecuencia
4. Fase vs frecuencia

## Requisitos

Instalar Python 3 y luego:

    pip install numpy pandas matplotlib

Tkinter normalmente viene incluido con Python para Windows.

## Uso

    python evaluador_ad5933ebz.py

1. Ingrese la resistencia de referencia en ohmios.
2. Seleccione exactamente 5 archivos CSV.
3. Pulse **Analizar**.
4. Revise la tabla y el resumen.
5. Use **Mostrar gráficas**.
6. Use **Exportar resultados** para guardar CSV y PNG.

## Formato de entrada

El programa intenta reconocer CSV estándar y también el formato usado por
el software de la AD5933EBZ con:

    Frequency, Impedance, Phase, Real, Imaginary, Magnitude

Incluye tolerancia para coma decimal y separadores por espacios.
