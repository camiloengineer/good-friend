"""
Servicio de validación de RUTs.
"""
from typing import List


class RutValidator:
    """Validador para RUTs chilenos."""
    
    @staticmethod
    def is_valid_rut(rut: str) -> bool:
        """Validar que el RUT tenga formato chileno válido (sin puntos ni guiones)."""
        try:
            rut = rut.lower()

            # Verificar longitud (7-8 dígitos + dígito verificador)
            if not (8 <= len(rut) <= 9):
                return False

            # Verificar que termina en número o 'k'
            if not rut[-1].isdigit() and rut[-1] != 'k':
                return False

            # Verificar que el resto son números
            if not rut[:-1].isdigit():
                return False

            return True
        except:
            return False
    
    @staticmethod
    def is_rut_exception(rut: str, exceptions_list: List[str]) -> bool:
        """Verificar si un RUT está en la lista de excepciones."""
        return rut.lower() in [exception_rut.lower() for exception_rut in exceptions_list]
    
    @staticmethod
    def mask_rut(rut: str) -> str:
        """Enmascarar RUT para logging (mostrar solo primeros 4 dígitos, preservar longitud)."""
        if len(rut) <= 4:
            return "*" * len(rut)
        return f"{rut[:4]}{'*' * (len(rut) - 4)}"
