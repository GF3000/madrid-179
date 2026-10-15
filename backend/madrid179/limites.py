"""Límite de llamadas al LLM: protege el saldo de DeepSeek ahora que la app está en una URL pública.

Solo cuentan las llamadas que llegan de verdad al LLM (las explicaciones servidas desde la caché no gastan).
Dos límites, con ventanas deslizantes en memoria:
  - por cliente (IP): reparte el uso entre visitantes. La IP sale de X-Forwarded-For, que el cliente puede
    falsear, así que este límite es de buena fe;
  - global: el que de verdad acota el gasto, porque no depende de nada que mande el cliente.
Las cuentas son por proceso: con varias instancias de Cloud Run (máximo 3, deploy.yml) el techo real es
el triple. Se configuran con variables de entorno; 0 desactiva ese límite.
"""
import os
import threading
import time
from collections import defaultdict, deque

HORA, DIA = 3600, 86400


class LimiteSuperado(RuntimeError):
    def __init__(self, mensaje, reintentar_s):
        super().__init__(mensaje)
        self.reintentar_s = max(1, int(reintentar_s) + 1)


class Limitador:
    def __init__(self, por_cliente_hora=40, global_hora=300, global_dia=1500, reloj=time.monotonic):
        self.por_cliente_hora, self.global_hora, self.global_dia = por_cliente_hora, global_hora, global_dia
        self._reloj = reloj
        self._clientes = defaultdict(deque)  # cliente -> instantes de su última hora
        self._global = deque()  # instantes de las últimas 24 h
        self._cerrojo = threading.Lock()  # FastAPI ejecuta los endpoints síncronos en varios hilos

    @classmethod
    def desde_entorno(cls):
        leer = lambda nombre, defecto: int(os.environ.get(nombre, defecto))
        return cls(leer("MADRID179_LLM_POR_IP_HORA", 40), leer("MADRID179_LLM_GLOBAL_HORA", 300),
                   leer("MADRID179_LLM_GLOBAL_DIA", 1500))

    def consumir(self, cliente):
        """Anota una llamada al LLM o lanza LimiteSuperado (con los segundos que faltan para poder reintentar)."""
        ahora = self._reloj()
        with self._cerrojo:
            while self._global and self._global[0] <= ahora - DIA:
                self._global.popleft()
            propias = self._clientes[cliente or "desconocido"]
            while propias and propias[0] <= ahora - HORA:
                propias.popleft()
            ultima_hora = [t for t in self._global if t > ahora - HORA]

            if self.global_dia and len(self._global) >= self.global_dia:
                raise LimiteSuperado("El asistente ha llegado a su límite diario de uso. Vuelve a probar más tarde.",
                                     self._global[-self.global_dia] + DIA - ahora)
            if self.global_hora and len(ultima_hora) >= self.global_hora:
                raise LimiteSuperado("El asistente está muy solicitado. Vuelve a probar en unos minutos.",
                                     ultima_hora[-self.global_hora] + HORA - ahora)
            if self.por_cliente_hora and len(propias) >= self.por_cliente_hora:
                raise LimiteSuperado("Has usado mucho el asistente en la última hora. Vuelve a probar en unos minutos.",
                                     propias[-self.por_cliente_hora] + HORA - ahora)

            propias.append(ahora)
            self._global.append(ahora)
            if len(self._clientes) > 5000:  # no acumular IPs que ya no cuentan
                for k in [k for k, v in self._clientes.items() if not v or v[-1] <= ahora - HORA]:
                    del self._clientes[k]
