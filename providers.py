import base64
import json
import os
import re
import time
import urllib.parse
from abc import ABC
from datetime import datetime, timedelta, timezone
from typing import Optional
import requests

from models import ArribosResponse, EstacionSearchResponse, GerenciaResponse, RamalResponse

try:
    from zoneinfo import ZoneInfo
    ARG_TZ = ZoneInfo("America/Argentina/Buenos_Aires")
except ImportError:
    ARG_TZ = timezone(timedelta(hours=-3))


class UnauthorizedException(Exception):
    pass


# --- Configuración y Constantes de Autenticación ---
CACHE_FILE_NAME = 'token.dat'
AUTH_ENDPOINT = '/auth/authorize'

CIPHER_RULES = [
    (re.compile(r'a'), ['#t', '#j']),
    (re.compile(r'e'), ['#x', '#p']),
    (re.compile(r'i'), ['#f', '#w']),
    (re.compile(r'o'), ['#l', '#8']),
    (re.compile(r'u'), ['#7', '#0']),
    (re.compile(r'='), ['#g', '#v']),
]


def to_str(x) -> str | None:
    """
    Transforma la entrada a string siempre que sea posible.
    Retorna None si la entrada es None.

    Args:
        x: objeto a convertir a string.
    """
    if isinstance(x, str) or x == None:
        return x
    return str(x)


def format_date(date: datetime) -> str:
    """
    Formatea la fecha como YYYY-MM-DD
    Si la entrada es None, retorna None.
    """
    if date is None:
        return None
    return date.strftime("%Y-%m-%d")


def format_time(date: datetime) -> str:
    """
    Formatea la fecha como HH:MM:SS
    Si la entrada es None, retorna None.
    """
    if date is None:
        return None
    return date.strftime("%H:%M:%S")


def to_argtz(date: datetime, tz=ARG_TZ) -> datetime:
    """
    Convierte la fecha al tz de Argentina.
    Si la entrada es None, retorna None.
    """
    if date is None:
        return None
    return date.astimezone(tz)


class Encoder:
    def __init__(self, s: str = "", cipher_rules: list[tuple[re.Pattern[str], list[str]]] = CIPHER_RULES):
        self.s = s
        self.cipher_rules = cipher_rules

    def base64(self) -> 'Encoder':
        encoded_bytes = base64.b64encode(self.s.encode('utf-8'))
        self.s = encoded_bytes.decode('utf-8')
        return self

    def cipher(self, step: int) -> 'Encoder':
        for pattern, out_list in self.cipher_rules:
            replacement = out_list[step]
            self.s = pattern.sub(replacement, self.s)
        return self

    def reverse(self) -> 'Encoder':
        self.s = self.s[::-1]
        return self

    def timestamp(self) -> 'Encoder':
        # Genera formato YYYYMMDDsofse en UTC
        now_utc = datetime.now(ARG_TZ)
        date_str = now_utc.strftime('%Y%m%d')
        self.s = f"{date_str}sofse"
        return self

    def url(self) -> 'Encoder':
        self.s = urllib.parse.quote(self.s, safe="~!*()'-.")
        return self

    def to_string(self) -> str:
        return self.s


def generate_credentials(encoder: Encoder) -> dict:
    username = encoder.timestamp().base64().to_string()
    password = (
        Encoder(username)
        .base64()
        .cipher(0)
        .reverse()
        .base64()
        .cipher(1)
        .reverse()
        .url()
        .to_string()
    )
    return {"username": username, "password": password}


SOSFE_ENCODER = Encoder()


def load_token(filename: str) -> str:
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception:
            pass
    save_token('', filename)
    return ''


def save_token(token: str, filename: str):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(token)


