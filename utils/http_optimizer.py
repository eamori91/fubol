"""
Optimizador de peticiones HTTP para consultas a APIs externas.
Incluye manejo de rate limiting, retry, paralelización y timeout.
"""

import time
import logging
import asyncio
import aiohttp
import requests
from typing import Dict, Any, List, Optional, Union, Callable, Tuple
from functools import wraps
import random
from concurrent.futures import ThreadPoolExecutor

# Configurar logging
logger = logging.getLogger('http_optimizer')

class HTTPOptimizer:
    """
    Optimizador de peticiones HTTP para mejorar la eficiencia
    y confiabilidad de las consultas a APIs externas.
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 30.0,
        max_connections: int = 10,
        rate_limit: Optional[Dict[str, Tuple[int, int]]] = None
    ):
        """
        Inicializa el optimizador HTTP.
        
        Args:
            max_retries: Número máximo de reintentos para peticiones fallidas
            retry_delay: Tiempo base de espera entre reintentos (segundos)
            timeout: Tiempo máximo de espera para peticiones (segundos)
            max_connections: Número máximo de conexiones simultáneas
            rate_limit: Dict con límites de tasa por dominio {dominio: (peticiones, segundos)}
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.max_connections = max_connections
        self.rate_limit = rate_limit or {}
        
        # Control de rate limiting
        self._last_request_time: Dict[str, List[float]] = {}
        self._executor = ThreadPoolExecutor(max_workers=max_connections)
        
        logger.info(f"HTTP Optimizer inicializado: max_retries={max_retries}, "
                   f"timeout={timeout}s, max_conn={max_connections}")
    
    def _get_domain(self, url: str) -> str:
        """
        Extrae el dominio de una URL.
        
        Args:
            url: URL a analizar
            
        Returns:
            Dominio extraído
        """
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        return parsed_url.netloc
    
    def _check_rate_limit(self, domain: str) -> float:
        """
        Comprueba si se debe aplicar rate limiting y calcula el tiempo de espera.
        
        Args:
            domain: Dominio de la petición
            
        Returns:
            Tiempo que se debe esperar antes de realizar la petición (segundos)
        """
        if domain not in self.rate_limit:
            return 0.0
            
        max_requests, period = self.rate_limit[domain]
        
        # Inicializar registro de tiempos si no existe
        if domain not in self._last_request_time:
            self._last_request_time[domain] = []
        
        # Eliminar tiempos antiguos fuera del período
        current_time = time.time()
        self._last_request_time[domain] = [
            t for t in self._last_request_time[domain]
            if current_time - t < period
        ]
        
        # Si no hemos alcanzado el límite, no esperar
        if len(self._last_request_time[domain]) < max_requests:
            return 0.0
            
        # Calcular tiempo a esperar para la petición más antigua + period
        oldest_request = min(self._last_request_time[domain])
        wait_time = oldest_request + period - current_time
        
        return max(0.0, wait_time)
    
    def _record_request(self, domain: str) -> None:
        """
        Registra una petición realizada para control de rate limiting.
        
        Args:
            domain: Dominio de la petición
        """
        if domain not in self._last_request_time:
            self._last_request_time[domain] = []
            
        self._last_request_time[domain].append(time.time())
    
    def request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> requests.Response:
        """
        Realiza una petición HTTP con reintentos y rate limiting.
        
        Args:
            method: Método HTTP ('GET', 'POST', etc.)
            url: URL de la petición
            **kwargs: Argumentos adicionales para requests
            
        Returns:
            Objeto Response de requests
            
        Raises:
            requests.RequestException: Si fallan todos los reintentos
        """
        domain = self._get_domain(url)
        
        # Aplicar timeout predeterminado si no se especifica
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
        
        for attempt in range(1, self.max_retries + 1):
            # Aplicar rate limiting
            wait_time = self._check_rate_limit(domain)
            if wait_time > 0:
                logger.debug(f"Rate limit aplicado para {domain}: esperando {wait_time:.2f}s")
                time.sleep(wait_time)
            
            try:
                response = requests.request(method, url, **kwargs)
                
                # Registrar petición realizada
                self._record_request(domain)
                
                # Si es un error 429 (Too Many Requests), aplicar retraso
                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After')
                    wait = float(retry_after) if retry_after and retry_after.isdigit() else self.retry_delay * 2**attempt
                    logger.warning(f"Rate limit detectado para {domain}, esperando {wait}s")
                    time.sleep(wait)
                    continue
                
                # Si es otro error 5XX, reintentar
                if 500 <= response.status_code < 600:
                    wait = self.retry_delay * 2**attempt
                    logger.warning(f"Error {response.status_code} para {url}, reintentando en {wait}s (intento {attempt}/{self.max_retries})")
                    time.sleep(wait)
                    continue
                
                return response
                
            except (requests.RequestException, IOError) as e:
                if attempt < self.max_retries:
                    wait = self.retry_delay * 2**attempt * (0.5 + random.random())  # Jitter
                    logger.warning(f"Error en petición a {url}: {str(e)}, reintentando en {wait:.2f}s (intento {attempt}/{self.max_retries})")
                    time.sleep(wait)
                else:
                    logger.error(f"Error final en petición a {url} después de {self.max_retries} intentos: {str(e)}")
                    raise
        
        # No debería llegar aquí, pero por seguridad
        raise requests.RequestException(f"Todos los intentos fallaron para {url}")
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """Atajo para peticiones GET."""
        return self.request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """Atajo para peticiones POST."""
        return self.request('POST', url, **kwargs)
    
    def put(self, url: str, **kwargs) -> requests.Response:
        """Atajo para peticiones PUT."""
        return self.request('PUT', url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> requests.Response:
        """Atajo para peticiones DELETE."""
        return self.request('DELETE', url, **kwargs)
    
    def parallel_requests(
        self,
        requests_params: List[Dict[str, Any]]
    ) -> List[Optional[requests.Response]]:
        """
        Realiza múltiples peticiones en paralelo.
        
        Args:
            requests_params: Lista de diccionarios con parámetros para cada petición
                             Cada dict debe tener 'method' y 'url', y opcionalmente otros kwargs
        
        Returns:
            Lista de respuestas en el mismo orden (None para las fallidas)
        """
        def _make_request(params):
            try:
                method = params.pop('method')
                url = params.pop('url')
                return self.request(method, url, **params)
            except Exception as e:
                logger.error(f"Error en petición paralela a {url}: {str(e)}")
                return None
        
        return list(self._executor.map(_make_request, requests_params))
    
    async def async_request(
        self,
        session: aiohttp.ClientSession,
        method: str,
        url: str,
        **kwargs
    ) -> Optional[aiohttp.ClientResponse]:
        """
        Realiza una petición HTTP asíncrona con reintentos y rate limiting.
        
        Args:
            session: Sesión aiohttp
            method: Método HTTP ('GET', 'POST', etc.)
            url: URL de la petición
            **kwargs: Argumentos adicionales para aiohttp
            
        Returns:
            Objeto ClientResponse de aiohttp o None si fallan todos los intentos
        """
        domain = self._get_domain(url)
        
        # Aplicar timeout predeterminado si no se especifica
        if 'timeout' not in kwargs:
            kwargs['timeout'] = aiohttp.ClientTimeout(total=self.timeout)
        
        for attempt in range(1, self.max_retries + 1):
            # Aplicar rate limiting
            wait_time = self._check_rate_limit(domain)
            if wait_time > 0:
                logger.debug(f"Rate limit async aplicado para {domain}: esperando {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
            
            try:
                response = await session.request(method, url, **kwargs)
                
                # Registrar petición realizada
                self._record_request(domain)
                
                # Si es un error 429 (Too Many Requests), aplicar retraso
                if response.status == 429:
                    retry_after = response.headers.get('Retry-After')
                    wait = float(retry_after) if retry_after and retry_after.isdigit() else self.retry_delay * 2**attempt
                    logger.warning(f"Rate limit async detectado para {domain}, esperando {wait}s")
                    await asyncio.sleep(wait)
                    continue
                
                # Si es otro error 5XX, reintentar
                if 500 <= response.status < 600:
                    wait = self.retry_delay * 2**attempt
                    logger.warning(f"Error async {response.status} para {url}, reintentando en {wait}s (intento {attempt}/{self.max_retries})")
                    await asyncio.sleep(wait)
                    continue
                
                return response
                
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < self.max_retries:
                    wait = self.retry_delay * 2**attempt * (0.5 + random.random())  # Jitter
                    logger.warning(f"Error async en petición a {url}: {str(e)}, reintentando en {wait:.2f}s (intento {attempt}/{self.max_retries})")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"Error async final en petición a {url} después de {self.max_retries} intentos: {str(e)}")
                    return None
        
        return None
    
    async def async_batch_request(
        self,
        requests_params: List[Dict[str, Any]],
        concurrency_limit: int = None
    ) -> List[Optional[Dict]]:
        """
        Realiza múltiples peticiones HTTP de forma asíncrona.
        
        Args:
            requests_params: Lista de diccionarios con parámetros para cada petición
                             Cada dict debe tener 'method' y 'url', y opcionalmente otros kwargs
            concurrency_limit: Límite de concurrencia (por defecto self.max_connections)
            
        Returns:
            Lista de resultados en el mismo orden (None para las fallidas)
        """
        if concurrency_limit is None:
            concurrency_limit = self.max_connections
            
        # Crear semáforo para limitar concurrencia
        semaphore = asyncio.Semaphore(concurrency_limit)
        
        async def _fetch(params):
            method = params.pop('method')
            url = params.pop('url')
            
            async with semaphore:
                async with aiohttp.ClientSession() as session:
                    try:
                        response = await self.async_request(session, method, url, **params)
                        if response:
                            return {
                                'status': response.status,
                                'headers': dict(response.headers),
                                'text': await response.text()
                            }
                    except Exception as e:
                        logger.error(f"Error en petición batch a {url}: {str(e)}")
                        return None
                    
                    return None
        
        # Crear todas las tareas
        tasks = [_fetch(params) for params in requests_params]
        
        # Ejecutar todas las tareas
        return await asyncio.gather(*tasks)


# Instancia global para uso en toda la aplicación
http_optimizer = HTTPOptimizer()


def optimized_request(func):
    """
    Decorador para optimizar peticiones HTTP en métodos.
    Reemplaza requests.get/post por http_optimizer.get/post.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Guardar referencias originales
        original_get = requests.get
        original_post = requests.post
        original_put = requests.put
        original_delete = requests.delete
        
        # Reemplazar con versiones optimizadas
        requests.get = http_optimizer.get
        requests.post = http_optimizer.post
        requests.put = http_optimizer.put
        requests.delete = http_optimizer.delete
        
        try:
            return func(*args, **kwargs)
        finally:
            # Restaurar originales
            requests.get = original_get
            requests.post = original_post
            requests.put = original_put
            requests.delete = original_delete
    
    return wrapper
