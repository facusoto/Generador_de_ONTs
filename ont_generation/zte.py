import time
import random

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.common.exceptions import WebDriverException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager


class InitZTE:
    def __init__(self, numeroMod, contrasenaMod, wanMod, wifiMod, wifiMod5g, previous_pass):

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
        self.previous_pass = previous_pass

        # Configuración de datos obtenidos
        self.gpon = None
        self.mac = None
        self.potencia = None
        self.output_pass = None
        self.numero_aleatorio = previous_pass if self.previous_pass is not None else random.randint(10000000, 99999999)

    def obtener_datos(self):
        # Ingreso, verificación de potencia y subida de datos de modem
        driver = self.driver

        try:
            driver.get('http://192.168.1.1')
            print("Ingresando a 192.168.1.1")

        except WebDriverException as e:
            # Verifica si el mensaje de error contiene "ERR_CONNECTION_TIMED_OUT"
            if "net::ERR_CONNECTION_TIMED_OUT" in str(e):
                print(f"Se produjo un error de tiempo de espera de conexión, verificá la conexión al modem")
                raise SystemExit

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

        # --------------------------
        # Obtener potencia del módem
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="internet"]'))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="internetStatus"]'))).click()

        # Valor potencia
        while True:
            try:
                self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ponopticalinfo"]'))).click()
                potencia_element = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="RxPower"]'))).text

                # Obtener valor o setearlo en 0
                try:
                    self.potencia = int(''.join(filter(str.isdigit, potencia_element))[:3])
                except ValueError:
                    self.potencia = 0

                break
            except (StaleElementReferenceException, ElementClickInterceptedException):
                time.sleep(1)

        # -----------
        # Obtener MAC
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ethWanStatus"]'))).click()

        # Valor MAC
        mac_element = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="cWorkIFMac:0"]'))).text
        self.mac = [[f"{mac_element.upper().replace(':', '')}"]]

        # ----------
        # Obtener GPON SN
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ponInfo"]'))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ponSn"]'))).click()

        # Valor GPON SN
        while True:
            try:
                gpon_element = driver.find_element_by_xpath('//*[@id="Sn"]')
                gpon_value = gpon_element.get_attribute('value')
                if gpon_value is not None:
                    self.gpon = [[f"{gpon_value.upper().replace('-', '')}"]]
                    break
                else:
                    time.sleep(1)
            except NoSuchElementException:
                time.sleep(1)

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

    def localnet_config(self):
        # Acá se configuran las redes wifi del dispositivo
        driver = self.driver

        while True:
            try:
                # Menu local network
                self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="localnet"]'))).click()

                # -------------------------------------
                # Inicio de configuración de WLAN config
                self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="wlanConfig"]'))).click()

                # -------------------------
                # WLAN Global Configuration
                gc_element = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="WlanBasicAdConfBar"]')))

                # Verifica si el elemento tiene la clase "collapsibleBarExp"
                if "collapsibleBarExp" not in gc_element.get_attribute("class"):
                    # Si no tiene la clase, haz clic en el elemento
                    gc_element.click()

                # ---------------------
                # Una vez abierto el anterior, asegurarse de que el expansible de 2.4 esté abierto
                gc2g_element = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="instName_WlanBasicAdConf:0"]')))

                # Verifica si el elemento tiene la clase "instNameExp"
                if "instNameExp" not in gc2g_element.get_attribute("class"):
                    # Si no tiene la clase, haz clic en el elemento
                    gc2g_element.click()

                # Seleccionar opciones para el 2.4g
                self.wait.until(EC.element_to_be_clickable((By.XPATH, '//select[@id="UI_Channel:0"]')))
                driver.find_element_by_xpath('//select[@id="UI_Channel:0"]/option[@value="1"]').click()
                driver.find_element_by_xpath('//select[@id="CountryCode:0"]/option[@value="USI"]').click()
                driver.find_element_by_xpath('//select[@id="UI_BandWidth:0"]/option[@value="40MHz"]').click()
                # Aplicar cambios y cerrar collapse
                driver.find_element_by_xpath('//*[@id="Btn_apply_WlanBasicAdConf:0"]').click()
                gc2g_element.click()

                # ---------------------
                # Asegurarse de que el expansible de 5g esté abierto
                gc5g_element = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="instName_WlanBasicAdConf:1"]')))

                # Verifica si el elemento tiene la clase "instNameExp"
                if "instNameExp" not in gc5g_element.get_attribute("class"):
                    # Si no tiene la clase, haz clic en el elemento
                    gc5g_element.click()

                # Seleccionar opciones para el 5g
                self.wait.until(EC.element_to_be_clickable((By.XPATH, '//select[@id="UI_Channel:1"]')))
                driver.find_element_by_xpath('//select[@id="UI_Channel:1"]/option[@value="60"]').click()
                driver.find_element_by_xpath('//select[@id="CountryCode:1"]/option[@value="USI"]').click()
                driver.find_element_by_xpath('//select[@id="UI_BandWidth:1"]/option[@value="80MHz"]').click()
                # Aplicar cambios
                driver.find_element_by_xpath('//*[@id="Btn_apply_WlanBasicAdConf:1"]').click()
                gc5g_element.click()
                break

            except Exception:
                time.sleep(1)

        while True:
            try:
                # ---------------
                # WLAN config bar
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
                break

            except Exception:
                time.sleep(1)

        # -----------------
        # LAN CONFIGURATION
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="lanConfig"]'))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="lanMgrIpv6"]'))).click()

        # DHCP6
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="IPv6DHCPServerBar"]'))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="Enable0:IPv6DHCPServer"]'))).click()
        driver.find_element_by_xpath('//*[@id="PrefixMode:IPv6DHCPServer"]').click()
        # Aplicar cambios
        driver.find_element_by_xpath('//*[@id="Btn_apply_IPv6DHCPServer"]').click()
        # Cerrar collapse
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="IPv6DHCPServerBar"]'))).click()

        # RA Service
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="RAServiceBar"]'))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="Enable0:RAService"]'))).click()
        driver.find_element_by_xpath('//*[@id="AdvLinkMTUEnable0"]').click()
        driver.find_element_by_xpath('//*[@id="AdvManagedFlag0"]').click()
        driver.find_element_by_xpath('//*[@id="AdvOtherConfigFlag0"]').click()
        # Aplicar cambios
        driver.find_element_by_xpath('//*[@id="Btn_apply_RAService"]').click()
        # Cerrar collapse
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="RAServiceBar"]'))).click()

        # Port Control
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="IPv6DHCPPortCtlBar"]'))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '(//*[@id="allOn_IPv6DHCPPortCtl"])[2]'))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="Btn_apply_IPv6DHCPPortCtl"]'))).click()

        # -----------------
        # DNS CONFIGURATION
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="dns"]'))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="LocalDnsServerBar"]'))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="sub_SerIPAddress10"]'))).click()

        # Definir un diccionario con nombres y valores
        elementos_dict = {
            "sub_SerIPAddress10": "8",
            "sub_SerIPAddress11": "8",
            "sub_SerIPAddress12": "8",
            "sub_SerIPAddress13": "8",
            "sub_SerIPAddress20": "1",
            "sub_SerIPAddress21": "1",
            "sub_SerIPAddress22": "1",
            "sub_SerIPAddress23": "1"
        }

        # Iterar a través del diccionario y establecer los valores en los elementos input
        for nombre, valor in elementos_dict.items():
            elemento = driver.find_element_by_id(nombre)
            elemento.clear()
            elemento.send_keys(valor)

        # Aplicar cambios
        driver.find_element_by_id('Btn_apply_LocalDnsServer').click()

        print("Cambios de Local Network finalizados")
        return self.output_pass, self.numero_aleatorio

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

        print("Cambios de configuración de internet finalizados")

    def cambio_contrasena(self):
        # Acá se cambia la contraseña de fábrica
        driver = self.driver
        tecnico = 'Tecnico2018'

        # Menú management & diagnosis
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mgrAndDiag"]'))).click()

        # Menú TR069 (Polisón)
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="remoteMgr"]'))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="URL"]'))).click()
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="TR069BasicConfBar"]')))
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="UserName"]')))

        # Elementos para agregar valores random
        random_inputs = ['UserName', 'UserPassword', 'ConnectionRequestUsername', 'ConnectionRequestPassword']
        for elem in random_inputs:
            element = driver.find_element_by_id(elem)
            element.clear()
            element.send_keys(self.numero_aleatorio)

        # Elementos a deseleccionar
        disable_inputs = ['PeriodicInformEnable0', 'SupportCertAuth0', 'RemoteUpgradeCertAuth0']
        for elem in disable_inputs:
            driver.find_element_by_id(elem).click()

        # Aplicar cambios
        driver.find_element_by_id('Btn_apply_TR069BasicConf').click()

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