# --- Verificación de Expiración del Token  ---
def is_token_expired(token: Optional[str]) -> bool:
    if not token:
        return True
    try:
        parts = token.split('.')
        if len(parts) < 2:
            return True
        payload_b64 = parts[1]
        # Añadir padding necesario para decodificar base64
        payload_b64 += '=' * (-len(payload_b64) % 4)
        payload_json = base64.b64decode(payload_b64).decode('utf-8')
        token_data = json.loads(payload_json)
        expiration_date = token_data.get('exp', 0)

        # Comparación en milisegundos
        now_ms = time.time() * 1000
        return now_ms > (expiration_date * 1000)
    except Exception:
        return True


class BaseServiceProvider(ABC):
    def buscar_estaciones(self, nombre: Optional[str] = None, id_ramal: Optional[int] = None):
        """
        Busca estaciones por nombre o ramal

        Args:
            nombre: Nombre de la estación (o parte de él)
            id_ramal: ID del ramal. Puede obtenerse con 'obtener_ramales'.
        """
        pass

    def obtener_ramales(self, id_gerencia: Optional[int] = None):
        """
        Recupera información de ramales

        Args:
            id_gerencia: ID del gerencia. Puede obtenerse con 'obtener_gerencias'.
        """
        pass

    def obtener_gerencias(self, id_empresa: Optional[int] = 1):
        """
        Recupera información de gerencias

        Args:
            id_empresa: ID de la empresa. Por defecto es '1'.
        """
        pass

    def obtener_arribos(self, id: str,
                        hasta: Optional[str] = None,
                        fecha: Optional[str] = None,
                        hora: Optional[str] = None,
                        cantidad: Optional[int] = None,
                        id_ramal: Optional[int] = None,
                        para_app: Optional[bool] = None,
                        sentido: Optional[int] = None,
                        tipo_busqueda: Optional[str] = None):
        """
        Recupera información de arribos para una estación específica

        Args:
            id: ID de la estación. Puede obtenerse con 'buscar_estaciones'.
            hasta: ID de la estación de destino. Puede obtenerse con 'buscar_estaciones'.
            fecha: Fecha de los arribos (YYYY-MM-DD).
            hora: Hora de los arribos (HH:MM)
            cantidad: Cantidad de arribos a devolver (máximo).
            para_app: Indicador para la aplicación.
            id_ramal: ID del ramal. Puede obtenerse con 'obtener_ramales'.
            sentido: Sentido del viaje.
            tipo_busqueda: Tipo de búsqueda.
        """
        pass


class APIServiceProvider(BaseServiceProvider):
    def __init__(self, base_url: str):
        self.base_url = base_url

    def get_from(self, endpoint: str, parameters: dict[str, str] = {}, headers: dict[str, str] = {}) -> requests.Response:
        return requests.get(f"{self.base_url}{endpoint}", params=parameters, headers=headers)

    def buscar_estaciones(self, nombre: Optional[str] = None, id_ramal: Optional[int] = None):
        return self.get_from('/infraestructura/estaciones', parameters={
            'nombre': to_str(nombre),
            'idRamal': to_str(id_ramal),
        })

    def obtener_ramales(self, id_gerencia: Optional[int] = None):
        return self.get_from('/infraestructura/ramales', parameters={
            'idGerencia': to_str(id_gerencia),
        })

    def obtener_gerencias(self, id_empresa: Optional[int] = 1):
        return self.get_from('/infraestructura/gerencias', parameters={
            'idEmpresa': to_str(id_empresa),
        })

    def obtener_arribos(self, id: str,
                        hasta: Optional[str] = None,
                        fecha: Optional[str] = None,
                        hora: Optional[str] = None,
                        cantidad: Optional[int] = None,
                        id_ramal: Optional[int] = None,
                        para_app: Optional[bool] = None,
                        sentido: Optional[int] = None,
                        tipo_busqueda: Optional[str] = None):
        return self.get_from(f'/arribos/estacion/{id}', parameters={
            'hasta': to_str(hasta),
            'fecha': to_str(fecha),
            'hora': to_str(hora),
            'cantidad': to_str(cantidad),
            'id_ramal': to_str(id_ramal),
            'para_app': to_str(para_app),
            'sentido': to_str(sentido),
            'tipo_busqueda': to_str(tipo_busqueda)
        })


