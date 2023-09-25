import csv
import re
import psutil
import subprocess

from google.oauth2 import service_account
from googleapiclient.discovery import build
from ont_generation.mitra_2541 import Init2541
from ont_generation.mitra_2741 import Init2741
from ont_generation.askey_3505 import Init3505
from ont_generation.askey_8115 import Init8115
from ont_generation.zte import InitZTE

# Variables para Google Sheets!
SAMPLE_SPREADSHEET_ID = None
SERVICE_ACCOUNT_FILE = 'keys.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()


# Obtener las contraseñas desde google sheets
def sheets_ont_passes(sheet_id, start, end):
    try:
        result = sheet.values().get(spreadsheetId=sheet_id, range=f'Modems!E{start}:E{end}').execute()
        return result['values']
    except Exception as e:
        print('Error, no se pudo conectar al servidor de Google Sheets. Revisa tu conexión y vuelve a intentarlo')
        raise SystemExit


# Google sheets, grabación de datos
def update_data(sheet_id, number, output_data):
    sheet.values().update(spreadsheetId=sheet_id,
                          range=f'Modems!D{number+1}', valueInputOption="USER_ENTERED",
                          body={"values": output_data}).execute()


# Google sheets, grabación de contraseña
def update_pass(sheet_id, number, column, output_pass):
    sheet.values().update(spreadsheetId=sheet_id,
                          range=f'Modems!{column}{number+1}', valueInputOption="USER_ENTERED",
                          body={"values": output_pass}).execute()


# Lectura y verificación de los registros
def lectura_registros():
    # Creando listas para las columnas
    registros = []
    ids_sheet = []
    errores = []

    # Expresiones regulares para validar las columnas
    regex_col1 = r'^[a-zA-Z0-9]{1,5}$'
    regex_col2 = r'^.{44}$'

    # Lectura del archivo de registros
    with open('registros.csv', 'r') as archivo_registros:
        archivo_registros = csv.DictReader(archivo_registros)

        # Encuentra las líneas con errores y los informa
        for i, col in enumerate(archivo_registros, start=2):
            registro_control = col['registro']
            id_sheet_control = col['id']

            if not re.match(regex_col1, registro_control):
                errores.append(f"\nIrregularidad en fila {i} del archivo de registros: " +
                               "Formato no válido en la columna 'registro'\n" +
                               "Soluciona el problema para continuar\n")
            else:
                registros.append(registro_control)

            if not re.match(regex_col2, id_sheet_control):
                errores.append(f"\nIrregularidad en fila {i} del archivo de registros: " +
                               "Formato no válido en la columna 'id'\n" +
                               "Soluciona el problema para continuar\n")
            else:
                ids_sheet.append(id_sheet_control)

    if len(registros) == 0:
        print('No existen registros para trabajar, agrega uno para continuar')
        editar_registros()
    else:
        # Valores a devolver
        resultado = {
            'registros': registros,
            'ids_sheet': ids_sheet,
            'errores': errores
        }
        return resultado


# Agregar nuevos registros al archivo
def editar_registros():
    while True:
        # Consulta el nombre del registro
        nombre_registro = input(
            "Ingresa el nombre del registro (máximo 5 letras o números), o escribe 'cancelar' para salir: ")

        if nombre_registro.lower() == "cancelar":
            print("Proceso de edición de registros cancelado.")
            break

        # Validación del nombre del registro
        if re.match(r'^[a-zA-Z0-9]{1,5}$', nombre_registro):
            break
        else:
            print("Nombre de registro no válido. Inténtalo nuevamente.")

    while True:
        # Consulta el ID del registro
        id_registro = input("Ingresa el ID del registro (44 caracteres), o escribe 'cancelar' para salir: ")

        if id_registro.lower() == "cancelar":
            print("Proceso de edición de registros cancelado.")
            break

        # Validación del ID del registro
        if re.match(r'^.{44}$', id_registro):
            break
        else:
            print("ID de registro no válido. Inténtalo nuevamente.")

    # Agrega los valores al archivo de registros utilizando la biblioteca csv
    with open('registros.csv', 'a', newline='') as archivo:
        writer = csv.writer(archivo)
        writer.writerow([nombre_registro, id_registro])

    print(f"Registro '{nombre_registro}' agregado correctamente.")
    raise SystemExit


