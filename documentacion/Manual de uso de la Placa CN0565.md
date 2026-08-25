# Índice

1.  **Introducción y Especificaciones Técnicas** 
	
	1.1. Descripción corta de la CN0565
	
	1.2. Diagrama en bloques simplificado
	
	1.3. Características y jumpers P7/P1
    
2. **Requisitos de Software y Control de Versiones**
	2.1. Hardware necesario
	2.2. Software necesario
	2.3. Software de utilidad
    
3. **Configuración del Entorno Virtual y Dependencias** (`venv`, `pyadi-iio`, `pyeit`, `openpyxl`)
	3.1. Entorno Virtual  'env'
	3.2. Clonar la librería libiio en la carpeta del proyecto
	3.3. Instalar pylibiio  y pyadi-iio mediante el comando "pip" en el entorno virtual
	3.4. Clonar los scripts de prueba escritos en python
	3.5. Descargar requerimientos de la librería pyadi-iio
    
4. **Flujo de Trabajo y Verificación de Diagnóstico**
    
    4.1. Flasheo y verificación en consola serie (Tera Term a 115200)
    4.2. Verificación de abstracción de hardware con `iio_info` (a 230400)
        
5. **Ejecución de Scripts y Captura de Datos**
    
    5.1. Medición de punto único (`cn0565_example_single.py`)
        
6. **Resolución de Problemas Comunes (Troubleshooting)** (Timeouts 138, puertos bloqueados, error de rutas en OneDrive)

# 1. Introducción y Especificaciones Técnicas
## 1.1. Descripción corta de la CN0565
La placa CN0565 es un sistema de medición de impedancia con la posibilidad de tomar mediciones en configuración bipolar o tetrapolar. Su etapa de _matrix switch_ le brinda la posibilidad realizar tomografía por impedancia eléctrica (EIT).
Su potencialidad de realizar EIT, le permite a la plataforma realizar un mapeo de conductividades que puede ser reconstruido utilizando una repetida  serie de mediciones con electrodos ubicados en diferentes lugares de la superficie de la muestra. Soporta setups de mediciones de hasta 24 electrodos. El diseño usa un par de _matrix switches_ analógicos de 8x12 (ADG2128, Analog Devices), que se activan con una señal de excitación que es aplicada a un par de electrodos cada vez. 

## 1.2. Diagrama en bloques simplificado
![[CN0565 Simplified Block Diagram.png]]

## 1.3. Caracteristicas y jumpers P7/P1:

### Características:
* Soporta setups de medicion de impedancia de hasta 24 pares de electrodos.
* Acepta un rango de frecuencia de un rango desde 0.015 Hz hasta 200kHz
* Para más información visitar: https://wiki.analog.com/resources/eval/user-guides/circuits-from-the-lab/cn0565
### Jumpers
* P7 (Chip Select Mapping) - dejar este en default para el firmware provisto.
![[P7 location.png]]
* P1 
![[P1 Location.png]]

# 2. Requisitos de Software y Control de Versiones

## 2.1. Hardware necesario:
* EVAL-CN0565-ARDZ
* EVAL-ADICUP3029
* PC host con Windows
* Cable micro-USB
## 2.2. Software necesario:
+ Firmware incorporado CN0565 (Archivo HEX)
+ Libiio (driver)
	+ setup: https://github.com/analogdevicesinc/libiio/releases/download/v0.26/libiio-0.26.ga0eca0d2-setup.exe
+ Python (versión más actual)
+ pyadi-iio (librería necesaria)

## 2.3. Software de utilidad
* Instalar Crosscore Serial Flash
	* https://download.analog.com/tools/CrossCoreUtils/Releases/Release_1.8.0/ADI_CrossCoreUtilities-Rel1.8.0.exe
* Instalar PyCharm (Opcional)
	* https://www.jetbrains.com/es-es/pycharm/download/