class TypedAPIServiceProvider(APIServiceProvider):
    def obtener_arribos(self, id: str,
                        hasta: Optional[str] = None,
                        fecha: Optional[str] = None,
                        hora: Optional[str] = None,
                        cantidad: Optional[int] = None,
                        id_ramal: Optional[int] = None,
                        para_app: Optional[bool] = None,
                        sentido: Optional[int] = None,
                        tipo_busqueda: Optional[str] = None) -> ArribosResponse:

        res = super().obtener_arribos(id, hasta, fecha, hora, cantidad,
                                      id_ramal, para_app, sentido, tipo_busqueda)
        res.raise_for_status()
        return ArribosResponse.model_validate(res.json())

    def buscar_estaciones(self, nombre: Optional[str] = None, id_ramal: Optional[int] = None) -> list[EstacionSearchResponse]:
        res = super().buscar_estaciones(nombre=nombre, id_ramal=id_ramal)
        res.raise_for_status()
        return [EstacionSearchResponse.model_validate(item) for item in res.json()]

    def obtener_ramales(self, id_gerencia: Optional[int] = None) -> list[RamalResponse]:
        res = super().obtener_ramales(id_gerencia=id_gerencia)
        res.raise_for_status()
        return [RamalResponse.model_validate(item) for item in res.json()]

    def obtener_gerencias(self, id_empresa: Optional[int] = 1) -> list[GerenciaResponse]:
        res = super().obtener_gerencias(id_empresa=id_empresa)
        res.raise_for_status()
        return [GerenciaResponse.model_validate(item) for item in res.json()]


class SOFSEApiServiceProvider(TypedAPIServiceProvider):
    def __init__(self, base_url: str = 'https://api-servicios.sofse.gob.ar/v1', auth_endpoint: str = AUTH_ENDPOINT, encoder: Encoder = SOSFE_ENCODER, filename: str = CACHE_FILE_NAME):
        super().__init__(base_url=base_url)
        self.auth_endpoint = auth_endpoint
        self.filename = filename
        self.encoder = encoder
        self.token = load_token(self.filename)

    def generate_token(self):
        creds = generate_credentials(self.encoder)
        res = requests.post(
            f"{self.base_url}{self.auth_endpoint}",
            json=creds,
            headers={'Content-Type': 'application/json'}
        )
        if not res.ok:
            res.raise_for_status()
        data = res.json()
        self.token = data.get('token')
        save_token(self.token, self.filename)

    def get_from(self, endpoint: str, parameters: dict[str, str] = {}, headers: dict[str, str] = {}) -> requests.Response:
        """
        Implementa la lógica de autenticación automática, caché y reintento en caso de 401/403 
        idéntica al comportamiento de la clase Api.
        """
        try:
            if is_token_expired(self.token):
                raise UnauthorizedException("Unauthorized")

            req_headers = {'Content-Type': 'application/json', **headers}
            if self.token:
                req_headers['Authorization'] = self.token

            res = requests.get(f"{self.base_url}{endpoint}",
                               params=parameters, headers=req_headers)

            # Si responde con error de autorización o token vencido, forzamos la excepción para regenerar
            if res.status_code in (401, 403):
                raise UnauthorizedException("Unauthorized")
            return res

        except UnauthorizedException as e:
            self.generate_token()
            req_headers = {'Content-Type': 'application/json', **headers}
            if self.token:
                req_headers['Authorization'] = self.token
            return requests.get(f"{self.base_url}{endpoint}", params=parameters, headers=req_headers)


class AriedroPublicApiServiceProvider(TypedAPIServiceProvider):
    def __init__(self, base_url: str = 'https://ariedro.dev/api-trenes'):
        super().__init__(base_url=base_url)
