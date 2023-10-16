import time
import random
import requests

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, NoAlertPresentException
from selenium.common.exceptions import UnexpectedAlertPresentException, WebDriverException
from webdriver_manager.firefox import GeckoDriverManager


class Init3505:
    def __init__(self, numeroMod, contrasenaMod, wanMod, wifiMod, wifiMod5g, previous_pass):

        # Configuraciónes previas al instanciado
        firefox_options = Options()
        # firefox_options.add_argument("--headless")
        firefox_options.add_argument("--start-maximized")
        firefox_options.add_argument("--log-level=3")
        firefox_options.add_argument("--silent")

        # Crea una instancia del controlador de Chrome con las opciones configuradas
        self.driver = webdriver.Firefox(executable_path=GeckoDriverManager().install(), options=firefox_options)
        # Configura el tiempo de espera
        self.wait = WebDriverWait(self.driver, 30)

        # Configuración de datos obtenidos desde Sheets
        self.numeroMod = numeroMod
        self.contrasenaMod = contrasenaMod
        self.wanMod = wanMod
        self.wifiMod = wifiMod
        self.wifiMod5g = wifiMod5g
        self.previous_pass = previous_pass

        # Configuración de datos obtenidos
        self.gpon = None
        self.mac = None
        self.potencia = None
        self.output_pass = None
        self.numero_aleatorio = previous_pass if self.previous_pass is not None else random.randint(10000000, 99999999)

    def obtener_datos(self):
        driver = self.driver
        # Ingreso, verificación de potencia y subida de datos de modem
        try:
            driver.delete_all_cookies()
            driver.get('http://192.168.1.1/')
            print("Ingresando a 192.168.1.1")

        except WebDriverException as e:
            # Verifica si el mensaje de error contiene "ERR_CONNECTION_TIMED_OUT"
            if "net::ERR_CONNECTION_TIMED_OUT" in str(e):
                print(f"Se produjo un error de tiempo de espera de conexión, verificá la conexión al modem")
                driver.quit()
                print("------\007")
                raise SystemExit

        # Frame de ingreso
        new_frame = driver.find_element_by_xpath("/html/frameset/frame[1]")
        driver.switch_to.frame(new_frame)

        input_pass = driver.find_element_by_name('Password')
        input_pass.send_keys(self.contrasenaMod)

        # Buscar y cliquear botón de ingreso (cambiante)
        try:
            entrar = driver.find_element_by_class_name('te_acceso_router_enter')
            entrar.click()

        except NoSuchElementException:
            entrar = driver.find_element_by_xpath("//input[@value='Entrar']")
            entrar.click()

        # Esperar un segundo e ir a la pestaña de información
        time.sleep(2)

        # Verificar si se puede cambiar de página, si no se puede la contraseña es incorrecta
        try:
            driver.get('http://192.168.1.1/te_info.html')

        except UnexpectedAlertPresentException:
            print('La contraseña introducida es incorrecta, por favor verificala')
            driver.quit()
            print("------\007")
            raise SystemExit

        # --------------------
        # Variables a utilizar
        gpon_element = ''
        mac_element = ''
        potencia_element = ''
        sin_potencia = "--- dBm"

        # Toma de valores en dos modelos
        try:
            gpon_element = driver.find_element_by_xpath('//*[@id="tdId"]').text
            mac_element = driver.find_element_by_xpath('//*[@id="tdMac"]').text
            potencia_element = driver.find_element_by_xpath('//*[@id="tdRx"]').text

        except NoSuchElementException:
            gpon_element = driver.find_element_by_xpath('//*[@id="tdId"]').text
            mac_element = driver.find_element_by_xpath('//*[@id="PCformat"]/div[3]/table/tbody/tr[9]').text
            potencia_element = driver.find_element_by_xpath('/html/body/div/div[1]/div[7]/div[2]/div[3]/span[1]').text

        except TimeoutException:
            print("No se pudo acceder y obtener los datos")

        # Formatea las cadenas de texto de manera más clara
        self.gpon = f"{gpon_element.upper().replace('-', '')}"

        if "46414D41" in self.gpon:
            self.gpon = [[f"{self.gpon.replace('46414D41', 'FAMA')}"]]
        elif "41534B59" in self.gpon:
            self.gpon = [[f"{self.gpon.replace('41534B59', 'ASKY')}"]]
        else:
            print('Error')

        self.mac = [[f"{mac_element.upper().replace(':', '')}"]]

        # Formatea la potencia
        if potencia_element != sin_potencia:
            self.potencia = int(''.join(filter(str.isdigit, potencia_element))[:3])
        else:
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

    def ont_progress(self):
        driver = self.driver
        driver.get('http://192.168.1.1:8000/')

        # Ventana de ingreso
        try:
            new_frame = driver.find_element_by_xpath('/html/frameset/frame[1]')
            driver.switch_to.frame(new_frame)

            # Acceder datos
            user = driver.find_element_by_name("Username")
            user.send_keys("admin")

            password = driver.find_element_by_name("Password")
            password.send_keys(self.contrasenaMod)

            entrar = driver.find_element_by_xpath("//input[@value='Entrar']")
            entrar.click()

            driver.switch_to.default_content()

        except NoSuchElementException:
            print("No fue necesario acceder de nuevo")

        time.sleep(3)

    def cambio_contrasena(self):
        driver = self.driver
        driver.get('http://192.168.1.1:8000/password.html')
        tecnico = "Tecnico2018"

        # Frame Menu (Management)
        if self.contrasenaMod != tecnico:
            # Ingresar la contraseña actual y la nueva contraseña
            driver.find_element_by_name("pwdOld").send_keys(self.contrasenaMod)
            driver.find_element_by_name("pwdNew").send_keys(tecnico)
            driver.find_element_by_name("pwdCfm").send_keys(tecnico)

            # Hacer clic en el botón de aplicar cambios
            driver.find_element_by_xpath("//input[@value='Apply/Save']").click()

            print("Contraseña cambiada con éxito")
        else:
            print("La contraseña actual es igual a la contraseña de técnico, no se realiza ningún cambio.")

    def cambio_wan(self):
        driver = self.driver
        driver.get('http://192.168.1.1:8000/wancfg.cmd')

        # Eliminar configuración previa
        try:
            rml_inputs = driver.find_elements_by_xpath("//input[@name='rml']")

            # Encontrar los elementos y eliminarlos
            for rml_input in rml_inputs:
                if rml_input.is_displayed():
                    rml_input.click()
            driver.find_element_by_xpath("//input[@value='Remove']").click()

        except NoSuchElementException:
            print("No se encontraron Input RML, algo inusual ocurrió.")

        # Agregar nueva configuración (Espera cautelosa)
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Add']")))
        driver.find_element_by_xpath("//input[@value='Add']").click()

        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='Next']")))
        driver.find_element_by_xpath("//input[@value='Next']").click()

        # Configuración VLAN
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='vlanMuxPr']")))
        vlan_min = driver.find_element_by_name("vlanMuxPr")
        vlan_min.clear()
        vlan_min.send_keys("0")

        vlan_max = driver.find_element_by_name("vlanMuxId")
        vlan_max.clear()
        vlan_max.send_keys("10")

        driver.find_element_by_xpath("//select[@name='vlanTpid']/option[text()='0x8100']").click()
        driver.find_element_by_xpath("//input[@value='Next']").click()

        # Configuración PPP
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='pppUserName']")))
        ppp_user_name = driver.find_element_by_name("pppUserName")
        ppp_user_name.clear()
        ppp_user_name.send_keys(self.wanMod)

        ppp_password = driver.find_element_by_name("pppPassword")
        ppp_password.clear()
        ppp_password.send_keys("123456")

        driver.find_element_by_xpath("//input[@value='Next']").click()
        driver.find_element_by_name("chkIpv4DefaultGtwy").click()

        driver.find_element_by_xpath("//input[@value='Next']").click()
        driver.find_element_by_xpath("//input[@value='Next']").click()

        # Finalizar configuración
        driver.find_element_by_xpath("//input[@value='Apply/Save']").click()

        print("Cambio de WAN")

    def cambios_varios(self):
        driver = self.driver

        # ---------------------
        # Configuración de IPv6
        driver.get('http://192.168.1.1:8000/ipv6lancfg.html')

        # Buscar elementos input de tipo checkbox excluyendo 'enableRadvdUla'
        checkboxes = driver.find_elements_by_xpath('//input[@type="checkbox" and not(@name="enableRadvdUla")]')

        # Verificar si se encontraron elementos
        if not checkboxes:
            print('No se encontraron botones para clickear, error')
        else:
            # Cliquear en los elementos que estén seleccionados
            for checkbox in checkboxes:
                if checkbox.is_selected():
                    checkbox.click()

        driver.find_element_by_xpath("//input[@value='Save/Apply']").click()

        # ---------------------
        # Configuración de DHCP
        driver.get('http://192.168.1.1:8000/adminlancfg.html')

        # Habilitar radio DHCP
        dhcp_enable = driver.find_element_by_xpath('//*[@id="dhcpInfo"]/table[1]/tbody/tr[2]/td/input')
        dhcp_enable.click()

        # Setear servidores DNS
        dns_server_1 = driver.find_element_by_name("lanHostDns1")
        dns_server_1.clear()
        dns_server_1.send_keys("8.8.8.8")

        dns_server_2 = driver.find_element_by_name("lanHostDns2")
        dns_server_2.clear()
        dns_server_2.send_keys("1.1.1.1")

        driver.find_element_by_xpath('//input[@value="Apply/Save"]').click()

        # --------------------------
        # Configuración de IP Filter
        driver.get('http://192.168.1.1:8000/scbidirectionalflt.cmd?action=view')

        # Selecciona el primer elemento y edita
        driver.find_element_by_xpath("//tr[2]/td[6]/input").click()
        driver.find_element_by_xpath("//input[@value='Edit']").click()

        # Selecciona default action
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='entryDefaultAction']")))
        default_action = Select(driver.find_element_by_name("entryDefaultAction"))
        default_action.select_by_value('Permit')

        driver.find_element_by_xpath('//input[@name="applyEntry"]').click()

        # --------------------
        # Configuración de DNS
        driver.get('http://192.168.1.1:8000/dnscfg.html')

        # Habilitar radio DNS
        dns_enable = driver.find_element_by_xpath("//table[3]/tbody/tr[1]/td/input")
        dns_enable.click()

        # Setear servidores DNS
        dns_server_1 = driver.find_element_by_name("dnsPrimary")
        dns_server_1.clear()
        dns_server_1.send_keys("8.8.8.8")

        dns_server_2 = driver.find_element_by_name("dnsSecondary")
        dns_server_2.clear()
        dns_server_2.send_keys("1.1.1.1")

        print("Cambios varios")

    def cambio_2g(self):
        driver = self.driver

        # ------------------------
        # Ir a la página principal
        driver.get('http://192.168.1.1:8000/te_wifi.html')

        # Cambiar nombre SSID
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='SSIDName']")))
        ssid2g = driver.find_element_by_name("SSIDName")
        ssid2g.clear()
        ssid2g.send_keys(self.wifiMod)

        # Selecciona la autenticación
        default_action = Select(driver.find_element_by_name("AuthType"))
        default_action.select_by_value('wpa2_a')

        # Selecciona el canal WIFI
        default_action = Select(driver.find_element_by_name("wlChannel"))
        default_action.select_by_value('1')

        # Desocultar red y contraseña
        driver.find_element_by_xpath('//*[@name="hideSSID" and @value="0"]').click()
        driver.find_element_by_xpath('//*[@class="hand"]').click()
        time.sleep(2)

        # Obteniendo la contraseña de fábrica
        password_input = driver.find_element_by_id('SSIDPassword')
        wifi_pass_text = password_input.get_attribute('value')
        self.output_pass = [[wifi_pass_text]]

        # Guardar contraseña generada
        driver.execute_script("arguments[0].value = '';", password_input)
        password_input.send_keys(self.numero_aleatorio)

        if self.output_pass is not None:
            print("¡Contraseña wifi obtenida!")
        else:
            print("Contraseña no obtenida")

        # Guargar configuración
        driver.find_element_by_xpath("//input[@value='Aplicar cambios']").click()

        # Encontrar y aceptar las alertas
        try:
            alerts = driver.switch_to.alert
            alerts.accept()
        except TimeoutException:
            print("Sin alerta, ¿Error?")
        except NoAlertPresentException:
            print("Sin alerta, ¿Error?")

        # ---------------------------------------------------------
        # Ir a la página de avanzadas y verificar que sea accesible
        while True:
            response = requests.get('http://192.168.1.1:8000/wlcfgadv.html')

            if "try again in a few minutes" in response.text:
                time.sleep(1)
            else:
                driver.get('http://192.168.1.1:8000/wlcfgadv.html')

                # Selecciona el canal
                default_action = Select(driver.find_element_by_name("wlChannel"))
                default_action.select_by_value('1')

                # Selecciona el bandwith
                default_action = Select(driver.find_element_by_name("wlNBwCap"))
                default_action.select_by_value('1')

                # Guargar configuración
                driver.find_element_by_xpath("//input[@value='Apply/Save']").click()

                print("Wifi 2g configurado")
                return self.output_pass, [[self.numero_aleatorio]]

    def cambio_5g(self):
        driver = self.driver

        # ------------------------
        # Ir a la página principal
        while True:
            response = requests.get('http://192.168.1.1:8000/te_wifi_5ghz.html')

            if "try again in a few minutes" in response.text:
                time.sleep(1)
            else:
                driver.get('http://192.168.1.1:8000/te_wifi_5ghz.html')

                # Cambiar nombre SSID
                self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='SSIDName']")))
                ssid2g = driver.find_element_by_name("SSIDName")
                ssid2g.clear()
                ssid2g.send_keys(self.wifiMod)

                # Selecciona la autenticación
                default_action = Select(driver.find_element_by_name("AuthType"))
                default_action.select_by_value('wpa2_a')

                # Selecciona el canal WIFI
                default_action = Select(driver.find_element_by_name("wlChannel"))
                default_action.select_by_value('60')

                # Encontrar y aceptar las alertas
                try:
                    alerts = driver.switch_to.alert
                    alerts.accept()
                except TimeoutException:
                    print("Sin alerta, ¿Error?")
                except NoAlertPresentException:
                    print("Sin alerta, ¿Error?")

                # Desocultar red y contraseña
                driver.find_element_by_xpath('//*[@name="hideSSID" and @value="0"]').click()
                driver.find_element_by_xpath('//*[@class="hand"]').click()
                time.sleep(2)

                # Obteniendo la contraseña de fábrica
                password_input = driver.find_element_by_id('SSIDPassword')
                driver.execute_script("arguments[0].value = '';", password_input)
                password_input.send_keys(self.numero_aleatorio)

                # Guargar configuración
                driver.find_element_by_xpath("//input[@value='Aplicar cambios']").click()

                # Encontrar y aceptar las alertas
                try:
                    alerts = driver.switch_to.alert
                    alerts.accept()
                except TimeoutException:
                    print("Sin alerta, ¿Error?")

                print("Wifi 5g configurado")

    def kill(self):
        driver = self.driver
        driver.quit()
