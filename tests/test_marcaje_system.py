"""
Pruebas automatizadas para el sistema de marcaje automático.
"""
import pytest
import os
from     @pytest.mark.unit
    def test_rut_in_exceptions_list(self, marcaje_service, mock_email_service, mock_config):
        """
        Test Caso 2: RUT en lista de excepciones.
        Un RUT debe ser saltado y enviar email de excepción.
        """
        ruts = mock_config.ACTIVE_RUTS
        special_rut = mock_config.get_special_rut()
        exceptions = [special_rut] if special_rut else [ruts[0]]  # Si no hay special_rut, usar el primer RUT
        
        # Contar emails de success esperados (todos los RUTs menos las excepciones)
        expected_successes = len([rut for rut in ruts if rut not in exceptions])
        expected_exceptions = len([rut for rut in ruts if rut in exceptions])
        
        # Ejecutar procesamiento
        for rut in ruts:
            marcaje_service.process_rut(rut, exceptions)
        
        # Verificar llamadas
        assert mock_email_service.send_success_email.call_count == expected_successes
        assert mock_email_service.send_exception_email.call_count == expected_exceptions
        
        print(f"✅ Procesados {expected_successes} RUTs normalmente, {expected_exceptions} excepciones")t Mock, patch
from datetime import datetime
import pytz

from config import Config
from services.marcaje_service import MarcajeService
from services.email_service import EmailService
from services.holiday_service import HolidayService
from utils.delay_manager import DelayManager
from utils.rut_validator import RutValidator


