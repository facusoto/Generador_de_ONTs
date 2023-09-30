import time
import random

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager


class Init8115:
    def __init__(self, numeroMod, contrasenaMod, wanMod, wifiMod, wifiMod5g):

        # Configuraciónes previas al instanciado
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--output=/dev/null")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--silent")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

        # Crea una instancia del controlador de Chrome con las opciones configuradas
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

        # Configura el tiempo de espera
        self.wait = WebDriverWait(self.driver, 30)

        # Configuración de datos obtenidos desde Sheets
        self.numeroMod = numeroMod
        self.contrasenaMod = contrasenaMod
        self.wanMod = wanMod
        self.wifiMod = wifiMod
        self.wifiMod5g = wifiMod5g

        # Configuración de datos obtenidos
        self.gpon = None
        self.mac = None
        self.potencia = None
        self.output_pass = None
        self.numero_aleatorio = random.randint(10000000, 99999999)

    def obtener_datos(self):
        driver = self.driver
        # Ingreso, verificación de potencia y subida de datos de modem
        try:
            # print('\t>Version de pruebas, no olvides deshacer los cambios y borrar este mensaje! (POTENCIA)')
            driver.get('http://192.168.1.1/te_info.asp')
            driver.delete_all_cookies()
            print("Ingresando a 192.168.1.1")

        except WebDriverException as e:
            # Verifica si el mensaje de error contiene "ERR_CONNECTION_TIMED_OUT"
            if "net::ERR_CONNECTION_TIMED_OUT" in str(e):
                print(f"Se produjo un error de tiempo de espera de conexión, verificá la conexión al modem")
                raise SystemExit

        try:
            # Obtén los elementos
            gpon_element = driver.find_element_by_xpath('//*[@id="tdId"]').text
            mac_element = driver.find_element_by_xpath('//*[@id="tdMac"]').text

            # Formatea las cadenas de texto de manera más clara
            self.gpon = [[f"{gpon_element.upper().replace('-', '')}"]]
            self.mac = [[f"{mac_element.upper().replace(':', '')}"]]

            # Setear valores para ciclo que obtenga un valor correcto de potencia
            sin_potencia = "--- dBm"
            max_intentos = 5
            intentos = 0

            # Evita los errores de lectura de potencia probando varias veces
            while intentos < max_intentos:
                # Obtener valor de potencia
                potencia_element = driver.find_element_by_xpath('//*[@id="tdRx"]').text

                # Obtiene el valor de potencia
                if potencia_element != sin_potencia:
                    self.potencia = int(''.join(filter(str.isdigit, potencia_element))[:3])
                    break
                else:
                    intentos += 1
                    driver.refresh()

            # Si no se obtuvo la potencia (y, por lo tanto, continúa en None) la establece en 0
            if self.potencia is None:
                self.potencia = 0

            # Verifica si no hay potencia y hace un break
            for cuenta in range(1):
                if self.potencia == 0:
                    print("¡Modem sin potencia, límpialo o revisa la conexión!")
                    break
                else:
                    # Evalúa y muestra el estado de la potencia
                    if self.potencia >= 245:
                        potencia_msg = "Mala potencia"
                    elif 220 <= self.potencia < 245:
                        potencia_msg = "Buena potencia"
                    elif 0 < self.potencia < 220:
                        potencia_msg = "Excelente potencia"
                    else:
                        potencia_msg = "Potencia desconocida"

                    # Imprime el mensaje de potencia
                    print(f"Potencia: {self.potencia} - {potencia_msg}")
                    # Se imprime que se obtuvieron los datos solo si pasa la prueba de la potencia
                    print("¡Datos de modem obtenidos!")

            return self.gpon, self.mac, self.potencia

        except TimeoutException:
            print("No se pudo acceder y obtener los datos")

    def ont_progress(self):

        # Ingreso a la página 192.168.1.1:8000
        driver = self.driver
        driver.get('http://192.168.1.1:8000/')

        # Ventana de ingreso
        user = driver.find_element_by_name("Username")
        user.send_keys("admin")

        password = driver.find_element_by_name("Password")
        password.send_keys(self.contrasenaMod)

        entrar = driver.find_element_by_xpath("//input[@value='Entrar']")
        entrar.click()

        print("Ingresando al modem")

    def cambio_contrasena(self):
        driver = self.driver
        tecnico = 'Tecnico2018'
        driver.get('http://192.168.1.1:8000/user_profile.asp')

        if self.contrasenaMod != tecnico:
            self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="pwdOld"]')))
            driver.find_element_by_id("pwdOld").send_keys(self.contrasenaMod)
            driver.find_element_by_id("pwdNew").send_keys(tecnico)
            driver.find_element_by_id("pwdConfirm").send_keys(tecnico)

            driver.find_element_by_id("btnSaveApply").click()

            # Encontrar y aceptar las alertas
            try:
                self.wait.until(EC.alert_is_present())
                alerts = driver.switch_to.alert
                alerts.accept()
            except TimeoutException:
                print("Sin alertas, ¿Error?")

            print("Contraseña cambiada con éxito")
        else:
            print("La contraseña actual es igual a la contraseña de técnico, no se realiza ningún cambio.")

    def cambio_wan(self):
        driver = self.driver
        driver.get('http://192.168.1.1:8000/wanintf.asp')

        # Obtiene la cantidad total de IP services
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//tr/td[1]/input')))
        elementos = driver.find_elements_by_xpath('//tr/td[1]/input')
        cantidad_total = len(elementos)

        # Verificar si hay más de un elemento
        if cantidad_total == 0:
            print('No existen WAN para configurar, error')
        elif cantidad_total > 1:
            # Hacer clic en los elementos restantes (si los hay)
            for elemento in elementos[1:]:
                elemento.click()

            # Elimina las IP services, excepto el primero
            driver.find_element_by_id("DelWanIPIntf").click()

            # Una vez hecho continua con la primera
            wan_interface = driver.find_element_by_xpath('//tr[1]/td[2]/a')
            wan_interface.click()

            # Configuración de la WAN Service
            vlan_id = driver.find_element_by_name("vlanid")
            vlan_id.clear()
            vlan_id.send_keys("10")

            wan_user = driver.find_element_by_name("username")
            wan_user.clear()
            wan_user.send_keys(self.wanMod)

            wan_password = driver.find_element_by_name("password")
            wan_password.clear()
            wan_password.send_keys("123456")

            dns_override = driver.find_element_by_name("dns_override")
            dns_override.click()

            # Definir un diccionario con nombres y valores
            elementos_dict = {
                "dnsv4_svr0-0": "8",
                "dnsv4_svr0-1": "8",
                "dnsv4_svr0-2": "8",
                "dnsv4_svr0-3": "8",
                "dnsv4_svr1-0": "1",
                "dnsv4_svr1-1": "1",
                "dnsv4_svr1-2": "1",
                "dnsv4_svr1-3": "1"
            }

            # Iterar a través del diccionario y establecer los valores en los elementos input
            for nombre, valor in elementos_dict.items():
                elemento = driver.find_element_by_name(nombre)
                elemento.clear()
                elemento.send_keys(valor)

            ipv6 = driver.find_element_by_xpath('//input[@name="ipv6_type" and @value="2"]')
            ipv6.click()

            driver.find_element_by_xpath("//input[@value='Apply']").click()
        print("Cambio de WAN")

    def cambios_varios(self):
        driver = self.driver

        # ---------------------
        # Configuración de IPv6
        driver.get('http://192.168.1.1:8000/ipv6.asp')

        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@type="radio" and @value="0"]')))
        elementos = driver.find_elements_by_xpath('//input[@type="radio" and @value="0"]')
        cantidad_total = len(elementos)

        # Verificar si hay más de un elemento
        if cantidad_total == 0:
            print('No botones para clickear, error')
        elif cantidad_total > 1:
            # Hacer clic en los elementos restantes (si los hay)
            for elemento in elementos:
                elemento.click()

        # Aplicar cambios
        driver.find_element_by_xpath('//*[@id="btnIPv6"]').click()

        # --------------------
        # Configuración de RIP
        driver.get('http://192.168.1.1:8000/rip.asp')

        try:
            checkbox = driver.find_element_by_xpath('//td[2]//input[@type="checkbox" and not(@checked)]')
            checkbox.click()
        except NoSuchElementException:
            pass

        # Aplicar cambios
        driver.find_element_by_xpath('//*[@id="SaveRip"]').click()

        # --------------------------
        # Configuración de DNS Relay
        valores = [8, 1]

        for i in valores:
            # Ingreso de la URL mudada
            driver.get('http://192.168.1.1:8000/dnsrelay.asp#1')

            # Agregar configuración, espera cautelosa
            self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="AddStaticDnsRelay"]')))
            driver.find_element_by_xpath('//*[@id="AddStaticDnsRelay"]').click()
            driver.find_element_by_xpath('//input[@name="adm_state" and @value="1"]').click()

            # Encontrar los inputs y rellenarlos
            elementos = driver.find_elements_by_xpath('//input[@type="text"]')
            cantidad_total = len(elementos)

            # Verificar si hay más de un elemento
            if cantidad_total == 0:
                print('No botones inputs para rellenar, error')
            elif cantidad_total > 1:
                # Hacer clic en los elementos restantes (si los hay)
                for elemento in elementos:
                    elemento.clear()
                    elemento.send_keys(i)

            # Guardar configuración
            driver.find_element_by_xpath('//*[@id="StaticDnsRelayForm"]/div[4]/input[2]').click()

        # ------------------------------
        # Configuración UPN y WAN Mirror
        urls = ['http://192.168.1.1:8000/upnp.asp', 'http://192.168.1.1:8000/diagsw.asp']

        for url in urls:
            # Navegar a la página web deseada
            driver.get(url)

            self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@type="radio" and @value="1"]')))
            radio = driver.find_element_by_xpath('//*[@type="radio" and @value="1"]')
            radio.click()
            apply = driver.find_element_by_xpath('//*[@value="Apply"]')
            apply.click()
            time.sleep(2)

        # ---------------------
        # Configuración de DHCP
        driver.get('http://192.168.1.1:8000/dhcp.asp')

        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//tr[1]/td[2]/a')))
        dhcp = driver.find_element_by_xpath('//tr[1]/td[2]/a')
        dhcp.click()

        # Espera cautelosa
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//fieldset[1]/div[4]')))

        # Definir un diccionario con nombres y valores
        elementos_dict = {
            "ipv4_dns_addr_0-0": "8",
            "ipv4_dns_addr_0-1": "8",
            "ipv4_dns_addr_0-2": "8",
            "ipv4_dns_addr_0-3": "8",
            "ipv4_dns_addr_1-0": "1",
            "ipv4_dns_addr_1-1": "1",
            "ipv4_dns_addr_1-2": "1",
            "ipv4_dns_addr_1-3": "1"
        }

        # Iterar a través del diccionario y establecer los valores en los elementos input
        for nombre, valor in elementos_dict.items():
            elemento = driver.find_element_by_name(nombre)
            elemento.clear()
            elemento.send_keys(valor)

        # Aplicar cambios
        driver.find_element_by_xpath('//*[@id="DHCPServerSettingForm"]/div[5]/input[2]').click()
        print("Cambios varios")

    def cambio_2g(self):
        driver = self.driver
        driver.get('http://192.168.1.1:8000/wifi.asp')

        # Seleccionar Bandwith (Espera cautelosa)
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="adm_bandwidth"]')))
        elemento_select = Select(driver.find_element_by_name("adm_bandwidth"))
        elemento_select.select_by_value('2')

        # Seleccionar Channel
        elemento_select = Select(driver.find_element_by_name("adm_channel"))
        elemento_select.select_by_value('1')

        # Aplicar cambios
        apply = driver.find_element_by_xpath('//*[@id="WiFiPhysicalSettingForm"]//input[@value="Apply"]')
        apply.click()

        # Ir al menú de configuración wifi
        ap_sett = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//li[2]/a')))
        ap_sett.click()

        # Ir al primer elemento y cambiar su configuración
        wifi_conf = driver.find_element_by_xpath('//*[@id="Tab2_1"]//tr[1]/td[1]/a')
        wifi_conf.click()

        wifi_name2g = driver.find_element_by_id("ssid")
        wifi_name2g.clear()
        wifi_name2g.send_keys(self.wifiMod)

        wifi_pass = driver.find_element_by_xpath('//input[@name="key_phrase"]')
        wifi_pass_text = wifi_pass.get_attribute('value')
        self.output_pass = [[wifi_pass_text]]

        wifi_pass.clear()
        wifi_pass.send_keys(self.numero_aleatorio)

        if wifi_pass_text:
            print("¡Contraseña wifi obtenida!")
        else:
            print("Contraseña no obtenida")

        driver.find_element_by_xpath('//*[@id="WiFiAPSettingForm"]//input[@value="Apply"]').click()

        print("Wifi 2g configurado")
        return self.output_pass, [[self.numero_aleatorio]]

    def cambio_5g(self):
        driver = self.driver
        driver.get('http://192.168.1.1:8000/wifi5g.asp')

        # Seleccionar Channel (Espera cautelosa)
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="adm_channel"]')))
        elemento_select = Select(driver.find_element_by_name("adm_channel"))
        elemento_select.select_by_value('60')

        # Aplicar cambios
        apply = driver.find_element_by_xpath('//*[@id="WiFiPhysicalSettingForm"]//input[@value="Apply"]')
        apply.click()

        # Ir al menú de configuración wifi
        ap_sett5g = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//li[2]/a')))
        ap_sett5g.click()

        # Ir al primer elemento y cambiar su configuración
        wifi_conf5g = driver.find_element_by_xpath('//*[@id="Tab2_1"]//tr[1]/td[1]/a')
        wifi_conf5g.click()

        wifi_name5g = driver.find_element_by_id("ssid")
        wifi_name5g.clear()
        wifi_name5g.send_keys(self.wifiMod5g)

        # Seleccionar tipo de autorización
        auth_selector = driver.find_element_by_xpath('//select[@id="authentication"]/option[@value="3"]')
        auth_selector.click()

        # Setear contraseña
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@name="key_phrase"]')))
        wifi_pass = driver.find_element_by_xpath('//input[@name="key_phrase"]')
        wifi_pass.clear()
        wifi_pass.send_keys(self.numero_aleatorio)

        driver.find_element_by_xpath("//*[@id='WiFiAPSettingForm']//input[@value='Apply']").click()

        print("Wifi 5g configurado")

    def kill(self):
        driver = self.driver
        driver.close()