# Ejecutar las clases para configurar los modems
def ont_config(sheet_id, modem_number, ontpass, registro, model):
    wifi2g = "FibrAzul_" + registro.upper() + str(modem_number)
    wifi5g = "FibrAzul5Ghz_" + registro.upper() + str(modem_number)

    # Crear un diccionario para mapear modelos a sus detalles
    modelo_detalles = {
        1: {"Modelo": "Askey 8115", "Wan service": f"askey{registro}{modem_number}", "Clase": Init8115},
        2: {"Modelo": "Askey 3505", "Wan service": f"askey{registro}{modem_number}", "Clase": Init3505},
        3: {"Modelo": "Mitra 2541", "Wan service": f"mitra{registro}{modem_number}", "Clase": Init2541},
        4: {"Modelo": "Mitra 2741", "Wan service": f"mitra{registro}{modem_number}", "Clase": Init2741},
        5: {"Modelo": "ZTE", "Wan service": f"zte{registro}{modem_number}", "Clase": InitZTE}
    }

    # Imprimir datos del módem basado en el modelo
    print("Número:", modem_number)
    print("Contraseña:", ontpass)
    print("Wifi 2g:", wifi2g)
    print("Wifi 5g:", wifi5g)

    # Realizar el trabajo de acuerdo al modelo
    if model in modelo_detalles:

        # Imprimir valores relacionados con el modelo
        detalles = modelo_detalles[model]
        print("Modelo:", detalles["Modelo"])
        print("Wan service:", detalles["Wan service"])

        # Crea una instancia de la clase correspondiente, ejecuta la configuración y obtiene los datos
        configurador = detalles["Clase"](modem_number, ontpass, detalles["Wan service"], wifi2g, wifi5g)

        # Si el modelo es un ZTE usa otros métodos
        if model == 5:
            try:
                configurador.ont_progress()
                configurador.upload_configuration()
                configurador.localnet_config()
                configurador.internet_config()
                configurador.cambio_contrasena()

                # Finalizar el proceso de Selenium tras finalizar
                configurador.kill()

            except Exception as e:
                print(f'Ocurrió un error: {e}')

        else:
            # Método para obtener los datos del modelo
            resultado = configurador.obtener_datos()

            # Verifica que el reultado no sea None, causas probables: Contraseña erronea.
            if resultado is not None:
                # Separa los datos obtenidos en distintas variables
                output_data = resultado[0]
                potencia = resultado[1]

                # Ejecuta el programa si la potencia está dentro de un intervalo aceptable
                if 0 < potencia < 245:
                    # Almacenar datos en google sheets
                    update_data(sheet_id, modem_number, output_data)

                    # Continuar con la ejecución
                    configurador.ont_progress()
                    configurador.cambio_wan()
                    configurador.cambios_varios()

                    # Obtener contraseña wifi de fábrica y la generada aleatoreamente
                    column_values = ['L', 'M']
                    output_pass = configurador.cambio_2g()

                    # Iterar a través de column_values y usar output_pass[0] para 'L' y output_pass[1] para 'M'
                    # Es decir, graba las contraseñas en distintas columnas
                    for column in column_values:
                        update_pass(sheet_id, modem_number, column, output_pass[column_values.index(column)])

                    configurador.cambio_5g()

                    # Repite el cambio del 5g si es un 3505
                    if model == 2:
                        configurador.cambio_5g()

                    configurador.cambio_contrasena()

                    # Finalizar el proceso de Selenium tras finalizar
                    configurador.kill()
            else:
                print("Proceso interrumpido: Potencia del modem demasiado alta.")
    else:
        print("Modelo no válido, ¿Cómo llegaste hasta acá?")

    # Final del proceso y alerta sonora
    print("------\007")


