"""
Configuración central del sistema de marcaje automático.
"""
import os
import json
import logging
import base64
from typing import List


class Config:
    """Clase para manejar toda la configuración del sistema."""
    
    def __init__(self):
        self._load_environment_variables()
        self._process_ruts()
        self._validate_configuration()
    
    def _load_environment_variables(self):
        """Cargar variables de entorno."""
        self.clock_in_active = os.getenv('CLOCK_IN_ACTIVE')
        self.debug_mode = os.getenv('DEBUG_MODE')
        
        # Cargar email y password desde base64
        self.email_address_b64 = os.getenv('EMAIL_ADDRESS_B64')
        self.email_pass_b64 = os.getenv('EMAIL_PASS_B64')
        
        # Mantener compatibilidad con versiones legacy
        self.email_address = os.getenv('EMAIL_ADDRESS')
        self.email_pass = os.getenv('EMAIL_PASS')
        
        # Cargar valores base64 encoded para mayor seguridad
        self.ruts_env_b64 = os.getenv('ACTIVE_RUTS_B64')
        self.special_email_b64 = os.getenv('SPECIAL_EMAIL_TO')
        self.default_email_b64 = os.getenv('DEFAULT_EMAIL_TO')
        self.special_rut_b64 = os.getenv('SPECIAL_RUT_B64')

        # Mantener compatibilidad con versiones legacy (sin base64)
        self.ruts_env = os.getenv('ACTIVE_RUTS')
        
        # Procesar booleanos
        self.DEBUG_MODE = self.debug_mode.lower() == "true" if self.debug_mode else False
        self.CLOCK_IN_ACTIVE = self.clock_in_active.lower() == "true" if self.clock_in_active else False
    
    def _process_ruts(self):
        """Procesar RUTs activos desde base64."""
        self.ACTIVE_RUTS = []
        
        # Procesar RUTs activos (priorizar base64)
        ruts_source = self.ruts_env_b64 or self.ruts_env
        if ruts_source:
            try:
                # Intentar decodificar base64 primero
                if self.ruts_env_b64:
                    ruts_json = base64.b64decode(self.ruts_env_b64).decode('utf-8')
                    if self.DEBUG_MODE:
                        print(f"🔍 DEBUG - RUTs decodificados desde base64: {ruts_json}")
                else:
                    ruts_json = self.ruts_env
                    if self.DEBUG_MODE:
                        print(f"🔍 DEBUG - RUTs cargados directamente (sin base64): {ruts_json}")
                
                ruts_list = json.loads(ruts_json)
                # CORRECCIÓN: No agregar 'k' automáticamente - usar RUTs tal como están configurados
                self.ACTIVE_RUTS = [str(rut) for rut in ruts_list]
                print(f"✅ RUTs activos cargados: {len(self.ACTIVE_RUTS)} RUTs")
                logging.info(f"RUTs activos configurados: {[rut[:4] + '****' for rut in self.ACTIVE_RUTS]}")
            except (json.JSONDecodeError, Exception) as e:
                print(f"⚠️ Error al procesar ACTIVE_RUTS: {str(e)}")
                logging.error(f"Error al procesar ACTIVE_RUTS: {str(e)}")
                self._exit_with_error("No se puede continuar sin RUTs válidos")
        else:
            self._exit_with_error("CRITICAL: No se configuró el secreto ACTIVE_RUTS_B64 o ACTIVE_RUTS")
        
    
    def get_default_email(self) -> str:
        """Obtener el email por defecto decodificado desde base64."""
        if self.default_email_b64:
            try:
                return base64.b64decode(self.default_email_b64).decode('utf-8')
            except Exception as e:
                print(f"⚠️ Error decodificando email por defecto: {str(e)}")
                logging.error(f"Error decodificando email por defecto: {str(e)}")
                return None
        return None
    
    def get_special_rut(self) -> str:
        """Obtener el RUT especial decodificado desde base64."""
        if self.special_rut_b64:
            try:
                return base64.b64decode(self.special_rut_b64).decode('utf-8')
            except Exception as e:
                print(f"⚠️ Error decodificando RUT especial: {str(e)}")
                logging.error(f"Error decodificando RUT especial: {str(e)}")
                return None
        return None

    def get_special_email(self) -> str:
        """Obtener el email especial decodificado desde base64."""
        if self.special_email_b64:
            try:
                return base64.b64decode(self.special_email_b64).decode('utf-8')
            except Exception as e:
                print(f"⚠️ Error decodificando email especial: {str(e)}")
                logging.error(f"Error decodificando email especial: {str(e)}")
                return None
        return None
    
    def _validate_configuration(self):
        """Validar que la configuración es correcta."""
        if not self.ACTIVE_RUTS:
            self._exit_with_error("CRITICAL: No hay RUTs activos para procesar")
    
    def _exit_with_error(self, message: str):
        """Salir del programa con un mensaje de error."""
        print(f"❌ {message}")
        logging.error(f"Script terminado: {message}")
        exit(1)
    
    def print_debug_info(self):
        """Imprimir información de debug."""
        print(f"🔍 DEBUG - Variable debug_mode cargada: '{self.debug_mode}'")
        print(f"🔍 DEBUG - Variable DEBUG_MODE calculada: {self.DEBUG_MODE}")
        print(f"🔍 DEBUG - Variable clock_in_active cargada: '{self.clock_in_active}'")
        print(f"🔍 DEBUG - Variable CLOCK_IN_ACTIVE calculada: {self.CLOCK_IN_ACTIVE}")
        print(f"🔍 DEBUG - RUTs activos: {[rut[:4] + '****' for rut in self.ACTIVE_RUTS]}")
    
    def get_email_destinations(self, rut: str) -> list:
        """Determinar emails de destino basado en el RUT.
        
        Lógica:
        - Email principal siempre recibe todas las notificaciones
        - Email especial solo recibe notificaciones de su propio RUT
        - Cuando es el RUT especial, ambos reciben el email
        """
        emails = []
        
        try:
            # Obtener el RUT especial desde la configuración
            special_rut = self.get_special_rut()
            
            # Comparar sin el dígito verificador 'k' y en minúsculas
            rut_clean = rut.lower().rstrip('k')
            special_email = self.get_special_email()
            
            # Email principal siempre recibe todas las notificaciones
            main_email = self.get_email_address()
            emails.append(main_email)
            
            # Si es el RUT especial, también enviar al email especial
            if special_rut:
                special_rut_clean = special_rut.lower().rstrip('k')
                if rut_clean == special_rut_clean and special_email:
                    emails.append(special_email)
                
            return emails
            
        except Exception as e:
            logging.error(f"Error determinando emails para RUT {rut[:4]}****: {str(e)}")
            return [self.get_email_address()]  # Fallback al email principal
    
    def get_email_address(self) -> str:
        """Obtener el email address decodificado desde base64."""
        if self.email_address_b64:
            try:
                return base64.b64decode(self.email_address_b64).decode('utf-8')
            except Exception as e:
                print(f"⚠️ Error decodificando email address: {str(e)}")
                logging.error(f"Error decodificando email address: {str(e)}")
        return self.email_address or "debug@test.com"
    
    def get_email_pass(self) -> str:
        """Obtener el email password decodificado desde base64."""
        if self.email_pass_b64:
            try:
                return base64.b64decode(self.email_pass_b64).decode('utf-8')
            except Exception as e:
                print(f"⚠️ Error decodificando email password: {str(e)}")
                logging.error(f"Error decodificando email password: {str(e)}")
        return self.email_pass or "debug_password"
    
    def get_holiday_emails(self) -> list:
        """Obtener emails para notificaciones de feriados (ambos destinatarios)."""
        emails = []
        
        # Siempre agregar el email principal
        main_email = self.get_email_address()
        emails.append(main_email)
        
        # Agregar email especial si existe
        special_email = self.get_special_email()
        if special_email:
            emails.append(special_email)
        
        return emails