* Instalar Tera Term
	* [https://github.com/TeraTermProject/teraterm/releases/download/v5.5.2/teraterm-5.5.2-x64.exe](https://github.com/TeraTermProject/teraterm/releases/download/v5.5.2/teraterm-5.5.2-x64.exe)
* Git y GitHub (para facilitar la instalación de librerías y drivers):
	* Git: https://git-scm.com/book/es/v2/Inicio---Sobre-el-Control-de-Versiones-Instalaci%C3%B3n-de-Git
	* GitHub: https://github.com/
  
# 3. Configuración del Entorno Virtual y Dependencias

## 3.1 Entorno Virtual  'env'
- Creamos un `entorno virtual venv` que es un directorio aislado que contiene una instalación independiente de **Python** y sus paquetes, permitiendo gestionar las dependencias de un proyecto específico sin interferir con el sistema global u otros proyectos. Al ejecutar el primer comando debería crearse una carpeta con el nombre que hayamos definido para el entorno virtual (por convención se usa `env`).
```PowerShell
PS C:\Users\elias\OneDrive\LEAB\cn0565> py -m venv env
```

- Para activar nuestro entorno virtual debemos ejecutar el segundo comando, el cual busca dentro de la carpeta de Scripts el comando `activate`, al ejecutar este comando debe aparecernos el nombre de nuestro entorno virtual entre paréntesis. 
```Powershell
PS C:\Users\elias\OneDrive\LEAB\cn0565> .\env\Scripts\activate
(env) PS C:\Users\elias\OneDrive\LEAB\cn0565>
```

## 3.2. Clonar la librería libiio en la carpeta del proyecto
**NOTA:** En varios de los pasos posteriores se puede ver que para instalar dependencias o librerías uso comandos de Git desde la consola, no es obligatorio que se use esta herramienta, pero en caso de que se la quiera usar debe tenerse previamente instalado Git en su ordenador.
```PowerShell
(env) PS C:\Users\elias\OneDrive\LEAB\cn0565> git clone https://github.com/analogdevicesinc/libiio.git
```

## 3.3. Instalar pylibiio  y pyadi-iio mediante el comando "pip" en el entorno virtual
**NOTA:** Al instalar librerías con el comando `pip` dentro del entorno virtual, estas solo van a estar disponibles para este proyecto, dichas librerías pueden ser consultadas en la carpeta `env`. 
**NOTA:** Utilizamos la sintaxis `python -m pip` en lugar de llamar a `pip` directamente para asegurarnos de que la instalación se aplique estrictamente al entorno virtual de Python que está activo y evitar problemas de rutas.

- pylibiio:
```Powershell
(env) PS C:\Users\elias\OneDrive\LEAB\cn0565> python -m pip install pylibiio
```

- pyadi-iio:
```Powershell
(env) PS C:\Users\elias\OneDrive\LEAB\cn0565> python -m pip install pyadi-iio
```

## 3.4. Clonar los scripts de prueba escritos en python
```PowerShell
(env) PS C:\Users\elias\OneDrive\LEAB\cn0565> git clone https://github.com/analogdevicesinc/pyadi-iio.git
```

## 3.5. Descargar requerimientos de la librería pyadi-iio
Luego de clonar los scripts de prueba debemos navegar dentro de la carpeta pyadi-iio e instalar los `requerimientos de software`:

### Navegamos a la carpeta pyadi-iio
```Powershell
(env) PS C:\Users\elias\OneDrive\LEAB\cn0565> cd C:\Users\elias\OneDrive\LEAB\cn0565\pyadi-iio
```
- requirements.txt
```PowerShell
(env) PS C:\Users\elias\OneDrive\LEAB\cn0565\pyadi-iio> python -m pip install -r requirements.txt
```
- requirements_dev.txt
```PowerShell
(env) PS C:\Users\elias\OneDrive\LEAB\cn0565\pyadi-iio>  python -m pip install -r requirements_dev.txt
```
- requirements_doc.txt 
```PowerShell
(env) PS C:\Users\elias\OneDrive\LEAB\cn0565\pyadi-iio>  python -m pip install -r requirements_doc.txt
```
- requirements_prod_test.txt
```PowerShell
(env) PS C:\Users\elias\OneDrive\LEAB\cn0565\pyadi-iio>  python -m pip install -r requirements_prod_test.txt
```

# 4. Flujo de Trabajo y Verificación de Diagnóstico
## 4.1. Flasheo y verificación en consola serie (Tera Term a 115200)
Este firmware puede ayudar a verificar que la placa responde correctamente.
Pasos a seguir para utilizarlo:
- Desconectar la placa

- separar la Adicup3029 de la CN0565

- conectar la adicup a la pc

- Abrir Crosscore Serial Flash y mientras se pulsa el boton BOOT de la placa seleccionar la opción Erase.

- deconectar la adicup

- volver a montar la adicup con la cn0565

- conectar nuevamente la placa a la pc

- arrastrar y soltar el archivo hex

- abrir Tera Term, seleccionar configuración, serial port y poner el baud rate en 115200

- apretar el boton reset de la placa adicup

Resultados de la terminal de Tera Term:
```Bash
Running TinyIIOD server...

                          If successful, you may connect an IIO client application by:

      1. Disconnecting the serial terminal you use to view this message.

                                                                        2. Connecting the IIO client application using the serial backend configured as shown:

                                                                                Baudrate: 230400

                        Data size: 8 bits

                                                Parity: none

                                                                Stop bits: 1

                                                                                Flow control: none
```

## 4.2. Verificación de abstracción de hardware con `iio_info` (a 230400)
**NOTA:** `COM3` es un ejemplo y el número de puerto puede cambiar dependiendo de la PC o de la entrada USB utilizada. revisar el _Administrador de Dispositivos_ de Windows si no está seguro de cuál es su puerto asignado.
Para esta prueba utilizamos el baudrate y el puerto USB que nos arrojó Tera Term y seguimos los siguientes pasos:

- desconectar la placa

- esperar tres segundos y volver a conectar

- copiar el comando en la terminal sin presionar ENTER
```Bash
iio_info -u serial:COM3,230400
```

- presionar el boton RESET de la adicup
	- Este paso es recomendable hacerlo con una pinza o algún elemento pequeño que nos permita llegar al boton RESET sin desmontar la adicup de la cn0565.

- inmediatamente despues presionar enter

Resultados:
```Powershell
(env) PS C:\Users\elias\OneDrive\Escritorio\LEAB\cn0565> iio_info -u serial:COM3,230400

iio_info version: 0.26 (git tag:a0eca0d)

Libiio version: 0.26 (git tag: a0eca0d) backends: xml ip usb serial

IIO context created with serial backend.

Backend version: 1.1 (git tag: 0000000)

Backend description string: no-OS analog 1.1.0-g0000000 #1 Tue Nov 26 09:52:32 IST 2019 armv7l

IIO context has 4 attributes:

        no-OS: 1.1.0-g0000000

        uri: serial:COM3,230400,8n1n

        serial,port: COM3

        serial,description: Dispositivo serie USB (COM3)

IIO context has 2 devices:

        iio:device0: ad5940

                1 channels found:

                        voltage0: bia (input)

                        1 channel-specific attributes found:

                                attr  0: raw value: -14 18

                5 device-specific attributes found:

                                attr  0: impedance_mode value: 0

                                attr  1: magnitude_mode value: 0

                                attr  2: excitation_frequency value: 10000

                                attr  3: excitation_amplitude value: 300

                                attr  4: gpio1_toggle value: 0

                1 debug attributes found:

                                debug attr  0: direct_reg_access value: 0

ERROR: checking for trigger : Invalid argument (22)

        iio:device1: adg2128

                0 channels found:

                1 debug attributes found:

                                debug attr  0: direct_reg_access value: 43069

ERROR: checking for trigger : Invalid argument (22)
```

# 5. Ejecución de Scripts y Captura de Datos

## 5.1. Medición de punto único (`cn0565_example_single.py`)
- Navegar a la carpeta `pyadi-iio\examples\cn0565`:

```Powershell
cd C:\Users\elias\OneDrive\Escritorio\LEAB\cn0565\pyadi-iio\examples\cn0565
```

- Abrir el script de python cn0565_example_single.py y modificar la linea, cambiando el puerto serial y el baudrate:
```python
my_eit = adi.cn0565(uri="serial:COM3,230400")
```

- abrir una terminal en la raíz del ejemplo con el entorno virtual activado y ejecutar el comando:
```Powershell
(env) PS C:\Users\elias\OneDrive\Escritorio\LEAB\cn0565\pyadi-iio\examples\cn0565> python cn0565_example_single.py 0 1 1 0
```

Resultados:
![[resultados prueba example_single.png]]


## 6. Troubleshooting

| Problema                                              | Posible Solución                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| :---------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Error de conexión**                                 | Realizar el flasheo de la EVAL-ADICUP3029 mediante el software Crosscore Serial Flash y posteriormente probar la respuesta de la placa con Tera Term.<br>Al terminar este procedimiento volver a conectar la placa, arrastrar y soltar el archivo `.hex` dentro de la carpeta DAPLINK y acondicionar el entorno virtual para realizar las pruebas.                                                                                                                    |
| **Errores con `venv`**                                | Si el entorno virtual falla al activarse, presenta rutas rotas (común al mover carpetas en OneDrive) o conflictos de permisos:<br>1. Eliminar manualmente la carpeta `env` y volver a crearla con `py -m venv env`.<br>2. Para consultar comandos específicos según el sistema operativo y buenas prácticas de gestión, revisar el **[Tutorial oficial de Python: Entornos virtuales y paquetes](https://docs.python.org/es/3/tutorial/venv.html)**.                  |
| **Errores o dudas con Git (clonado de repositorios)** | Si al ejecutar `git clone` la terminal indica que el comando no se reconoce, verificar que Git esté instalado y agregado al PATH del sistema.<br>Para usuarios no familiarizados con la herramienta o con comandos de control de versiones, consultar el **[Libro oficial Pro Git en español](https://git-scm.com/book/es/v2)** o la **[Guía de instalación de Git](https://git-scm.com/book/es/v2/Inicio---Sobre-el-Control-de-Versiones-Instalaci%C3%B3n-de-Git)**. |
| **Librerías faltantes (análisis y gráficos)**         | Si ocurre un `ModuleNotFoundError` al generar reportes o imágenes, instalar las dependencias con:<br>`python -m pip install openpyxl pyeit matplotlib`                                                                                                                                                                                                                                                                                                                |
| **Error de TimeOut (138)**                            | El puerto COM es de acceso exclusivo. **Se deben desconectar o cerrar siempre Tera Term** antes de ejecutar comandos de `iio_info` o correr los scripts de Python, y viceversa. Si dos programas intentan acceder al mismo puerto simultáneamente, la comunicación fallará con un error de *Timeout*.                                                                                                                                                                 |
