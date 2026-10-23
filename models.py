from typing import List, Optional, Union, Any
from pydantic import BaseModel, Field


class EstadoGerencia(BaseModel):
    id: int
    mensaje: str
    color: str


class Alerta(BaseModel):
    id: int
    linea_id: Optional[int] = None
    ramal_id: Optional[int] = None
    estacion_id: Optional[int] = None
    sentido: Optional[int] = None
    causa_gtfs: Optional[str] = None
    efecto_gtfs: Optional[str] = None
    icono_fontawesome: Optional[str] = None
    contenido: Optional[str] = None
    habilitado: int
    vigencia_desde: Optional[str] = None
    vigencia_hasta: Optional[str] = None
    criticidad_orden: Optional[int] = None
    criticidad_color_fondo: Optional[str] = None
    criticidad_color_texto: Optional[str] = None


class GerenciaResponse(BaseModel):
    id: int
    id_empresa: int
    nombre: str
    estado: EstadoGerencia
    alerta: Optional[List[Alerta]] = None


class CabeceraRamal(BaseModel):
    id: int
    nombre: str
    siglas: Optional[str] = None
    nombre_corto: Optional[str] = None
    visibilidad: Optional[str] = None


class RamalResponse(BaseModel):
    id: int
    id_estacion_inicial: int
    id_estacion_final: int
    id_gerencia: int
    nombre: str
    estaciones: int
    operativo: int
    es_electrico: int
    tipo_id: int
    puntualidad_tolerancia: int
    siglas: str
    publico: bool
    orden_ramal: int
    mostrar_en_panel_cumplimiento: bool
    cabecera_inicial: CabeceraRamal
    cabecera_final: CabeceraRamal
    alerta: Optional[Any] = None


class VisibilidadEstacion(BaseModel):
    totem: int
    app_mobile: int


class EstacionSearchResponse(BaseModel):
    nombre: str
    id_estacion: str
    id_tramo: str
    orden: str
    id_referencia: str
    latitud: str
    longitud: str
    referencia_orden: str
    radio: Optional[str] = ""
    andenes_habilitados: Optional[str] = ""
    visibilidad: VisibilidadEstacion
    incluida_en_ramales: List[int]
    operativa_en_ramales: List[int]


class Anden(BaseModel):
    id: int
    nombre: str


class Equipo(BaseModel):
    id: Union[int, str]
    nombre: str
    gpss: Optional[List[str]] = None
    esElectrico: Optional[int] = None


class HorarioDetalle(BaseModel):
    programada: Optional[str] = None
    estimada: Optional[str] = None
    real: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    distancia: Optional[Union[float, int]] = None
    velocidad: Optional[int] = None
    referencia: Optional[int] = None
    ultimaHoraRegistrada: Optional[str] = None
    inArea: Optional[bool] = None


class Tramo(BaseModel):
    id: int
    orden: int


class EstacionPuntoDetalle(BaseModel):
    tipo: Optional[dict] = None
    anden: Optional[Anden] = None
    orden: Optional[int] = None
    tramo: Optional[Tramo] = None
    equipo: Optional[Union[Equipo, dict, str]] = None
    nombre: Optional[str] = None
    parada: Optional[bool] = None
    salida: Optional[HorarioDetalle] = None
    llegada: Optional[HorarioDetalle] = None
    idPunto: Optional[int] = None
    idElemento: Optional[int] = None
    programada: Optional[bool] = None
    segundos: Optional[int] = None


class EstadoEstacion(BaseModel):
    id: int
    nombre: str


class DesdeHastaDetalle(BaseModel):
    estacion: Optional[EstacionPuntoDetalle] = None
    punto: Optional[EstacionPuntoDetalle] = None
    estado: Optional[EstadoEstacion] = None


class ClasificacionTipo(BaseModel):
    id: int
    nombre: str


class TipoServicio(BaseModel):
    id: int
    nombre: str
    programado: bool
    clasificacion: ClasificacionTipo
    subclasificacion: int


class Location(BaseModel):
    lat: float
    long: float


class CabeceraFinalServicio(BaseModel):
    id: int
    nombre: str
    nombreCorto: Optional[str] = None


class RamalServicio(BaseModel):
    id: int
    nombre: str
    tolerancia: int
    cabeceraFinal: CabeceraFinalServicio
    cabeceraInicial: CabeceraFinalServicio


class GerenciaServicio(BaseModel):
    id: int
    nombre: str


class ServicioArribo(BaseModel):
    numero: int
    ramal: RamalServicio = Field(..., description="Ramal del servicio")
    gerencia: GerenciaServicio
    cancelacion: Optional[Any] = None
    equipo: Equipo
    oculto: bool
    sentido: int
    tipo: TipoServicio
    leyenda: Optional[str] = None
    location: Location
    id: str
    desde: DesdeHastaDetalle
    hasta: DesdeHastaDetalle
    estaciones: List[EstacionPuntoDetalle]


class ArriboDetalle(BaseModel):
    anden: Optional[Anden] = None
    orden: int
    equipo: Equipo
    nombre: str
    parada: bool
    salida: Optional[HorarioDetalle] = None
    llegada: Optional[HorarioDetalle] = None
    idPunto: int
    idElemento: int
    programada: bool
    segundos: int


class ResultadoArribo(BaseModel):
    arribo: ArriboDetalle
    servicio: ServicioArribo


class ArribosResponse(BaseModel):
    timestamp: int
    results: List[ResultadoArribo]
    total: int
