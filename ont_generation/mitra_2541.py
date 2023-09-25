import random
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager


class Init2541:
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
        self.output_data = None
        self.potencia = None
        self.output_pass = None
        self.base_frame = None
        self.menu_frame = None
        self.numero_aleatorio = random.randint(10000000, 99999999)

    def obtener_datos(self):
        driver = self.driver
        # Ingreso, verificación de potencia y subida de datos de modem
        try:
            print('\t>Version de pruebas, no olvides deshacer los cambios y borrar este mensaje! (POTENCIA)')
            driver.get('http://192.168.1.100')
            print("Ingresando a 192.168.1.100")

        except WebDriverException as e:
            # Verifica si el mensaje de error contiene "ERR_CONNECTION_TIMED_OUT"
            if "net::ERR_CONNECTION_TIMED_OUT" in str(e):
                print(f"Se produjo un error de tiempo de espera de conexión, verificá la conexión al modem")
                raise SystemExit

        # Campo contraseña
        input_password = driver.find_element_by_name('pass')
        input_password.send_keys(self.contrasenaMod)

        # Buscar y cliquear botón de ingreso (cambiante)
        try:
            login_enter = driver.find_element_by_class_name('sendBtu2')
            login_enter.click()

        except NoSuchElementException:
            login_enter = driver.find_element_by_class_name('sendBtu')
            login_enter.click()

        # Variables a utilizar
        gpon_element = ''
        mac_element = ''
        potencia_element = ''

        # Verificar si la URL ha cambiado debido a la contraseña incorrecta
        if "logIn_mhs_pw_error.html" in driver.current_url:
            print("Contraseña incorrecta. Corrige la contraseña en Google sheets y vuelve a intentar.")
            # Puedes lanzar una excepción aquí o realizar otra acción adecuada.
        else:
            # Toma de valores en dos modelos
            try:
                # Obtén los elementos modelo 1
                gpon_element = driver.find_element_by_xpath('//*[@id="gsn"]').text
                mac_element = driver.find_element_by_xpath('//*[@class="FLOATBOX"][1]//div[9]/span').text
                potencia_element = driver.find_element_by_xpath('//*[@class="FLOATBOX"][3]//div[3]/span[1]').text

            except NoSuchElementException:
                # Obtén los elementos modelo 2
                gpon_element = driver.find_element_by_xpath('//*[@id="gsn"]').text
                mac_element = driver.find_element_by_xpath('/html/body/div/div[1]/div[5]/div[3]/div[2]/div[9]').text
                potencia_element = driver.find_element_by_xpath('/html/body/div/div[1]/div[7]/div[2]/div[3]/span[1]').text

            except TimeoutException:
                print("No se pudo acceder y obtener los datos")

            # Formatea las cadenas de texto de manera más clara
            modelo = "MODELO: Mitrastar 2541\n"
            gpon_replaced = f"GPON SN: <{gpon_element.replace('-', '')}>\n"
            mac_replaced = f"MAC: {mac_element.replace(':', '')}"
            self.output_data = [[modelo + gpon_replaced + mac_replaced]]

            self.potencia = int(''.join(filter(str.isdigit, potencia_element))[:3])

            # BORRAR!
            if self.potencia == 0:
                self.potencia = 210

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

            return self.output_data, self.potencia

    def ont_progress(self):
        # Ingreso a la página 192.168.1.100:8000
        driver = self.driver
        driver.get('http://192.168.1.100/logIn_main.html')

        # Ingresando a configuración avanzada
        user = driver.find_element_by_name("user")
        user.send_keys("admin")

        password = driver.find_element_by_name("pass")
        password.send_keys(self.contrasenaMod)

        entrar = driver.find_element_by_name("acceptLogin")
        entrar.click()

    def cambio_wan(self):
        driver = self.driver
        new_url = 'http://192.168.1.100:8000/wancfg.cmd'

        # Obtener el frame, cambiar su URL y hacerle Switch
        driver.switch_to.default_content()
        self.base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='basefrm']")))
        driver.execute_script(f"arguments[0].src = '{new_url}';", self.base_frame)
        driver.switch_to.frame(self.base_frame)

        # Eliminar configuración previa
        try:
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@name='rml']")))
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

        driver.find_element_by_name("enblNat").click()
        driver.find_element_by_xpath("//input[@value='Next']").click()

        driver.find_element_by_xpath("//input[@value='Next']").click()
        driver.find_element_by_xpath("//input[@value='Next']").click()

        # Finalizar configuración
        driver.find_element_by_xpath("//input[@value='Apply/Save']").click()

        print("Cambio de WAN")

    def cambios_varios(self):
        driver = self.driver

        # ---------------------------
        # Configuración de DNS Server
        new_url = 'http://192.168.1.100:8000/dnscfg.html'

        # Obtener el frame, cambiar su URL y hacerle Switch
        driver.switch_to.default_content()
        self.base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='basefrm']")))
        driver.execute_script(f"arguments[0].src = '{new_url}';", self.base_frame)
        driver.switch_to.frame(self.base_frame)

        # Utilizar esta DNS
        driver.find_element_by_xpath('(//input[@name="dns"])[2]').click()

        # Agregar DNS
        ssid2g = driver.find_element_by_name("dnsPrimary")
        ssid2g.clear()
        ssid2g.send_keys('8.8.8.8')

        ssid2g = driver.find_element_by_name("dnsSecondary")
        ssid2g.clear()
        ssid2g.send_keys('1.1.1.1')

        driver.find_element_by_xpath("//input[@value='Apply/Save']").click()

        # ---------------------
        # Configuración de UPNP
        new_url = 'http://192.168.1.100:8000/upnpcfg.html'

        # Obtener el frame, cambiar su URL y hacerle Switch
        driver.switch_to.default_content()
        self.base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='basefrm']")))
        driver.execute_script(f"arguments[0].src = '{new_url}';", self.base_frame)
        driver.switch_to.frame(self.base_frame)

        # Encuentra el elemento checkbox por su atributo "name"
        checkbox_element = driver.find_element_by_name('chkUpnp')

        # Verifica si el checkbox está marcado, de no estarlo lo marca
        if not checkbox_element.is_selected():
            checkbox_element.click()

        driver.find_element_by_xpath("//input[@value='Apply/Save']").click()

        # ---------------------
        # Configuración de IPv6
        new_url = 'http://192.168.1.100:8000/ipv6lancfg.html'

        # Obtener el frame, cambiar su URL y hacerle Switch
        driver.switch_to.default_content()
        self.base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='basefrm']")))
        driver.execute_script(f"arguments[0].src = '{new_url}';", self.base_frame)
        driver.switch_to.frame(self.base_frame)

        # Encuentra el elemento checkbox por su atributo "name"
        checkbox_element = driver.find_elements_by_xpath('//input[@type="checkbox" and not(@name="enableRadvdUla")]')

        # Verifica si el checkbox está marcado, de no estarlo lo marca
        for element in checkbox_element:
            if element.is_selected():
                element.click()

        driver.find_element_by_xpath("//input[@value='Save/Apply']").click()

    def cambio_2g(self):
        driver = self.driver
        new_url = 'http://192.168.1.100:8000/wlcfg.html'

        # Obtener el frame, cambiar su URL y hacerle Switch
        driver.switch_to.default_content()
        self.base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='basefrm']")))
        driver.execute_script(f"arguments[0].src = '{new_url}';", self.base_frame)
        driver.switch_to.frame(self.base_frame)

        # Cambiar nombre SSID
        ssid2g = driver.find_element_by_name("wlSsid")
        ssid2g.clear()
        ssid2g.send_keys(self.wifiMod)

        # Cambiar región
        driver.find_element_by_xpath("//select[@name='wlCountry']/option[text()='UNITED STATES']").click()
        apply2g = driver.find_element_by_xpath("//input[@value='Apply/Save']")
        apply2g.click()

        # Ir a la página de seguridad
        new_url = 'http://192.168.1.100:8000/wlsecurity.html'

        # Obtener el frame, cambiar su URL y hacerle Switch
        driver.switch_to.default_content()
        self.base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='basefrm']")))
        driver.execute_script(f"arguments[0].src = '{new_url}';", self.base_frame)
        driver.switch_to.frame(self.base_frame)

        # Obteniendo la contraseña de fábrica
        try:
            driver.find_element_by_id("revealcheck").click()
            wifi_pass = driver.find_element_by_id("wifiPass")
            wifi_pass_text = wifi_pass.get_attribute('value')
            self.output_pass = [[wifi_pass_text]]

            # Setear la contraseña
            wifi_pass.clear()
            wifi_pass.send_keys(self.numero_aleatorio)

        except ElementNotInteractableException:
            print("Red wifi actualmente abierta, no reiniciaste el modem de fábrica")

        if self.output_pass is not None:
            print("¡Contraseña wifi obtenida!")
        else:
            print("Contraseña no obtenida")

        # Guargar configuración
        driver.find_element_by_xpath("//input[@value='Apply/Save']").click()

        print("Wifi 2g configurado")
        return self.output_pass, [[self.numero_aleatorio]]

    def cambio_5g(self):
        driver = self.driver
        new_url = 'http://192.168.1.100:8000/wlextcfg.html'

        # Obtener el frame, cambiar su URL y hacerle Switch
        driver.switch_to.default_content()
        self.base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='basefrm']")))
        driver.execute_script(f"arguments[0].src = '{new_url}';", self.base_frame)
        driver.switch_to.frame(self.base_frame)

        # Cambiar nombre SSID
        ssid5g = driver.find_element_by_name("wlSsid")
        ssid5g.clear()
        ssid5g.send_keys(self.wifiMod5g)

        # Cambiar contraseña
        ssid5g = driver.find_element_by_name("wlWpaPsk")
        ssid5g.clear()
        ssid5g.send_keys(self.numero_aleatorio)

        driver.find_element_by_xpath("//input[@value='Apply/Save']").click()

        print("Wifi 5g configurado")

    def cambio_contrasena(self):
        driver = self.driver
        new_url = 'http://192.168.1.100:8000/password.html'

        # Obtener el frame, cambiar su URL y hacerle Switch
        driver.switch_to.default_content()
        self.base_frame = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@name='basefrm']")))
        driver.execute_script(f"arguments[0].src = '{new_url}';", self.base_frame)
        driver.switch_to.frame(self.base_frame)

        tecnico = "Tecnico2018"
        if self.contrasenaMod != tecnico:
            try:
                driver.find_element_by_name("userName").send_keys("admin")
                driver.find_element_by_name("pwdOld").send_keys(self.contrasenaMod)
                driver.find_element_by_name("pwdNew").send_keys("Tecnico2018")
                driver.find_element_by_name("pwdCfm").send_keys("Tecnico2018")

            except NoSuchElementException:
                print("Error, no encontrado (?")

            apply_manage = driver.find_element_by_xpath("//input[@value='Apply/Save']")
            apply_manage.click()

            print("Cambio de contraseña")
        else:
            print("La contraseña actual es igual a la contraseña de técnico, no se realiza ningún cambio.")

    def kill(self):
        driver = self.driver
        driver.quit()