# Configuración de correo
class EmailConfig:
    """Configuración específica para el correo."""
    
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587


# Feriados de Chile 2025
CHILE_HOLIDAYS_2025 = [
    {"date": "2025-01-01", "title": "Año Nuevo", "type": "Civil"},
    {"date": "2025-04-18", "title": "Viernes Santo", "type": "Religioso"},
    {"date": "2025-04-19", "title": "Sábado Santo", "type": "Religioso"},
    {"date": "2025-05-01", "title": "Día Nacional del Trabajo", "type": "Civil"},
    {"date": "2025-05-21", "title": "Día de las Glorias Navales", "type": "Civil"},
    {"date": "2025-06-29", "title": "San Pedro y San Pablo", "type": "Religioso"},
    {"date": "2025-07-16", "title": "Día de la Virgen del Carmen", "type": "Religioso"},
    {"date": "2025-08-15", "title": "Asunción de la Virgen", "type": "Religioso"},
    {"date": "2025-09-18", "title": "Independencia Nacional", "type": "Civil"},
    {"date": "2025-09-19", "title": "Día de las Glorias del Ejército", "type": "Civil"},
    {"date": "2025-12-08", "title": "Inmaculada Concepción", "type": "Religioso"},
    {"date": "2025-12-25", "title": "Navidad", "type": "Religioso"}
]
