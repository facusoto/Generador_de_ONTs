import os
import time
import random
import subprocess

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager


class InitZTE:
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
        self.driver.maximize_window()

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
        self.numero_aleatorio = random.randint(10000000, 99999999)

    def obtener_datos(self):
        pass

    def ont_progress(self):
        # Ingreso a la página 192.168.1.100
        driver = self.driver
        driver.get('http://192.168.1.100')

        # Ingresando a configuración avanzada
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="Frm_Username"]')))
        user_login = driver.find_element_by_xpath('//*[@id="Frm_Username"]')
        user_login.clear()
        user_login.send_keys('admin')

        pass_login = driver.find_element_by_xpath('//*[@id="Frm_Password"]')
        pass_login.clear()
        pass_login.send_keys(self.contrasenaMod)

        # Inciar sesión
        driver.find_element_by_xpath('//*[@id="LoginId"]').click()

    def upload_configuration(self):
        # Acá se lee la configuración con el archivo BIN
        driver = self.driver

        # Menú management & diagnosis
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mgrAndDiag"]'))).click()

        # System management
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="devMgr"]'))).click()

        # User Configuration Management
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="usrCfgMgr"]'))).click()

        # Restore User Configuration
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="UserConfUploadBar"]'))).click()

        # -----------------------------------------
        # File input (realiza subida de archivo acá)
        ruta_relativa = 'config.bin'

        # Obtiene el directorio actual
        directorio_actual = os.path.dirname(__file__)

        # Obtiene la ruta absoluta del archivo
        ruta_absoluta = os.path.join(directorio_actual, ruta_relativa)

        upload_input = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ConfigUpload"]')))
        upload_input.send_keys(ruta_absoluta)

        # Subir configuración
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="Btn_Upload"]'))).click()

        # Aceptar configuración
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="confirmOK"]'))).click()

    def localnet_config(self):
        # Acá se configuran las redes wifi del dispositivo
        url_objetivo = 'http://192.168.1.100/'
        driver = self.driver

        while True:
            try:
                subprocess.check_output(['ping', '-n', '1', url_objetivo])  # Realiza un ping a la URL objetivo

                # Si el ping tiene éxito, espera un tiempo y luego intenta nuevamente cargar la página
                print('Se logro ingresar nuevamente')
                time.sleep(3)  # Espera 10 segundos antes de volver a verificar
                driver.get(url_objetivo)  # Carga la página con Selenium

                # Realiza el ingreso nuevamente
                self.ont_progress()

                # Termina el bucle si la página se carga correctamente
                break

            except subprocess.CalledProcessError:
                # Si el ping falla, espera un tiempo y vuelve a intentarlo
                # time.sleep(10)  # Espera 10 segundos antes de volver a verificar
                print('Verificando ip nuevamente')

        # Menu local network
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="localnet"]'))).click()

        # -------------------------------------
        # Inicio de configuración de WAN config
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="wlanConfig"]'))).click()

        # Wan config bar
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="WLANSSIDConfBar"]'))).click()

        # Lista de elementos a desactivar (Esperar a que el siguiente sea clickeable)
        disable_elements = ["Enable0:1", "Enable0:2", "Enable0:3", "Enable0:5", "Enable0:6", "Enable0:7"]

        for element in disable_elements:
            self.wait.until(EC.element_to_be_clickable((By.XPATH, f'//*[@id="{element}"]'))).click()

        # Lista de elementos a activar
        enable_elements = ["Enable1:0", "Enable1:4"]

        for element in enable_elements:
            self.wait.until(EC.element_to_be_clickable((By.XPATH, f'//*[@id="{element}"]'))).click()

        # ------------------------
        # Configurador red 2.4 GHz
        wifi_element = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="instName_WLANSSIDConf:0"]')))

        # Verifica si el elemento tiene la clase "instNameExp"
        if "instNameExp" not in wifi_element.get_attribute("class"):
            # Si no tiene la clase, haz clic en el elemento
            wifi_element.click()

        # Cambio de nombre de red
        ssid_name = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ESSID:0"]')))
        ssid_name.clear()
        ssid_name.send_keys(self.wifiMod)

        # Bullet ocultar red
        driver.find_element_by_xpath('//*[@id="ESSIDHideEnable1:0"]').click()
        # Selector tipo encriptacion
        driver.find_element_by_xpath('//select[@id="EncryptionType:0"]/option[@value="WPA/WPA2-PSK-TKIP/AES"]').click()

        # Cambio de contraseña
        ssid_pass = driver.find_element_by_xpath('//*[@id="KeyPassphrase:0"]')
        ssid_pass.clear()
        ssid_pass.send_keys(self.numero_aleatorio)

        # Bullet Insolación
        driver.find_element_by_xpath('//*[@id="VapIsolationEnable0:0"]').click()

        # Aplicar cambios y hacer collapse
        driver.find_element_by_xpath('//*[@id="Btn_apply_WLANSSIDConf:0"]').click()
        wifi_element.click()

        # ------------------------
        # Configurador red 5 GHz
        wifi_element = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="instName_WLANSSIDConf:4"]')))

        # Verifica si el elemento tiene la clase "instNameExp"
        if "instNameExp" not in wifi_element.get_attribute("class"):
            # Si no tiene la clase, haz clic en el elemento
            wifi_element.click()

        # Cambio de nombre de red
        ssid_name = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ESSID:4"]')))
        ssid_name.clear()
        ssid_name.send_keys(self.wifiMod)

        # Bullet ocultar red
        driver.find_element_by_xpath('//*[@id="ESSIDHideEnable1:4"]').click()
        # Selector tipo encriptacion
        driver.find_element_by_xpath('//select[@id="EncryptionType:4"]/option[@value="WPA/WPA2-PSK-TKIP/AES"]').click()

        # Cambio de contraseña
        ssid_pass = driver.find_element_by_xpath('(//*[@id="KeyPassphrase:4"])[1]')
        ssid_pass.clear()
        ssid_pass.send_keys(self.numero_aleatorio)

        # Bullet Insolación
        driver.find_element_by_xpath('//*[@id="VapIsolationEnable0:4"]').click()

        # Aplicar cambios
        driver.find_element_by_xpath('//*[@id="Btn_apply_WLANSSIDConf:4"]').click()

    def internet_config(self):
        # Acá se configura la WAN service
        driver = self.driver

        # Menú internet
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="internet"]'))).click()

        # Menú WAN
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="internetConfig"]'))).click()

        # Submenú WAN
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ethWanConfig"]'))).click()

        # WAN collapse
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="InternetBar"]')))

        while True:
            try:
                current_wans = driver.find_elements_by_xpath("//*[contains(@id,'instDelete_Internet')][not(ancestor::*/@style='display:none;')]")
                # Elimina las wan preexistentes
                for wan in current_wans:
                    wan.click()
                break
            except Exception as e:
                print('Sin Wan preexistentes')
                print(e)

        # New wan collapse
        while True:
            try:
                self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="addInstBar_Internet"]'))).click()

                # New wan name
                new_namw = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="WANCName:1"]')))
                new_namw.clear()
                new_namw.send_keys("WAN")

                # Wan name
                ppp_username = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="UserName:1"]')))
                ppp_username.clear()
                ppp_username.send_keys(self.wanMod)

                # Wan password
                ppp_username = driver.find_element_by_xpath('//*[@id="Password:1"]')
                ppp_username.clear()
                ppp_username.send_keys('123456')

                # Wan ip mode
                driver.find_element_by_xpath('//select[@id="IpMode:1"]/option[@value="IPv4"]').click()

                # Nat enable
                driver.find_element_by_xpath('//*[@id="IsNAT1:1"]').click()

                # VLAN enable
                driver.find_element_by_xpath('//*[@id="VlanEnable1:1"]').click()

                # Vlan id max
                vlan_man = driver.find_element_by_xpath('//*[@id="VLANID:1"]')
                vlan_man.clear()
                vlan_man.send_keys('10')

                # Vlan id min
                vlan_min = driver.find_element_by_xpath('//*[@id="DSCP:1"]')
                vlan_min.clear()
                vlan_min.send_keys('-1')

                # Aplicar cambios
                driver.find_element_by_xpath('//*[@id="Btn_apply_internet:1"]').click()
                break

            except (StaleElementReferenceException, ElementClickInterceptedException):
                time.sleep(1)

    def cambio_contrasena(self):
        # Acá se cambia la contraseña de fábrica
        driver = self.driver
        tecnico = 'Tecnico2018'

        # Menú management & diagnosis
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mgrAndDiag"]'))).click()

        # Menú Account management
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="accountMgr"]'))).click()

        # Password inputs
        if self.contrasenaMod != tecnico:
            old_pass = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="Password:0"]')))
            old_pass.send_keys(self.contrasenaMod)
            new_pass = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="NewPassword:0"]')))
            new_pass.send_keys(tecnico)
            rep_pass = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="NewConfirmPassword:0"]')))
            rep_pass.send_keys(tecnico)

            # Hacer clic en el botón de aplicar cambios
            driver.find_element_by_xpath('//*[@id="Btn_apply_AccountManag:0"]').click()

            print("Contraseña cambiada con éxito")
        else:
            print("La contraseña actual es igual a la contraseña de técnico, no se realiza ningún cambio.")

    def kill(self):
        driver = self.driver
        driver.quit()
