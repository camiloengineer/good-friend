"""
Gestor de delays aleatorios para evitar detección automatizada.
"""
import random
import logging
from typing import Dict


class DelayManager:
    """Gestor de delays aleatorios para RUTs."""
    
    def __init__(self):
        self.delay_registry: Dict[str, int] = {}
        self.delay_coincidences = 0
    
    def get_random_delay(self, rut: str) -> int:
        """Generar un delay aleatorio entre 1 y 20 minutos y evitar coincidencias."""
        max_attempts = 10
        attempts = 0

        while attempts < max_attempts:
            delay_minutes = random.randint(1, 20)

            # Si es el primer RUT o no hay coincidencia, aceptamos el delay
            if len(self.delay_registry) == 0 or delay_minutes not in self.delay_registry.values():
                break

            # Si hay coincidencia, incrementamos el contador e intentamos de nuevo
            attempts += 1
            logging.debug(
                f"Coincidencia detectada con delay de {delay_minutes} minutos. "
                f"Reintentando... ({attempts}/{max_attempts})"
            )

        # Si después de varios intentos seguimos con coincidencia, aceptamos pero avisamos
        if attempts == max_attempts:
            self.delay_coincidences += 1
            rut_masked = f"{rut[:4]}****"
            logging.warning(
                f"⚠️ No se pudo evitar coincidencia después de {max_attempts} intentos para RUT {rut_masked}"
            )
            print(
                f"⚠️ No se pudo evitar coincidencia después de {max_attempts} intentos. "
                f"Se usará delay de {delay_minutes} minutos."
            )

        # Registrar el delay final para este RUT
        self.delay_registry[rut] = delay_minutes

        # Log normal
        rut_masked = f"{rut[:4]}****"
        logging.info(f"Delay aleatorio generado para RUT {rut_masked}: {delay_minutes} minutos")
        return delay_minutes
    
    def get_statistics(self) -> Dict[str, int]:
        """Obtener estadísticas de delays."""
        return {
            "total_ruts": len(self.delay_registry),
            "coincidences": self.delay_coincidences,
            "delays": dict(self.delay_registry)
        }
