"""
Servicio de verificación de feriados en Chile.
"""
import requests
import logging
from datetime import date
from typing import Dict, Optional, Any

from config import CHILE_HOLIDAYS_2025
from .email_service import EmailService


class HolidayService:
    """Servicio para verificar feriados en Chile."""
    
    def __init__(self, email_service: EmailService, active_ruts_count: int, active_ruts_masked: list):
        self.email_service = email_service
        self.active_ruts_count = active_ruts_count
        self.active_ruts_masked = active_ruts_masked
    
    def is_holiday(self) -> bool:
        """Verificar si hoy es feriado."""
        print("🎄 Verificando si hoy es feriado...")
        
        # Intentar primero con la API online
        holiday = self._check_online_api()
        if holiday:
            print(f"🎉 ¡Hoy es feriado!: {holiday['title']} ({holiday['type']})")
            self.email_service.send_holiday_email(holiday, "API", self.active_ruts_count, self.active_ruts_masked)
            return True
        
        # Si falla la API, usar lista local
        holiday = self._check_local_holidays()
        if holiday:
            print(f"🎉 ¡Hoy es feriado! (lista local): {holiday['title']} ({holiday['type']})")
            self.email_service.send_holiday_email(holiday, "LOCAL", self.active_ruts_count, self.active_ruts_masked)
            return True
        
        print("✅ No es feriado, continuando con el marcaje")
        return False
    
    def _check_online_api(self) -> Optional[Dict[str, Any]]:
        """Verificar feriados usando API online."""
        try:
            print("🌐 Consultando API de feriados online...")
            headers = {'accept': 'application/json'}
            response = requests.get(
                'https://api.boostr.cl/holidays.json', 
                headers=headers, 
                timeout=5
            )

            if response.status_code == 200:
                print("✅ API de feriados respondió correctamente")
                result = response.json()
                if result['status'] == 'success':
                    holidays = result['data']
                    today = date.today().strftime("%Y-%m-%d")
                    print(f"📅 Verificando fecha: {today}")

                    holiday = next(
                        (h for h in holidays if h['date'] == today), None
                    )
                    if holiday:
                        return holiday
                    else:
                        print("📅 No es feriado según API online")
                        return None
                else:
                    raise Exception(f"API retornó estado no exitoso: {result['status']}")
            else:
                raise Exception(f"API retornó status code: {response.status_code}")

        except Exception as e:
            print(f"⚠️ API de feriados no disponible: {str(e)}")
            return None
    
    def _check_local_holidays(self) -> Optional[Dict[str, Any]]:
        """Verificar feriados usando lista local."""
        print("📋 Verificando con lista local de feriados...")
        today = date.today().strftime("%Y-%m-%d")
        
        holiday = next(
            (h for h in CHILE_HOLIDAYS_2025 if h['date'] == today), None
        )
        
        return holiday
