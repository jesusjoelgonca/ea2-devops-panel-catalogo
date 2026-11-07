"""Indicadores del mercado a partir del catálogo cargado.

Todas las funciones son puras: reciben productos y devuelven estructuras
planas que el sitio puede serializar tal cual. Ninguna depende de NumPy;
con dieciséis productos el cálculo manual es más claro y mantiene el
proyecto sin dependencias externas.
"""

from __future__ import annotations

from statistics import correlation, mean, median

from src.panel.datos import Producto, con_precio

TRAMOS_PRECIO = (
    ("< $300", 0.0, 300.0),
    ("$300 - $499", 300.0, 500.0),
    ("$500 - $799", 500.0, 800.0),
    (">= $800", 800.0, float("inf")),
)


def resumen_general(productos: list[Producto]) -> dict:
    """Cifras de cabecera del panel."""
    con_p = con_precio(productos)
    precios = [p.precio for p in con_p]
    resumen = {
        "productos": len(productos),
        "con_precio": len(con_p),
        "marcas": len({p.marca for p in productos}),
        "precio_promedio": round(mean(precios), 2) if precios else None,
        "precio_mediano": round(median(precios), 2) if precios else None,
        "precio_minimo": min(precios) if precios else None,
        "precio_maximo": max(precios) if precios else None,
        "calificacion_promedio": round(mean(p.calificacion for p in productos), 2),
        "resenas_totales": sum(p.resenas for p in productos),
        "descuento_promedio": _descuento_promedio(con_p),
    }
    return resumen


def _descuento_promedio(productos: list[Producto]) -> float | None:
    descuentos = [p.descuento_pct for p in productos if p.descuento_pct is not None]
    return round(mean(descuentos), 1) if descuentos else None


def por_marca(productos: list[Producto]) -> list[dict]:
    """Agregados por marca, ordenados de mayor a menor precio promedio."""
    grupos: dict[str, list[Producto]] = {}
    for producto in productos:
        grupos.setdefault(producto.marca, []).append(producto)

    filas = []
    for marca, lista in grupos.items():
        con_p = con_precio(lista)
        precios = [p.precio for p in con_p]
        filas.append(
            {
                "marca": marca,
                "productos": len(lista),
                "precio_promedio": round(mean(precios), 2) if precios else None,
                "calificacion_promedio": round(mean(p.calificacion for p in lista), 2),
            }
        )
    filas.sort(key=lambda fila: (fila["precio_promedio"] is None, -(fila["precio_promedio"] or 0)))
    return filas


def mejores_descuentos(productos: list[Producto], cantidad: int = 5) -> list[dict]:
    """Los productos con mayor descuento sobre el precio de lista."""
    con_descuento = [p for p in productos if p.descuento_pct is not None and p.precio is not None]
    con_descuento.sort(key=lambda p: p.descuento_pct, reverse=True)
    return [
        {
            "asin": p.asin,
            "titulo": p.titulo,
            "marca": p.marca,
            "precio": p.precio,
            "precio_lista": p.precio_lista,
            "descuento_pct": p.descuento_pct,
        }
        for p in con_descuento[:cantidad]
    ]


def distribucion_precio(productos: list[Producto]) -> list[dict]:
    """Cantidad de productos por tramo de precio; los sin precio no cuentan."""
    tramos = [{"tramo": nombre, "productos": 0} for nombre, _, _ in TRAMOS_PRECIO]
    for producto in con_precio(productos):
        for indice, (_, desde, hasta) in enumerate(TRAMOS_PRECIO):
            if desde <= producto.precio < hasta:
                tramos[indice]["productos"] += 1
                break
    return tramos


def correlacion_precio_calificacion(productos: list[Producto]) -> float | None:
    """Coeficiente de Pearson entre precio y calificación; None si no hay datos."""
    pares = [(p.precio, p.calificacion) for p in con_precio(productos)]
    if len(pares) < 3:
        return None
    precios, calificaciones = zip(*pares)
    return round(correlation(precios, calificaciones), 3)


def mejor_calificado(productos: list[Producto], cantidad: int = 5) -> list[dict]:
    """Top de calificación; el empate se deshace con más reseñas."""
    ordenados = sorted(productos, key=lambda p: (p.calificacion, p.resenas), reverse=True)
    return [
        {
            "asin": p.asin,
            "titulo": p.titulo,
            "marca": p.marca,
            "calificacion": p.calificacion,
            "resenas": p.resenas,
            "precio": p.precio,
        }
        for p in ordenados[:cantidad]
    ]
