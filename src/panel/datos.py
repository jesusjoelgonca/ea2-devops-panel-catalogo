"""Carga y validación del catálogo consolidado producido en la EA1.

El catálogo es un CSV con 26 columnas; aquí solo interesan las que alimentan
el panel. Un registro se acepta si tiene identificador, título y marca, y si
los campos numéricos que trae son consistentes: un producto puede carecer de
precio (el buybox suprimido de la EA1) pero no puede traer un precio negativo
ni una calificación fuera del rango de una a cinco estrellas.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

CAMPOS_REQUERIDOS = (
    "asin",
    "titulo",
    "marca",
    "precio",
    "moneda",
    "precio_lista",
    "descuento_pct",
    "calificacion",
    "resenas",
    "disponibilidad",
    "url",
)

CAMPOS_NUMERICOS = ("precio", "precio_lista", "descuento_pct", "calificacion", "resenas")

CALIFICACION_MINIMA = 0.0
CALIFICACION_MAXIMA = 5.0


class CatalogoNoValido(ValueError):
    """El archivo del catálogo no cumple el contrato esperado."""


@dataclass(frozen=True)
class Producto:
    """Un renglón del catálogo con los campos que usa el panel."""

    asin: str
    titulo: str
    marca: str
    precio: float | None
    moneda: str
    precio_lista: float | None
    descuento_pct: float | None
    calificacion: float
    resenas: int
    disponibilidad: str
    url: str


def _a_numero(texto: str, campo: str, asin: str) -> float | None:
    """Convierte un campo numérico del CSV; vacío significa que no hay dato."""
    limpio = (texto or "").strip()
    if not limpio:
        return None
    try:
        numero = float(limpio)
    except ValueError as error:
        raise CatalogoNoValido(
            f"El producto {asin} trae un valor no numérico en '{campo}': {limpio!r}"
        ) from error
    if numero < 0:
        raise CatalogoNoValido(f"El producto {asin} trae un {campo} negativo: {numero}")
    return numero


def _validar_calificacion(calificacion: float | None, asin: str) -> float:
    if calificacion is None:
        raise CatalogoNoValido(f"El producto {asin} no trae calificación")
    if not CALIFICACION_MINIMA <= calificacion <= CALIFICACION_MAXIMA:
        raise CatalogoNoValido(
            f"El producto {asin} trae una calificación fuera de rango: {calificacion}"
        )
    return calificacion


def _a_producto(fila: dict[str, str], linea: int) -> Producto:
    for campo in CAMPOS_REQUERIDOS:
        if campo not in fila:
            raise CatalogoNoValido(
                f"La línea {linea} no tiene la columna '{campo}' exigida por el catálogo"
            )
    asin = (fila["asin"] or "").strip()
    titulo = (fila["titulo"] or "").strip()
    marca = (fila["marca"] or "").strip()
    if not asin:
        raise CatalogoNoValido(f"La línea {linea} no tiene ASIN")
    if not titulo or not marca:
        raise CatalogoNoValido(f"El producto {asin or linea} no trae título o marca")

    precio = _a_numero(fila["precio"], "precio", asin)
    calificacion = _validar_calificacion(
        _a_numero(fila["calificacion"], "calificacion", asin), asin
    )
    resenas = _a_numero(fila["resenas"], "resenas", asin)
    return Producto(
        asin=asin,
        titulo=titulo,
        marca=marca,
        precio=precio,
        moneda=(fila["moneda"] or "USD").strip(),
        precio_lista=_a_numero(fila["precio_lista"], "precio_lista", asin),
        descuento_pct=_a_numero(fila["descuento_pct"], "descuento_pct", asin),
        calificacion=calificacion,
        resenas=int(resenas) if resenas is not None else 0,
        disponibilidad=(fila["disponibilidad"] or "").strip(),
        url=(fila["url"] or "").strip(),
    )


def cargar(ruta: str | Path) -> list[Producto]:
    """Lee el catálogo y devuelve los productos validados, en orden de archivo."""
    archivo = Path(ruta)
    if not archivo.is_file():
        raise CatalogoNoValido(f"No se encontró el catálogo en {archivo}")

    # utf-8-sig absorbe la marca de orden de bytes que Excel deja al inicio.
    with archivo.open(encoding="utf-8-sig", newline="") as contenido:
        lector = csv.DictReader(contenido)
        if lector.fieldnames is None:
            raise CatalogoNoValido(f"El catálogo {archivo} está vacío")
        productos: list[Producto] = []
        for linea, fila in enumerate(lector, start=2):
            productos.append(_a_producto(fila, linea))
    if not productos:
        raise CatalogoNoValido(f"El catálogo {archivo} no contiene productos")
    return productos


def con_precio(productos: list[Producto]) -> list[Producto]:
    """Subconjunto con precio conocido; alimenta las métricas monetarias."""
    return [p for p in productos if p.precio is not None]
