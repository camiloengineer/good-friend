"""
Servicio de notificaciones por correo electrónico.
"""
import smtplib
import logging
from datetime import datetime
from email.message import EmailMessage
from typing import Dict, Any

from config import EmailConfig


class EmailService:
    """Servicio para envío de correos electrónicos."""
    
    def __init__(self, email_from: str, email_pass: str, config=None, debug_mode: bool = False):
        self.email_from = email_from
        self.email_pass = email_pass
        self.config = config
        self.debug_mode = debug_mode  # Nuevo parámetro para modo DEBUG
        self.smtp_server = EmailConfig.SMTP_SERVER
        self.smtp_port = EmailConfig.SMTP_PORT
    
    def send_email(self, subject: str, content: str, email_to: str = None, rut: str = None) -> bool:
        """Enviar un correo electrónico al destinatario especificado o determinado por RUT."""
        try:
            # Determinar destinatarios
            if self.debug_mode:
                # En modo DEBUG: SOLO enviar al email principal
                email_destinations = [self.config.get_email_address() if self.config else self.email_from]
                print(f"🧪 DEBUG: Email será enviado SOLO a: {email_destinations[0]}")
            elif rut and self.config:
                # Modo PRODUCCIÓN: Usar la lógica de múltiples destinatarios basada en RUT
                email_destinations = self.config.get_email_destinations(rut)
            elif email_to:
                # Usar el destinatario especificado
                email_destinations = [email_to]
            else:
                # Fallback al email principal
                email_destinations = [self.config.get_email_address() if self.config else self.email_from]
            
            # Enviar a todos los destinatarios
            success_count = 0
            for destination in email_destinations:
                try:
                    email = EmailMessage()
                    email["From"] = self.email_from
                    email["To"] = destination
                    email["Subject"] = subject
                    email.set_content(content)

                    with smtplib.SMTP(self.smtp_server, self.smtp_port) as smtp:
                        smtp.starttls()
                        smtp.login(self.email_from, self.email_pass)
                        smtp.send_message(email)
                    
                    # Log mejorado con información del RUT
                    rut_info = f" para RUT {rut[:4]}****" if rut else ""
                    logging.info(f"Correo enviado exitosamente a {destination}{rut_info}")
                    success_count += 1
                except Exception as e:
                    logging.error(f"No se pudo enviar correo a {destination}: {str(e)}")
            
            return success_count > 0  # Retorna True si al menos un email fue enviado
        except Exception as e:
            logging.error(f"Error general enviando correos: {str(e)}")
            return False
    
    def send_holiday_email(self, holiday: Dict[str, str], source: str, active_ruts_count: int, active_ruts_masked: list) -> bool:
        """Enviar correo de notificación de feriado a todos los destinatarios."""
        subject = f"🎉 Feriado: {holiday['title']} - No hay marcaje"
        content = f"""Hoy es feriado ({holiday['title']}), no se realizará marcaje.
Tipo: {holiday['type']}
Fuente: {'API en línea' if source == 'API' else 'Lista local (API no disponible)'}
RUTs configurados: {active_ruts_count} RUTs - {active_ruts_masked}"""
        
        # En modo DEBUG: solo al email principal. En producción: a todos
        if self.debug_mode:
            email_destinations = [self.config.get_email_address() if self.config else self.email_from]
            print(f"🧪 DEBUG: Email de feriado será enviado SOLO a: {email_destinations[0]}")
        elif self.config:
            email_destinations = self.config.get_holiday_emails()
        else:
            email_destinations = [self.email_from]
        
        success_count = 0
        for email_to in email_destinations:
            if self.send_email(subject, content, email_to=email_to):
                success_count += 1
        
        success = success_count > 0
        if success:
            logging.info(f"Correo de feriado enviado a {success_count} destinatarios (fuente: {source})")
        return success
    
    def send_exception_email(self, rut_masked: str, rut: str = None) -> bool:
        """Enviar correo de notificación de RUT en excepciones."""
        subject = f"🚫 RUT en Lista de Excepciones - {rut_masked}"
        content = f"""El RUT {rut_masked} está configurado en la lista de excepciones y no se procesará.

Motivo: RUT incluido en EXCEPTIONS_RUTS
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Para procesar este RUT, debe ser removido de la lista de excepciones en GitHub Secrets."""
        
        # Usar la lógica de múltiples destinatarios si se proporciona el RUT
        success = self.send_email(subject, content, rut=rut)
        if success:
            logging.info(f"Correo de excepción enviado para RUT {rut_masked}")
            print(f"📧 Correo de excepción enviado para RUT {rut_masked}")
        else:
            print(f"❌ Error enviando correo de excepción: RUT {rut_masked}")
        return success
    
    def send_success_email(self, rut_masked: str, action_type: str, message: str, is_debug: bool = False, rut: str = None) -> bool:
        """Enviar correo de confirmación de marcaje exitoso."""
        subject = f"{action_type} {'(simulada)' if is_debug else ''} completada - RUT: {rut_masked}"
        # Usar la lógica de múltiples destinatarios si se proporciona el RUT
        success = self.send_email(subject, message, rut=rut)
        if success:
            print(f"✅ Correo de confirmación enviado exitosamente")
        return success
    
    def send_error_email(self, rut_masked: str, action_type: str, error_message: str, rut: str = None) -> bool:
        """Enviar correo de error en marcaje."""
        subject = f"Error en {action_type} - RUT: {rut_masked}"
        # Usar la lógica de múltiples destinatarios si se proporciona el RUT
        success = self.send_email(subject, error_message, rut=rut)
        if success:
            print(f"✅ Correo de error enviado")
        else:
            print(f"❌ No se pudo enviar correo de error")
        return success