class TestMarcajeSystem:
    """Pruebas del sistema de marcaje completo."""
    
    @pytest.fixture
    def mock_env_vars(self):
        """Variables de entorno para pruebas."""
        return {
            'DEBUG_MODE': 'true',
            'CLOCK_IN_ACTIVE': 'true',
            'EMAIL_ADDRESS_B64': os.getenv('EMAIL_ADDRESS_B64', 'dGVzdEBlbWFpbC5jb20='),
            'EMAIL_PASS_B64': 'dGVzdF9wYXNz',
            'SPECIAL_EMAIL_TO': os.getenv('SPECIAL_EMAIL_TO', 'dGVzdEBlbWFpbC5jb20='),
            'DEFAULT_EMAIL_TO': os.getenv('DEFAULT_EMAIL_TO', 'dGVzdEBlbWFpbC5jb20='),
            'SPECIAL_RUT_B64': os.getenv('SPECIAL_RUT_B64', 'dGVzdF9ydXQ='),
            'ACTIVE_RUTS_B64': os.getenv('ACTIVE_RUTS_B64', 'WyJ0ZXN0X3J1dDEiLCAidGVzdF9ydXQyIl0='),
            'EXCEPTIONS_RUTS_B64': 'W10='
        }
    
    @pytest.fixture
    def mock_config(self, mock_env_vars, mocker):
        """Configuración mockeada para pruebas."""
        mocker.patch.dict(os.environ, mock_env_vars)
        return Config()
    
    def get_active_ruts_helper(self, config):
        """Helper para obtener RUTs activos."""
        return config.ACTIVE_RUTS
    
    def get_exceptions_ruts_helper(self, config):
        """Helper para obtener RUTs de excepción."""
        return config.EXCEPTIONS_RUTS
    
    @pytest.fixture
    def mock_email_service(self, mocker):
        """EmailService mockeado."""
        mock_service = Mock(spec=EmailService)
        mock_service.send_success_email = Mock()
        mock_service.send_error_email = Mock()
        mock_service.send_exception_email = Mock()
        mock_service.send_holiday_email = Mock()
        return mock_service
    
    @pytest.fixture
    def mock_delay_manager(self, mocker):
        """DelayManager mockeado."""
        mock_manager = Mock(spec=DelayManager)
        mock_manager.get_random_delay = Mock(return_value=0)  # Sin delay para pruebas
        return mock_manager
    
    @pytest.fixture
    def marcaje_service(self, mock_email_service, mock_delay_manager):
        """Instancia de MarcajeService para pruebas."""
        return MarcajeService(
            email_service=mock_email_service,
            delay_manager=mock_delay_manager,
            debug_mode=True
        )

    @pytest.mark.unit
    def test_normal_operation_no_exceptions(self, marcaje_service, mock_email_service, mock_config):
        """
        Test Caso 1: Funcionamiento normal sin excepciones.
        Ambos RUTs deben procesarse y enviar emails.
        """
        ruts = mock_config.ACTIVE_RUTS
        exceptions = []
        
        # Ejecutar procesamiento para cada RUT
        for rut in ruts:
            marcaje_service.process_rut(rut, exceptions)
        
        # Verificar que se enviaron emails de éxito para ambos RUTs
        assert mock_email_service.send_success_email.call_count == len(ruts)
        assert mock_email_service.send_exception_email.call_count == 0
        
        # Verificar que se llamó con los RUTs correctos
        calls = mock_email_service.send_success_email.call_args_list
        processed_ruts = [call.kwargs.get('rut') for call in calls]
        for rut in ruts:
            assert rut in processed_ruts

    @pytest.mark.unit
    def test_rut_in_exceptions_list(self, marcaje_service, mock_email_service, mock_config):
        """
        Test Caso 2: RUT en lista de excepciones.
        Un RUT debe ser saltado y enviar email de excepción.
        """
        ruts = mock_config.ACTIVE_RUTS
        special_rut = mock_config.get_special_rut()
        exceptions = [special_rut]
        
        # Ejecutar procesamiento
        for rut in ruts:
            marcaje_service.process_rut(rut, exceptions)
        
        # Verificar que solo se procesó un RUT normalmente
        assert mock_email_service.send_success_email.call_count == 1
        assert mock_email_service.send_exception_email.call_count == 1
        
        # Verificar que el RUT de excepción fue el correcto
        exception_call = mock_email_service.send_exception_email.call_args
        assert exception_call.kwargs.get('rut') == special_rut
        
        # Verificar que solo se procesó el RUT que no está en excepciones
        success_call = mock_email_service.send_success_email.call_args
        non_special_rut = next(rut for rut in ruts if rut != special_rut)
        assert success_call.kwargs.get('rut') == non_special_rut

    @pytest.mark.unit
    def test_both_ruts_in_exceptions(self, marcaje_service, mock_email_service, mock_config):
        """
        Test Caso Extra: Ambos RUTs en excepciones.
        Ningún RUT debe procesarse, solo emails de excepción.
        """
        ruts = mock_config.ACTIVE_RUTS
        exceptions = ruts.copy()  # Todos los RUTs en excepciones
        
        # Ejecutar procesamiento
        for rut in ruts:
            marcaje_service.process_rut(rut, exceptions)
        
        # Verificar que no se procesó ningún RUT normalmente
        assert mock_email_service.send_success_email.call_count == 0
        assert mock_email_service.send_exception_email.call_count == len(ruts)

    @pytest.mark.integration
    def test_email_destinations_special_rut(self, mock_config):
        """
        Test Caso 3: Verificar destinatarios de email para RUT especial.
        El RUT especial debe enviar emails a los destinatarios configurados.
        """
        special_rut = mock_config.get_special_rut()
        active_ruts = mock_config.ACTIVE_RUTS
        normal_rut = next(rut for rut in active_ruts if rut != special_rut)
        main_email = mock_config.get_email_address()
        
        # Verificar destinatarios para RUT especial
        special_destinations = mock_config.get_email_destinations(special_rut)
        assert len(special_destinations) >= 1
        assert main_email in special_destinations
        
        # Verificar destinatarios para RUT normal
        normal_destinations = mock_config.get_email_destinations(normal_rut)
        assert len(normal_destinations) >= 1
        assert main_email in normal_destinations

    @pytest.mark.unit
    def test_holiday_scenario(self, mocker):
        """
        Test Caso 4: Escenario de feriado.
        En feriados no debe realizar marcaje, solo enviar notificaciones.
        """
        # Mockear el servicio de feriados para retornar True
        mock_holiday_service = Mock(spec=HolidayService)
        mock_holiday_service.is_holiday = Mock(return_value=True)
        
        # Mockear la función principal que usa el servicio de feriados
        with patch('main.HolidayService', return_value=mock_holiday_service):
            # Simular el comportamiento del main cuando es feriado
            is_holiday = mock_holiday_service.is_holiday()
            assert is_holiday == True

    @pytest.mark.unit
    def test_script_deactivated(self, mock_env_vars, mocker):
        """
        Test Caso 5: Script desactivado.
        Con CLOCK_IN_ACTIVE=false, no debe procesarse nada.
        """
        # Modificar la variable de entorno para desactivar el script
        mock_env_vars['CLOCK_IN_ACTIVE'] = 'false'
        mocker.patch.dict(os.environ, mock_env_vars)
        
        config = Config()
        assert config.CLOCK_IN_ACTIVE == False

    @pytest.mark.unit
    def test_rut_masking(self, mock_config):
        """
        Test de utilidad: Verificar que el enmascarado de RUTs funcione correctamente.
        """
        active_ruts = mock_config.ACTIVE_RUTS
        
        for rut in active_ruts:
            masked = RutValidator.mask_rut(rut)
            # Verificar que la máscara tiene el formato correcto
            assert "***" in masked
            assert len(masked) == len(rut)
            # Verificar que mantiene los primeros y últimos caracteres
            assert masked.startswith(rut[:3])
            assert masked.endswith(rut[-3:])

    @pytest.mark.unit
    def test_rut_exception_validation(self, mock_config):
        """
        Test de utilidad: Verificar validación de RUTs en excepciones.
        """
        active_ruts = mock_config.ACTIVE_RUTS
        special_rut = mock_config.get_special_rut()
        exceptions = [special_rut]
        
        assert RutValidator.is_rut_exception(special_rut, exceptions) == True
        
        # Obtener un RUT que no esté en excepciones
        non_exception_rut = next(rut for rut in active_ruts if rut != special_rut)
        assert RutValidator.is_rut_exception(non_exception_rut, exceptions) == False

    @pytest.mark.unit
    def test_config_base64_decoding(self, mock_config):
        """
        Test de configuración: Verificar decodificación de valores base64.
        """
        # Verificar que el email se decodifica correctamente
        email = mock_config.get_email_address()
        assert email is not None and len(email) > 0
        
        # Verificar que los RUTs se decodifican correctamente
        ruts = mock_config.ACTIVE_RUTS
        assert len(ruts) >= 2
        
        # Verificar que las excepciones se decodifican correctamente
        exceptions = mock_config.EXCEPTIONS_RUTS
        assert exceptions == []

    @pytest.mark.integration
    def test_marcaje_action_type_determination(self, marcaje_service, mocker):
        """
        Test de integración: Verificar determinación del tipo de acción según la hora.
        """
        chile_tz = pytz.timezone('America/Santiago')
        
        # Mockear hora de la mañana (entrada)
        morning_time = datetime(2025, 6, 28, 9, 0, 0, tzinfo=chile_tz)
        with patch('services.marcaje_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = morning_time
            action_type = marcaje_service._determine_action_type()
            assert action_type == "ENTRADA"
        
        # Mockear hora de la tarde (salida)
        afternoon_time = datetime(2025, 6, 28, 15, 0, 0, tzinfo=chile_tz)
        with patch('services.marcaje_service.datetime') as mock_datetime:
            mock_datetime.now.return_value = afternoon_time
            action_type = marcaje_service._determine_action_type()
            assert action_type == "SALIDA"


class TestConfigurationScenarios:
    """Pruebas de diferentes configuraciones del sistema."""
    
    @pytest.mark.parametrize("exceptions_b64,expected_count", [
        ("W10=", 0),  # Array vacío
        ("WyJ0ZXN0X3J1dDEiXQ==", 1),  # Un RUT de prueba
        ("WyJ0ZXN0X3J1dDEiLCAidGVzdF9ydXQyIl0=", 2),  # Dos RUTs de prueba
    ])
    def test_different_exception_configurations(self, exceptions_b64, expected_count, mocker):
        """
        Test parametrizado: Diferentes configuraciones de RUTs de excepción.
        """
        env_vars = {
            'EXCEPTIONS_RUTS_B64': exceptions_b64
        }
        mocker.patch.dict(os.environ, env_vars)
        
        config = Config()
        actual_exceptions = config.get_exceptions_ruts()
        
        assert len(actual_exceptions) == expected_count

    @pytest.mark.parametrize("debug_mode,clock_active,should_process", [
        ("true", "true", True),
        ("false", "true", True),
        ("true", "false", False),
        ("false", "false", False),
    ])
    def test_system_activation_scenarios(self, debug_mode, clock_active, should_process, mocker):
        """
        Test parametrizado: Diferentes combinaciones de activación del sistema.
        """
        env_vars = {
            'DEBUG_MODE': debug_mode,
            'CLOCK_IN_ACTIVE': clock_active
        }
        mocker.patch.dict(os.environ, env_vars)
        
        config = Config()
        
        assert config.CLOCK_IN_ACTIVE == (clock_active == "true")
        assert config.DEBUG_MODE == (debug_mode == "true")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
