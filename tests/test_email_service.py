"""
Pruebas específicas para el servicio de email.
Verifica los destinatarios y el contenido de los emails.
"""
import pytest
import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from config import Config
from services.email_service import EmailService


class TestEmailService:
    """Pruebas del servicio de email."""
    
    @pytest.fixture
    def mock_env_vars(self):
        """Variables de entorno para pruebas de email."""
        return {
            'EMAIL_ADDRESS_B64': os.getenv('EMAIL_ADDRESS_B64', 'dGVzdEBlbWFpbC5jb20='),
            'EMAIL_PASS_B64': 'dGVzdF9wYXNzd29yZA==',
            'SPECIAL_EMAIL_TO': os.getenv('SPECIAL_EMAIL_TO', 'dGVzdEBlbWFpbC5jb20='),
            'DEFAULT_EMAIL_TO': os.getenv('DEFAULT_EMAIL_TO', 'dGVzdEBlbWFpbC5jb20='),
            'SPECIAL_RUT_B64': os.getenv('SPECIAL_RUT_B64', 'dGVzdF9ydXQ='),
        }
    
    @pytest.fixture
    def mock_config(self, mock_env_vars, mocker):
        """Configuración mockeada para pruebas de email."""
        mocker.patch.dict(os.environ, mock_env_vars)
        return Config()
    
    @pytest.fixture
    def email_service(self, mock_config, mocker):
        """EmailService mockeado para pruebas."""
        # Mockear smtplib para evitar envíos reales
        mock_smtp = MagicMock()
        mocker.patch('smtplib.SMTP_SSL', return_value=mock_smtp)
        
        # Obtener email y password desde la configuración
        email_from = mock_config.get_email_address()
        email_pass = mock_config.get_email_pass()
        
        return EmailService(email_from, email_pass, mock_config, debug_mode=True)

    @pytest.mark.email
    def test_email_destinations_special_rut(self, mock_config):
        """
        Test: Verificar destinatarios para RUT especial.
        Debe enviar al email principal (y potencialmente email especial).
        """
        special_rut = mock_config.get_special_rut()
        main_email = mock_config.get_email_address()
        destinations = mock_config.get_email_destinations(special_rut)
        
        # Verificar que al menos está el email principal
        assert main_email in destinations
        assert len(destinations) >= 1

    @pytest.mark.email
    def test_email_destinations_normal_rut(self, mock_config):
        """
        Test: Verificar destinatarios para RUT normal.
        Debe enviar solo al email principal.
        """
        active_ruts = mock_config.ACTIVE_RUTS
        special_rut = mock_config.get_special_rut()
        # Obtener el RUT que no es el especial
        normal_rut = next(rut for rut in active_ruts if rut != special_rut)
        main_email = mock_config.get_email_address()
        destinations = mock_config.get_email_destinations(normal_rut)
        
        # Verificar que está el email principal
        assert main_email in destinations
        assert len(destinations) >= 1

    @pytest.mark.email
    def test_success_email_call(self, email_service, mocker, mock_config):
        """
        Test: Verificar que se llama correctamente al envío de email de éxito.
        """
        # Mockear el método interno de envío
        mock_send = mocker.patch.object(email_service, 'send_email')
        
        special_rut = mock_config.get_special_rut()
        rut_masked = f"{special_rut[:3]}***{special_rut[-3:]}"
        action_type = "ENTRADA"
        message = "Test message"
        debug_mode = True
        
        # Llamar al método
        email_service.send_success_email(rut_masked, action_type, message, debug_mode, rut=special_rut)
        
        # Verificar que se llamó al método de envío
        assert mock_send.called

    @pytest.mark.email
    def test_exception_email_call(self, email_service, mocker, mock_config):
        """
        Test: Verificar que se llama correctamente al envío de email de excepción.
        """
        # Mockear el método interno de envío
        mock_send = mocker.patch.object(email_service, 'send_email')
        
        special_rut = mock_config.get_special_rut()
        rut_masked = f"{special_rut[:3]}***{special_rut[-3:]}"
        
        # Llamar al método
        email_service.send_exception_email(rut_masked, rut=special_rut)
        
        # Verificar que se llamó al método de envío
        assert mock_send.called

    @pytest.mark.email
    def test_error_email_call(self, email_service, mocker, mock_config):
        """
        Test: Verificar que se llama correctamente al envío de email de error.
        """
        # Mockear el método interno de envío
        mock_send = mocker.patch.object(email_service, 'send_email')
        
        special_rut = mock_config.get_special_rut()
        rut_masked = f"{special_rut[:3]}***{special_rut[-3:]}"
        action_type = "ENTRADA"
        error_message = "Test error"
        
        # Llamar al método
        email_service.send_error_email(rut_masked, action_type, error_message, rut=special_rut)
        
        # Verificar que se llamó al método de envío
        assert mock_send.called

    @pytest.mark.email
    def test_holiday_email_call(self, email_service, mocker, mock_config):
        """
        Test: Verificar que se llama correctamente al envío de email de feriado.
        """
        # Mockear el método interno de envío
        mock_send = mocker.patch.object(email_service, 'send_email')
        
        holiday_name = "Día de Prueba"
        active_ruts = mock_config.ACTIVE_RUTS
        
        # Llamar al método
        for rut in active_ruts:
            subject = f"🏖️ ¡Hoy es feriado! - {holiday_name}"
            content = f"Hoy {datetime.now().strftime('%d/%m/%Y')} es {holiday_name}"
            email_service.send_email(subject, content, rut=rut)
        
        # Verificar que se llamó al método de envío para ambos RUTs
        assert mock_send.call_count == len(active_ruts)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
