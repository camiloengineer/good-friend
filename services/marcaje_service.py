"""
Servicio de marcaje automático usando Selenium.
"""
import threading
import pytz
import logging
from datetime import datetime
from time import sleep
from typing import List, Dict, Tuple
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from utils.rut_validator import RutValidator
from utils.delay_manager import DelayManager
from .email_service import EmailService


class MarcajeService:
    """Servicio principal para realizar marcajes automáticos."""
    
    def __init__(self, email_service: EmailService, delay_manager: DelayManager, debug_mode: bool = False):
        self.email_service = email_service
        self.delay_manager = delay_manager
        self.debug_mode = debug_mode
        self.chile_tz = pytz.timezone('America/Santiago')
    
    def process_rut(self, rut: str, exceptions_list: List[str]) -> None:
        """Procesar un RUT individual."""
        current_thread = threading.current_thread()
        rut_masked = RutValidator.mask_rut(rut)

        # Verificar si el RUT está en la lista de excepciones
        if RutValidator.is_rut_exception(rut, exceptions_list):
            print(f"🚫 [Hilo {current_thread.name}] RUT {rut_masked} está en lista de excepciones - SALTANDO")
            logging.info(f"RUT {rut_masked} saltado por estar en lista de excepciones")
            self.email_service.send_exception_email(rut_masked, rut=rut)
            return

        # Capturar logs para el email
        log_messages = []
        start_time = datetime.now(self.chile_tz)

        try:
            log_messages.append(f"🚀 Iniciando procesamiento RUT: {rut_masked} a las {start_time.strftime('%H:%M:%S')} (CLT)")
            print(f"🚀 [Hilo {current_thread.name}] Iniciando RUT {rut_masked} a las {start_time.strftime('%H:%M:%S')} (CLT)")

            # Aplicar delay aleatorio si no está en modo debug
            self._apply_delay(rut, current_thread)

            # Determinar tipo de acción y ejecutar marcaje
            action_type = self._determine_action_type()
            message = self._execute_marcaje(rut, action_type, log_messages, current_thread)

            print(f"✅ [Hilo {current_thread.name}] Marcaje completado para RUT: {rut_masked}")

            # Enviar correo de confirmación
            print(f"📧 [Hilo {current_thread.name}] Enviando correo de confirmación...")
            self.email_service.send_success_email(rut_masked, action_type, message, self.debug_mode, rut=rut)

        except Exception as e:
            self._handle_error(e, rut_masked, log_messages, current_thread, rut=rut)

        finally:
            self._log_completion(rut_masked, start_time, current_thread)
    
    def _apply_delay(self, rut: str, current_thread):
        """Aplicar delay aleatorio si no está en modo debug."""
        if not self.debug_mode:
            delay_minutes = self.delay_manager.get_random_delay(rut)
            print(f"⏰ [Hilo {current_thread.name}] Aplicando delay aleatorio para RUT {RutValidator.mask_rut(rut)}: {delay_minutes} minutos")
            print(f"⏳ [Hilo {current_thread.name}] Esperando para simular comportamiento humano...")
            logging.info(f"Aplicando delay de {delay_minutes} minutos para RUT {RutValidator.mask_rut(rut)}")
            sleep(delay_minutes * 60)  # Convertir minutos a segundos
            print(f"✅ [Hilo {current_thread.name}] Delay completado para RUT {RutValidator.mask_rut(rut)}, continuando...")
        else:
            print(f"🔄 [Hilo {current_thread.name}] Modo DEBUG activo: sin delay para RUT {RutValidator.mask_rut(rut)}")
    
    def _determine_action_type(self) -> str:
        """Determinar si es entrada o salida según la hora."""
        chile_time = datetime.now(self.chile_tz)
        return "ENTRADA" if 5 <= chile_time.hour < 12 else "SALIDA"
    
    def _execute_marcaje(self, rut: str, action_type: str, log_messages: List[str], current_thread) -> str:
        """Ejecutar el marcaje propiamente tal."""
        chile_time = datetime.now(self.chile_tz)
        
        print(f"🕐 [Hilo {current_thread.name}] Hora Chile: {chile_time.strftime('%H:%M:%S')} (CLT)")
        print(f"📍 [Hilo {current_thread.name}] Ubicación: Sin coordenadas")
        print(f"🔍 [Hilo {current_thread.name}] Tipo de marcaje: {action_type}")

        if self.debug_mode:
            log_messages.append("🧪 Modo DEBUG activo - simulando marcaje")
            return f"🧪 DEBUG activo: no se ejecutó marcaje. Hora Chile: {chile_time.strftime('%H:%M:%S')} (CLT)"
        else:
            return self._execute_real_marcaje(rut, action_type, log_messages, current_thread, chile_time)
    
    def _execute_real_marcaje(self, rut: str, action_type: str, log_messages: List[str], current_thread, chile_time) -> str:
        """Ejecutar marcaje real usando Selenium."""
        log_messages.append("⚡ Iniciando marcaje real...")
        print(f"⚡ [Hilo {current_thread.name}] Iniciando marcaje real...")

        # Configurar Chrome options
        options = self._get_chrome_options()
        
        print(f"🌐 [Hilo {current_thread.name}] Iniciando navegador sin geolocalización...")
        driver = webdriver.Chrome(options=options)

        try:
            # Deshabilitar geolocalización con JavaScript
            driver.execute_script("""
                navigator.geolocation.getCurrentPosition = function(success, error) {
                    if (error) error({ code: 1, message: 'User denied Geolocation' });
                };
                navigator.geolocation.watchPosition = function() { return null; };
            """)

            # Navegar a la página
            print(f"🌐 [Hilo {current_thread.name}] Cargando página de marcaje...")
            driver.get("https://app.ctrlit.cl/ctrl/dial/web/K1NBpBqyjf")
            driver.implicitly_wait(10)
            sleep(2)

            # Hacer clic en el botón de acción
            self._click_action_button(driver, action_type, current_thread)
            
            # Ingresar RUT
            self._enter_rut(driver, rut, current_thread)
            
            # Enviar formulario
            self._submit_form(driver, current_thread)

        finally:
            driver.quit()
            print(f"🌐 [Hilo {current_thread.name}] Navegador cerrado")

        # Crear mensaje de éxito
        log_summary = "\n".join(log_messages[-10:])
        return f"""✅ {action_type} realizada con éxito a las {chile_time.strftime('%H:%M:%S')} (Chile - CLT).
📍 Geolocalización: Sin coordenadas
📍 Ubicación: Sin dirección

📋 LOGS DEL PROCESO:
{log_summary}"""
    
    def _get_chrome_options(self) -> Options:
        """Obtener opciones de Chrome configuradas."""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-geolocation")
        options.add_argument("--disable-features=VizDisplayCompositor")
        
        prefs = {
            "profile.default_content_setting_values.geolocation": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.geolocation": 2
        }
        options.add_experimental_option("prefs", prefs)
        return options
    
    def _click_action_button(self, driver, action_type: str, current_thread):
        """Hacer clic en el botón de entrada o salida."""
        print(f"🔘 [Hilo {current_thread.name}] Buscando botón {action_type}...")
        boton = next((el for el in driver.find_elements(By.CSS_SELECTOR, 'button, div, span, li')
                     if el.text.strip().upper() == action_type), None)
        if not boton:
            raise Exception(f"No se encontró botón {action_type}")
        
        print(f"👆 [Hilo {current_thread.name}] Click en botón {action_type}")
        boton.click()
        sleep(2)
    
    def _enter_rut(self, driver, rut: str, current_thread):
        """Ingresar RUT en el formulario."""
        print(f"🔢 [Hilo {current_thread.name}] Ingresando RUT: {RutValidator.mask_rut(rut)}")
        buttons = driver.find_elements(By.CSS_SELECTOR, "li.digits")
        available_buttons = [el.text.strip() for el in buttons]
        print(f"📱 [Hilo {current_thread.name}] Botones disponibles: {available_buttons}")

        for i, char in enumerate(rut):
            print(f"🔤 [Hilo {current_thread.name}] Ingresando carácter {i+1}/{len(rut)}")
            found = False
            for el in buttons:
                if el.text.strip().upper() == char.upper():
                    el.click()
                    found = True
                    break
            if not found:
                raise Exception(f"No se encontró el carácter: {char}")
            sleep(0.3)
        
        sleep(1)
    
    def _submit_form(self, driver, current_thread):
        """Enviar el formulario."""
        print(f"📤 [Hilo {current_thread.name}] Enviando formulario...")
        enviar = next((el for el in driver.find_elements(By.CSS_SELECTOR, 'li.pad-action.digits')
                      if el.text.strip().upper() == "ENVIAR"), None)
        if not enviar:
            raise Exception("No se encontró botón ENVIAR")
        enviar.click()
        sleep(1)
    
    def _handle_error(self, error: Exception, rut_masked: str, log_messages: List[str], current_thread, rut: str = None):
        """Manejar errores durante el procesamiento."""
        error_msg = f"""❌ Error en marcaje para RUT {rut_masked}:
{str(error)}

📋 LOGS DEL PROCESO:
{chr(10).join(log_messages)}"""
        
        print(error_msg)
        logging.error(error_msg)

        # Enviar correo de error
        print(f"📧 [Hilo {current_thread.name}] Enviando correo de error...")
        action_type = "MARCAJE"  # Valor por defecto si no se pudo determinar
        self.email_service.send_error_email(rut_masked, action_type, error_msg, rut=rut)
    
    def _log_completion(self, rut_masked: str, start_time: datetime, current_thread):
        """Registrar la finalización del proceso."""
        end_time = datetime.now(self.chile_tz)
        duration = (end_time - start_time).total_seconds()
        minutes, seconds = divmod(duration, 60)

        print(f"🏁 [Hilo {current_thread.name}] Proceso finalizado para RUT: {rut_masked} a las {end_time.strftime('%H:%M:%S')} (CLT)")
        print(f"⏱️ [Hilo {current_thread.name}] Duración total: {int(minutes)} minutos y {int(seconds)} segundos")