# Realizar preguntas y setear intervalos
def configurar_marco_trabajo(reg_dict):
    # Setear archivos para el usuario
    archivo_ayuda = "ayuda.html"

    # Mensajes de bienvenida
    print('\n.:: Bienvenido al Generador de ONTs ::.')
    print("Escribe 'administrar' para abrir el registro, 'ayuda' para ver el manual de Usuario o simplemente continúa el proceso\n")

    while True:
        # Configurar cantidad de dispositivos
        entrada = input("¿Cuántas veces deseas repetirlo?: ")

        # Proceso para ingresar a los registros
        if entrada.lower() == "administrar":
            editar_registros()

        # Proceso para recibir ayuda
        elif entrada.lower() == "ayuda":
            try:
                subprocess.Popen(["start", archivo_ayuda], shell=True)
            except FileNotFoundError:
                print("No se pudo encontrar un visor de PDF adecuado en tu sistema.")
            except Exception as e:
                print(f"Se produjo un error: {e}")

        # Proceso convencional
        else:
            try:
                cantidad = int(entrada)
                if cantidad == 0:
                    print("Por favor, ingresa un número válido para la cantidad de repeticiones.")
                elif cantidad > 0:
                    break  # Sale del bucle si se ingresó un número válido positivo
                else:
                    print("La cantidad debe ser un número positivo.")
            except ValueError:
                print("Por favor, ingresa un número válido para la cantidad de repeticiones.")

    # Declarar los modelos a configurar
    model_list = []
    for i in range(cantidad):
        while True:
            try:
                modelo = int(input(f"{i + 1}) // 8115 = 1 // 3505 = 2 // 2541 = 3 // 2741 = 4 // ZTE = 5 : "))
                if modelo in [1, 2, 3, 4, 5]:
                    model_list.append(modelo)
                    break  # Sale del bucle si se ingresó un número válido
                else:
                    print("Por favor, ingresa un número válido entre 1 y 5.")
            except ValueError:
                print("Por favor, ingresa un número válido para el modelo.")

    # Declarar el registro a utilizar
    while True:
        # Verificar si el registro existe
        registro = input(f"¿Qué registro usar? {'/'.join(reg_dict.keys())}: ").lower()

        if registro in reg_dict:
            # El usuario ingresó una llave válida
            sheet_id = reg_dict[registro]
            print(f"Se va a trabajar con el registro: {registro}")
            break
        else:
            # El usuario ingresó una llave no válida
            print(f"El registro {registro} no es válido. Por favor, ingresa uno válido.")

    # Obtención de número inicial y determinación del rango en google sheets
    while True:
        try:
            first_modem = int(input("¿Cuál es el número del modem inicial?: "))
            if first_modem <= 0:
                print("Por favor, ingresa un número positivo para el número inicial del modem.")
            else:
                break  # Sale del bucle si se ingresó un número válido positivo
        except ValueError:
            print("Por favor, ingresa un número válido para el número inicial del modem.")

    # La busqueda tarda, mensaje explicativo y separador
    print(f"Buscando las contraseñas en el registro: {registro}")
    print("------")

    start = (first_modem + 1)
    end = (first_modem + cantidad)

    # Obtención de contraseñas desde sheets
    ont_passes = sheets_ont_passes(sheet_id, start, end)

    # Comprobar que la request contiene contraseñas
    if not ont_passes:
        print('El intervalo seleccionado está vacío, por favor ingresa las contraseñas en el registro')
        raise SystemExit  # Termina la ejecución del programa en caso de error

    else:
        # Mensaje de inicio del proceso
        print("Iniciando proceso de configuración de modems...\n------")

        for i in range(0, cantidad):
            try:
                # Seteando los valores que se van a enviar a la función
                ontpass = ont_passes[i][0]
                modem_number = first_modem + i

                # Función configuradora de modems
                ont_config(sheet_id, modem_number, ontpass, registro, model_list[i])

                # Mensaje para cuando se finaliza el proceso en cada modem.
                input('Proceso completado. Cambia el cable del modem y presiona "Enter".\n------')

            except IndexError:
                print('El intervalo está vacío. Ingresa la contraseña del modem en el registro.')
                raise SystemExit
        else:
            # Mensaje de final de proceso
            print("¡Proceso de configuración concluido!")


# Ejecución final
def ejecutar_programa():
    # Busca todos los procesos en ejecución llamados "chromedriver.exe"
    for process in psutil.process_iter(attrs=['name']):
        if process.name() == 'chromedriver.exe':
            try:
                # Intenta terminar el proceso
                process.terminate()
            except Exception as e:
                print(f"No se pudo terminar el proceso: {str(e)}")

    # Llama a la función de lectura y verificación
    resultado = lectura_registros()

    # Si encuentra errores los imprime, si no los encuentra ejecuta el programa
    if resultado['errores']:
        for error in resultado['errores']:
            print(error)
    else:
        # Creando un diccionario de los registros
        reg_dict = {clave: valor for clave, valor in zip(resultado['registros'], resultado['ids_sheet'])}

        # Función que hará el trabajo
        configurar_marco_trabajo(reg_dict)


if __name__ == "__main__":
    # Llama a la función para ejecutar el programa
    ejecutar_programa()
