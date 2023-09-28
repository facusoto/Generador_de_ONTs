import time
import random

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException, ElementClickInterceptedException, NoAlertPresentException, UnexpectedAlertPresentException
from webdriver_manager.chrome import ChromeDriverManager


class Init2741:
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
        self.base_frame = None
        self.numero_aleatorio = random.randint(10000000, 99999999)

    def obtener_datos(self):
        driver = self.driver
        # Ingreso, verificación de potencia y subida de datos de modem
        try:
            driver.get('http://192.168.1.1/cgi-bin/logIn_mhs.cgi')
            print("Ingresando a 192.168.1.1")

        except WebDriverException as e:
            # Verifica si el mensaje de error contiene "ERR_CONNECTION_TIMED_OUT"
            if "net::ERR_CONNECTION_TIMED_OUT" in str(e):
                print(f"Se produjo un error de tiempo de espera de conexión, verificá la conexión al modem")
                raise SystemExit

        # Localiza el campo de contraseña y envía la contraseña
        contrasena_input = driver.find_element_by_name('syspasswd_1')
        contrasena_input.send_keys(self.contrasenaMod)

        # Localiza el botón de entrada y haz clic en él para iniciar sesión
        entrar_btn = driver.find_element_by_id('Submit')
        entrar_btn.click()

        # Verificar si la URL ha cambiado debido a la contraseña incorrecta
        if "logIn_mhs_pw_error.cgi" in driver.current_url:
            print("Contraseña incorrecta. Corrige la contraseña en Google sheets y vuelve a intentar.")
            # Puedes lanzar una excepción aquí o realizar otra acción adecuada.
        else:
            try:
                # Obtén los elementos, espera cautelosa
                self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="gsn"]')))
                gpon_element = driver.find_element_by_xpath('//*[@id="gsn"]').text
                mac_element = driver.find_element_by_xpath('//*[@id="basemacaddress"]').text
                potencia_element = driver.find_element_by_xpath('//*[@id="opticalRX"]').text

                # Formatea las cadenas de texto de manera más clara
                self.gpon = [[f"{gpon_element.upper().replace('-', '')}"]]
                self.mac = [[f"{mac_element.upper().replace(':', '')}"]]

                # Obtiene el valor de potencia, si es 40 lo reemplaza por 0
                self.potencia = 0 if int(''.join(filter(str.isdigit, potencia_element))[:3]) == 40 else int(''.join(filter(str.isdigit, potencia_element))[:3])

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
        driver.get('http://192.168.1.1:8000/cgi-bin/logIn_main.cgi')

        # Ventana de ingreso
        user = driver.find_element_by_name("username")
        user.send_keys("admin")

        password = driver.find_element_by_name("syspasswd_1")
        password.send_keys(self.contrasenaMod)

        entrar = driver.find_element_by_xpath("//input[@value='Entrar']")
        entrar.click()

        print("Ingresando al modem")
        try:
            # Setear el valor del frame base una vez ingresado
            self.base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainFrame"]')))
        except TimeoutException:
            print('Contraseña erronea')

    def cambio_wan(self):
        driver = self.driver
        driver.switch_to.default_content()

        # Frame Menu (Wan Interface)
        wan_interface = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="network"]')))

        # Gesto hover sobre menú de WAN y clickear elemento
        hover_wan = ActionChains(driver).move_to_element(wan_interface)
        hover_wan.perform()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="network-broadband"]/a'))).click()

        # Cambiar al marco de base (Wan Interface)
        self.base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainFrame"]')))
        driver.switch_to.frame(self.base_frame)

        # Clickear wan a editar
        wan_edit_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@onclick="editXPONWan(0);"]')))
        wan_edit_button.click()

        driver.switch_to.default_content()

        # Cambiar configuración
        self.base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="RN_UserName"]')))
        wan_user = driver.find_element_by_name("RN_UserName")
        wan_user.clear()
        wan_user.send_keys(self.wanMod)

        wan_password = driver.find_element_by_name("RN_Password")
        wan_password.clear()
        wan_password.send_keys("123456")

        # Seleccionar IPv4
        ipv4_selector = driver.find_element_by_xpath("//select[@name='ipVerRadio']/option[text()='IPv4 Only']")
        ipv4_selector.click()

        # Aplicar configuración
        driver.find_element_by_xpath(f'//button[text()="Apply"]').click()

        print("Cambio de WAN")

    def cambios_varios(self):
        driver = self.driver
        driver.get('http://192.168.1.1:8000/cgi-bin/indexmain.cgi')

        # Frame Menu (Network Interface)
        network_interface = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="network"]')))

        # Gesto hover sobre menú de WAN y clicar elemento LAN
        hover_network = ActionChains(driver).move_to_element(network_interface)
        hover_network.perform()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="network-homeNetworking"]/a'))).click()

        # Cambiar al marco de base (Network Interface)
        self.base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainFrame"]')))
        driver.switch_to.frame(self.base_frame)

        # ---------
        # DNS Setup

        # Espera cautelosa
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//select[@name='MLG_DNSServer1_LANSetup']")))

        # Seleccionar y aplicar los DNS de google
        dns_sel = driver.find_element_by_xpath("//select[@name='MLG_DNSServer1_LANSetup']/option[text()='UserDefined']")
        dns_sel.click()
        dns1 = driver.find_element_by_xpath('//*[@name="PrimaryDns"]')
        dns1.clear()
        dns1.send_keys('8.8.8.8')

        dns_sel = driver.find_element_by_xpath("//select[@name='MLG_DNSServer2_LANSetup']/option[text()='UserDefined']")
        dns_sel.click()
        dns2 = driver.find_element_by_xpath('//*[@name="SecondDns"]')
        dns2.clear()
        dns2.send_keys('1.1.1.1')

        # Aplicar cambios
        driver.find_element_by_xpath('//*[@id="Apply_ID"]').click()

        try:
            alerts = driver.switch_to.alert
            alerts.accept()
        except TimeoutException:
            print("Sin alerta, ¿Error?")

        # --------------
        # IPV6 LAN setup

        # Ingresar al menú
        while True:
            try:
                ipv6_setup = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="t4"]')))
                ipv6_setup.click()
                break  # Salir del bucle si se hizo clic con éxito
            except ElementClickInterceptedException:
                # Esperar un momento antes de volver a intentar
                time.sleep(1)

        # Nombres de los checkbox a clickear
        checkbox_names = ['IPv6Enable_Chk', 'IPv6globalenable_Chk']

        # En caso de estar activados los desactiva
        for checkbox_name in checkbox_names:
            self.wait.until(EC.element_to_be_clickable((By.XPATH, f'//*[@name="{checkbox_name}"]')))
            checkbox = driver.find_element_by_name(checkbox_name)

            # Verifica si el checkbox está marcado, de estarlo, lo desmarca
            if checkbox.is_selected():
                checkbox.click()

        # Selecciona radio DHCPV6
        driver.find_element_by_xpath('//*[@name="dhcp6sEnableRadio" and @value="0"]').click()

        # Aplicar cambios
        driver.find_element_by_xpath('//*[@id="Apply_ID"]').click()

        # ------------
        # Serving pool

        # Ingresar al menú
        while True:
            try:
                serving_pool = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="t5"]')))
                serving_pool.click()
                break  # Salir del bucle si se hizo clic con éxito
            except ElementClickInterceptedException:
                # Esperar un momento antes de volver a intentar
                time.sleep(1)

        # Nombres de los checkbox a clickear
        modify_names = ['editClick(0);', 'editClick(1);']

        # Esperar a la aparición del modify
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@onclick="editClick(0);"]')))

        # Por cada modificador ingresa al menú y agrega los datos
        for modify in modify_names:

            # Elemento modificador
            while True:
                try:
                    element = driver.find_element_by_xpath(f'//*[@onclick="{modify}"]')
                    element.click()
                    break
                except ElementClickInterceptedException:
                    # Esperar un momento antes de volver a intentar
                    time.sleep(1)

            driver.switch_to.default_content()
            self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="ConSerDNS1"]')))

            # Aplicar los DNS
            dns1 = driver.find_element_by_xpath('//*[@name="ConSerDNS1"]')
            dns1.clear()
            dns1.send_keys('8.8.8.8')

            dns2 = driver.find_element_by_xpath('//*[@name="ConSerDNS2"]')
            dns2.clear()
            dns2.send_keys('1.1.1.1')

            # Apicar los cambios
            driver.find_element_by_xpath(f'//button[text()="Apply"]').click()

            # Cambiar al marco de base (Network Interface)
            driver.switch_to.frame(self.base_frame)

    def cambio_2g(self):
        driver = self.driver
        driver.get('http://192.168.1.1:8000/cgi-bin/indexmain.cgi')

        # Frame Menu (Network Interface)
        network_interface = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="network"]')))

        # Gesto hover sobre menú de WAN y clickear elemento
        hover_network = ActionChains(driver).move_to_element(network_interface)
        hover_network.perform()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="network-wireless"]/a'))).click()

        # Cambiar al marco de base (Network Interface)
        self.base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainFrame"]')))
        driver.switch_to.frame(self.base_frame)

        # Esperar a la aparición del elemento y configurar SSID
        wifi_name2g = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="SSID"]')))
        wifi_name2g.clear()
        wifi_name2g.send_keys(self.wifiMod)

        # Seleccionar tipo de preámbulo
        self.wait.until(EC.element_to_be_clickable((By.XPATH, "//select[@name='WPAEncrtption']/option[text()='WPA2-PSK']"))).click()

        # Obtener contraseña de fábrica
        wifi_pass = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="PreSharedKey"]')))
        wifi_pass_text = wifi_pass.get_attribute('value')
        self.output_pass = [[wifi_pass_text]]

        while True:
            try:
                # Setear nueva contraseña
                wifi_pass.clear()
                wifi_pass.send_keys(self.numero_aleatorio)

                while True:
                    try:
                        alert = driver.switch_to.alert
                        alert.accept()
                    except NoAlertPresentException:
                        # No hay más alertas, salir del bucle
                        break
                break

            except UnexpectedAlertPresentException:
                pass

        if wifi_pass_text:
            print("¡Contraseña wifi obtenida!")
        else:
            print("Contraseña no obtenida")

        # Guardar configuración
        print('Error?')
        apply2g = driver.find_element_by_id("Apply")
        apply2g.click()

        # Encontrar y aceptar las alertas
        while True:
            try:
                alert = driver.switch_to.alert
                alert.accept()
            except NoAlertPresentException:
                # No hay más alertas, salir del bucle
                break

        # ----------------------------
        # Opciones avanzadas de la red
        while True:
            try:
                advanced = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="t5"]')))
                advanced.click()
                break  # Salir del bucle si se hizo clic con éxito
            except ElementClickInterceptedException:
                # Esperar un momento antes de volver a intentar
                time.sleep(1)

        # Seleccionar tipo de preámbulo
        ipv4_selector = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//select[@name='wlPreamble']/option[text()='Long']")))
        ipv4_selector.click()

        # Guardar configuración
        driver.find_element_by_xpath('//*[@value="Apply"]').click()

        # Obteniendo la contraseña de fábrica
        print("Wifi 2g configurado")
        return self.output_pass, [[self.numero_aleatorio]]

    def cambio_5g(self):
        driver = self.driver
        driver.get('http://192.168.1.1:8000/cgi-bin/indexmain.cgi')

        # Frame Menu (Network Interface)
        network_interface = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="network"]')))

        # Gesto hover sobre menú de WAN y clickear elemento
        hover_network = ActionChains(driver).move_to_element(network_interface)
        hover_network.perform()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="network-wireless5G"]/a'))).click()

        # Cambiar al marco de base (Network Interface)
        self.base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainFrame"]')))
        driver.switch_to.frame(self.base_frame)

        # Esperar a la aparición del elemento y configurar SSID
        wifi_name5g = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="SSID"]')))
        wifi_name5g.clear()
        wifi_name5g.send_keys(self.wifiMod5g)

        # Seleccionar tipo de autorización
        auth_selector = driver.find_element_by_xpath("//select[@name='AuthenticationSelection']/option[@value='psk2']")
        auth_selector.click()

        # Obtener contraseña de fábrica
        wifi_pass = driver.find_element_by_name("PreSharedKey")
        wifi_pass.clear()
        wifi_pass.send_keys(self.numero_aleatorio)

        # Guardar configuración
        apply5g = driver.find_element_by_id("Apply")
        apply5g.click()

        # Encontrar y aceptar las alertas
        while True:
            try:
                alert = driver.switch_to.alert
                alert.accept()
            except NoAlertPresentException:
                # No hay más alertas, salir del bucle
                break

        # ----------------------------
        # Opciones avanzadas de la red
        while True:
            try:
                advanced = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="t3"]')))
                advanced.click()
                break  # Salir del bucle si se hizo clic con éxito
            except ElementClickInterceptedException:
                # Esperar un momento antes de volver a intentar
                time.sleep(1)

        # Seleccionar tipo de preámbulo
        interval = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//select[@name='GuardInterval']/option[@value='0']")))
        interval.click()

        # Guardar configuración
        driver.find_element_by_xpath('//*[@value="Apply"]').click()

        print("Wifi 5g configurado")

    def cambio_contrasena(self):
        driver = self.driver
        tecnico = 'Tecnico2018'
        driver.get('http://192.168.1.1:8000/cgi-bin/indexmain.cgi')

        # Frame Menu (Maintenance Interface)
        maintenance_interface = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="maintenance"]')))

        # Gesto hover sobre menú de Maintenance y clicar elemento
        hover_maintenance = ActionChains(driver).move_to_element(maintenance_interface)
        hover_maintenance.perform()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="maintenance-userAccount"]/a'))).click()

        # Cambiar al marco de base (Wan Interface)
        self.base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainFrame"]')))
        driver.switch_to.frame(self.base_frame)

        if self.contrasenaMod != tecnico:
            # Ingresar la contraseña actual y la nueva contraseña
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='uiViewTools_oldpassword']")))
            driver.find_element_by_name('uiViewTools_oldpassword').send_keys(self.contrasenaMod)
            driver.find_element_by_name('uiViewTools_Password').send_keys(tecnico)
            driver.find_element_by_name('uiViewTools_PasswordConfirm').send_keys(tecnico)

            # Hacer clic en el botón de aplicar cambios
            driver.find_element_by_id('APPLY_ID').click()

            print("Contraseña cambiada con éxito")
        else:
            print("La contraseña actual es igual a la contraseña de técnico, no se realiza ningún cambio.")

    def kill(self):
        driver = self.driver
        driver.close()
