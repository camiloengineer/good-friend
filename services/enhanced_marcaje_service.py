"""
Servicio de marcaje automático Enterprise-Grade con retry logic, circuit breakers y observabilidad.
"""
import threading
import pytz
import logging
import time
from datetime import datetime
from time import sleep
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

from utils.rut_validator import RutValidator
from utils.delay_manager import DelayManager
from utils.logger import StructuredLogger, MetricsCollector
from utils.advanced_config import CircuitBreaker
from .email_service import EmailService


class EnhancedMarcajeService:
    """Servicio Enterprise-Grade para realizar marcajes automáticos."""
    
    def __init__(self, email_service: EmailService, delay_manager: DelayManager, 
                 debug_mode: bool = False, execution_config=None, metrics_collector: MetricsCollector = None):
        self.email_service = email_service
        self.delay_manager = delay_manager
        self.debug_mode = debug_mode
        self.execution_config = execution_config
        self.metrics_collector = metrics_collector or MetricsCollector()
        self.chile_tz = pytz.timezone('America/Santiago')
        self.circuit_breaker = CircuitBreaker(
            threshold=execution_config.circuit_breaker_threshold if execution_config else 3
        )
    
    def process_rut(self, rut: str) -> bool:
        """Procesar un RUT individual con retry logic y circuit breaker."""
        current_thread = threading.current_thread()
        rut_masked = RutValidator.mask_rut(rut)
        start_time = datetime.now(self.chile_tz)

        # Verificar circuit breaker
        if not self.circuit_breaker.can_execute():
            print(f"🚫 [Hilo {current_thread.name}] Circuit breaker ABIERTO - saltando RUT {rut_masked}")
            StructuredLogger.log_error(rut_masked, "Circuit breaker abierto")
            return False

        print(f"🚀 [Hilo {current_thread.name}] INICIANDO RUT {rut_masked}")
        StructuredLogger.log_rut_start(rut_masked)
        self.metrics_collector.record_rut_start()

        # Intentar con retry logic
        max_attempts = self.execution_config.retry_attempts + 1 if self.execution_config else 1
        
        for attempt in range(max_attempts):
            try:
                success = self._process_rut_attempt(rut, rut_masked, current_thread, attempt + 1, max_attempts)
                
                if success:
                    # Registrar éxito
                    duration = (datetime.now(self.chile_tz) - start_time).total_seconds()
                    action_type = self._determine_action_type()
                    
                    StructuredLogger.log_rut_complete(rut_masked, action_type, duration)
                    self.metrics_collector.record_success(duration)
                    self.circuit_breaker.record_success()
                    
                    print(f"✅ [Hilo {current_thread.name}] RUT {rut_masked} procesado exitosamente")
                    return True
                
            except Exception as e:
                print(f"❌ [Hilo {current_thread.name}] Intento {attempt + 1}/{max_attempts} falló para RUT {rut_masked}: {str(e)}")
                StructuredLogger.log_error(rut_masked, str(e))
                
                # Si no es el último intento y tenemos retry configurado
                if attempt < max_attempts - 1 and self.execution_config:
                    retry_delay = self.execution_config.retry_delay_seconds
                    print(f"⏳ [Hilo {current_thread.name}] Esperando {retry_delay}s antes del siguiente intento...")
                    time.sleep(retry_delay)
                    continue
                
                # Último intento fallido
                self.circuit_breaker.record_failure()
                self.metrics_collector.record_error()
                self._handle_error(e, rut_masked, [], current_thread, rut=rut)
                return False
        
        return False
    
    def _process_rut_attempt(self, rut: str, rut_masked: str, current_thread, attempt: int, max_attempts: int) -> bool:
        """Procesar un intento individual de marcaje para un RUT."""
        log_messages = []
        
        start_time = datetime.now(self.chile_tz)
        log_messages.append(f"🚀 Intento {attempt}/{max_attempts} - Iniciando procesamiento RUT: {rut_masked} a las {start_time.strftime('%H:%M:%S')} (CLT)")
        print(f"🚀 [Hilo {current_thread.name}] Intento {attempt}/{max_attempts} - Iniciando RUT {rut_masked} a las {start_time.strftime('%H:%M:%S')} (CLT)")

        try:
            # Aplicar delay aleatorio si no está en modo debug
            print(f"⏰ [Hilo {current_thread.name}] Aplicando delay para RUT {rut_masked}...")
            self._apply_delay(rut, current_thread)
            print(f"✅ [Hilo {current_thread.name}] Delay completado para RUT {rut_masked}")

            # Determinar tipo de acción y ejecutar marcaje
            print(f"🔍 [Hilo {current_thread.name}] Determinando tipo de acción para RUT {rut_masked}...")
            action_type = self._determine_action_type()
            print(f"📝 [Hilo {current_thread.name}] Tipo de acción: {action_type}")
            
            print(f"⚡ [Hilo {current_thread.name}] EJECUTANDO MARCAJE para RUT {rut_masked}...")
            logging.info(f"EJECUTANDO marcaje {action_type} para RUT {rut_masked}")
            
            message = self._execute_marcaje(rut, action_type, log_messages, current_thread)
            
            print(f"✅ [Hilo {current_thread.name}] MARCAJE COMPLETADO para RUT: {rut_masked}")
            logging.info(f"MARCAJE COMPLETADO {action_type} para RUT {rut_masked}")

            # Enviar correo de confirmación
            print(f"📧 [Hilo {current_thread.name}] Enviando correo de confirmación...")
            self.email_service.send_success_email(rut_masked, action_type, message, self.debug_mode, rut=rut)
            print(f"✅ [Hilo {current_thread.name}] Email enviado para RUT {rut_masked}")
            
            return True
            
        except Exception as e:
            print(f"❌ [Hilo {current_thread.name}] ERROR en intento {attempt} para RUT {rut_masked}: {str(e)}")
            logging.error(f"ERROR en intento {attempt} para RUT {rut_masked}: {str(e)}")
            raise e  # Re-lanzar para manejo en nivel superior
        
        finally:
            print(f"🏁 [Hilo {current_thread.name}] FINALIZANDO intento {attempt} para RUT {rut_masked}")
            logging.info(f"FINALIZANDO intento {attempt} para RUT {rut_masked}")
    
    def _apply_delay(self, rut: str, current_thread):
        """Aplicar delay aleatorio si no está en modo debug."""
        if not self.debug_mode:
            delay_minutes = self.delay_manager.get_random_delay(rut)
            print(f"⏰ [Hilo {current_thread.name}] Aplicando delay aleatorio para RUT {RutValidator.mask_rut(rut)}: {delay_minutes} minutos")
            print(f"⏳ [Hilo {current_thread.name}] Esperando para simular comportamiento humano...")
            logging.info(f"Aplicando delay de {delay_minutes} minutos para RUT {RutValidator.mask_rut(rut)}")
            self.metrics_collector.record_delay_applied()
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
        """Ejecutar marcaje real usando Selenium con manejo robusto de errores."""
        log_messages.append("⚡ Iniciando marcaje real...")
        print(f"⚡ [Hilo {current_thread.name}] Iniciando marcaje real...")

        driver = None
        try:
            # Configurar Chrome options
            options = self._get_chrome_options()
            
            print(f"🌐 [Hilo {current_thread.name}] Iniciando navegador sin geolocalización...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(30)  # Timeout de 30 segundos

            # Deshabilitar geolocalización con JavaScript
            driver.execute_script("""
                navigator.geolocation.getCurrentPosition = function(success, error) {
                    if (error) error({ code: 1, message: 'User denied Geolocation' });
                };
                navigator.geolocation.watchPosition = function() { return null; };
            """)

            # Navegar a la página con retry logic
            self._navigate_with_retry(driver, current_thread)
            
            # Hacer clic en el botón de acción
            self._click_action_button(driver, action_type, current_thread)
            
            # Ingresar RUT
            self._enter_rut(driver, rut, current_thread)
            
            # Enviar formulario
            self._submit_form(driver, current_thread)

            # Crear mensaje de éxito personalizado
            mensaje_final = (
                f"✅ {action_type} realizada con éxito a las {chile_time.strftime('%H:%M:%S')} (Chile - CLT).\n"
                f"📍 Geolocalización: Sin coordenadas\n"
                f"📍 Ubicación: Sin dirección\n\n"
            )
            if action_type == "ENTRADA":
                mensaje_final += "¡Que tengas un excelente día!"
            else:
                mensaje_final += "¡Que descanses y disfrutes tu tiempo libre!"
            return mensaje_final

        except TimeoutException as e:
            raise Exception(f"Timeout en navegador: {str(e)}")
        except WebDriverException as e:
            raise Exception(f"Error de WebDriver: {str(e)}")
        except Exception as e:
            raise Exception(f"Error inesperado en marcaje: {str(e)}")
        finally:
            if driver:
                try:
                    driver.quit()
                    print(f"🌐 [Hilo {current_thread.name}] Navegador cerrado")
                except Exception as e:
                    print(f"⚠️ [Hilo {current_thread.name}] Error cerrando navegador: {str(e)}")
    
    def _navigate_with_retry(self, driver, current_thread, max_retries: int = 3):
        """Navegar a la página con retry logic."""
        for attempt in range(max_retries):
            try:
                print(f"🌐 [Hilo {current_thread.name}] Cargando página de marcaje (intento {attempt + 1}/{max_retries})...")
                driver.get("https://app.ctrlit.cl/ctrl/dial/web/K1NBpBqyjf")
                driver.implicitly_wait(10)
                sleep(2)
                return
            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Falló carga de página después de {max_retries} intentos: {str(e)}")
                print(f"⚠️ [Hilo {current_thread.name}] Reintentando carga de página...")
                time.sleep(2)
    
    def _get_chrome_options(self) -> Options:
        """Obtener opciones de Chrome configuradas para enterprise."""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-geolocation")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")  # Optimización de performance
        
        prefs = {
            "profile.default_content_setting_values.geolocation": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.geolocation": 2,
            "profile.default_content_setting_values.notifications": 2
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
        print(f"🔍 [Hilo {current_thread.name}] RUT exacto a ingresar: '{rut}' (longitud: {len(rut)})")
        
        buttons = driver.find_elements(By.CSS_SELECTOR, "li.digits")
        available_buttons = [el.text.strip() for el in buttons]
        print(f"📱 [Hilo {current_thread.name}] Botones disponibles: {available_buttons}")

        # CORRECCIÓN: Tratar todos los caracteres de manera uniforme
        for i, char in enumerate(rut):
            print(f"🔤 [Hilo {current_thread.name}] Ingresando carácter {i+1}/{len(rut)}: '{char}'")
            found = False
            
            # Buscar el botón que corresponde al carácter actual
            for el in buttons:
                button_text = el.text.strip().upper()
                char_upper = char.upper()
                
                if button_text == char_upper:
                    print(f"✅ [Hilo {current_thread.name}] Encontrado botón '{button_text}' para carácter '{char}'")
                    el.click()
                    found = True
                    break
            
            if not found:
                print(f"❌ [Hilo {current_thread.name}] No se encontró botón para carácter: '{char}'")
                raise Exception(f"No se encontró el carácter: {char}")
            
            sleep(0.3)
        
        print(f"✅ [Hilo {current_thread.name}] RUT completo ingresado: {len(rut)} caracteres")
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
    
    def get_circuit_breaker_status(self) -> Dict:
        """Obtener estado del circuit breaker para monitoreo."""
        return self.circuit_breaker.get_state()
    
    def get_metrics_summary(self) -> Dict:
        """Obtener resumen de métricas."""
        return self.metrics_collector.get_summary()
