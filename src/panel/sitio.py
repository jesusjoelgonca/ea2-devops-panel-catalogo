"""Generación del panel HTML y del JSON de datos.

La plantilla es un texto con huecos marcados; no se usa un motor de
plantillas porque hay un solo documento y escaparlo a mano con
``html.escape`` evita introducir HTML inyectado desde el catálogo.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from html import escape
from pathlib import Path

from src.panel.datos import Producto
from src.panel.metricas import (
    correlacion_precio_calificacion,
    distribucion_precio,
    mejor_calificado,
    mejores_descuentos,
    por_marca,
    resumen_general,
)

MONEDA = "USD"
FECHA_DATOS = "19 de octubre de 2026"


def _precio(p: float | None) -> str:
    """Formatea el monto en convención colombiana: $1.234,56."""
    if p is None:
        return "&mdash;"
    entero, decimal = f"{p:,.2f}".split(".")
    return "$" + entero.replace(",", ".") + "," + decimal


def _filas_tabla(celdas: list[list[str]]) -> str:
    cuerpo = "".join(
        "<tr>" + "".join(f"<td>{celda}</td>" for celda in fila) + "</tr>" for fila in celdas
    )
    return cuerpo or "<tr><td colspan='9'>Sin datos</td></tr>"


def _tabla_productos(productos: list[Producto]) -> str:
    ordenados = sorted(
        productos,
        key=lambda p: (p.precio is None, p.precio or 0, -p.calificacion),
    )
    filas = [
        [
            f"<a href='{escape(p.url)}'>{escape(p.asin)}</a>",
            escape(p.titulo[:70] + ("…" if len(p.titulo) > 70 else "")),
            escape(p.marca),
            _precio(p.precio),
            f"{p.calificacion:.1f}",
            str(p.resenas),
            escape(p.disponibilidad or "—"),
        ]
        for p in ordenados
    ]
    return _filas_tabla(filas)


def _tabla_marcas(filas: list[dict]) -> str:
    cuerpo = [
        [
            escape(f["marca"]),
            str(f["productos"]),
            _precio(f["precio_promedio"]),
            f"{f['calificacion_promedio']:.2f}",
        ]
        for f in filas
    ]
    return _filas_tabla(cuerpo)


def _lista_descuentos(top: list[dict]) -> str:
    if not top:
        return "<p>No hay descuentos registrados en el catálogo.</p>"
    items = "".join(
        f"<li><strong>{escape(d['marca'])}</strong> &mdash; "
        f"{escape(d['titulo'][:60])}… "
        f"<span class='precio'>{_precio(d['precio'])}</span> "
        f"<span class='chip'>-{d['descuento_pct']:.1f}%</span></li>"
        for d in top
    )
    return f"<ul class='lista-top'>{items}</ul>"


def _lista_calificados(top: list[dict]) -> str:
    items = "".join(
        f"<li><strong>{escape(c['marca'])}</strong> &mdash; "
        f"{escape(c['titulo'][:60])}… "
        f"<span class='chip'>{c['calificacion']:.1f} &#9733;</span> "
        f"<span class='detalle'>{c['resenas']} rese&ntilde;as</span></li>"
        for c in top
    )
    return f"<ul class='lista-top'>{items}</ul>"


def _barras_tramos(tramos: list[dict]) -> str:
    maximo = max((t["productos"] for t in tramos), default=0) or 1
    barras = "".join(
        "<div class='fila-barra'>"
        f"<span class='etiqueta-tramo'>{escape(t['tramo'])}</span>"
        f"<span class='barra' style='width:{t['productos'] / maximo * 100:.0f}%'></span>"
        f"<span class='valor-tramo'>{t['productos']}</span>"
        "</div>"
        for t in tramos
    )
    return f"<div class='barras'>{barras}</div>"


PLANTILLA = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Panel del catálogo — Programación para Análisis de Datos (EA2)</title>
<style>
:root {{ --tinta: #1a1a1a; --borde: #d8d8d8; --suave: #f5f5f2; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font: 15px/1.55 Georgia, "Times New Roman", serif; color: var(--tinta); background: #fff; }}
main {{ max-width: 1080px; margin: 0 auto; padding: 2.2rem 1.4rem 4rem; }}
header {{ border-bottom: 3px double var(--tinta); padding-bottom: 1rem; margin-bottom: 1.6rem; }}
h1 {{ font-size: 1.7rem; margin: 0 0 .3rem; }}
header p {{ margin: 0; color: #555; font-size: .92rem; }}
h2 {{ font-size: 1.15rem; margin: 2.2rem 0 .8rem; padding-bottom: .3rem; border-bottom: 1px solid var(--borde); }}
.tarjetas {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: .8rem; }}
.tarjeta {{ border: 1px solid var(--borde); border-top: 3px solid var(--tinta); padding: .8rem 1rem; background: var(--suave); }}
.tarjeta .cifra {{ font-size: 1.5rem; font-weight: bold; }}
.tarjeta .rotulo {{ font-size: .8rem; color: #555; text-transform: uppercase; letter-spacing: .06em; }}
.dos-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }}
@media (max-width: 760px) {{ .dos-col {{ grid-template-columns: 1fr; }} }}
table {{ width: 100%; border-collapse: collapse; font-size: .9rem; }}
th {{ text-align: left; border-bottom: 2px solid var(--tinta); padding: .45rem .5rem; font-family: sans-serif; font-size: .78rem; text-transform: uppercase; letter-spacing: .05em; }}
td {{ border-bottom: 1px solid var(--borde); padding: .45rem .5rem; vertical-align: top; }}
tr:hover td {{ background: var(--suave); }}
a {{ color: var(--tinta); }}
.barras {{ display: flex; flex-direction: column; gap: .5rem; }}
.fila-barra {{ display: flex; align-items: center; gap: .6rem; }}
.etiqueta-tramo {{ width: 110px; font-size: .85rem; text-align: right; flex-shrink: 0; }}
.barra {{ height: 1.15rem; background: var(--tinta); min-width: 2px; }}
.valor-tramo {{ font-size: .85rem; }}
.lista-top {{ padding-left: 1.2rem; margin: 0; }}
.lista-top li {{ margin-bottom: .55rem; }}
.chip {{ display: inline-block; border: 1px solid var(--tinta); padding: 0 .4rem; font-size: .78rem; font-family: sans-serif; }}
.detalle, .precio {{ color: #555; font-size: .85rem; }}
.nota {{ font-size: .82rem; color: #555; border-top: 1px solid var(--borde); margin-top: 2.5rem; padding-top: .8rem; }}
</style>
</head>
<body>
<main>
<header>
<h1>Panel del catálogo de teléfonos inteligentes</h1>
<p>Programación para Análisis de Datos &mdash; Evidencia de aprendizaje 2 &middot;
{productos} productos extraídos de Amazon.com ({FECHA_DATOS}) &middot;
construido y publicado de forma automática con GitHub Actions</p>
</header>

<section class="tarjetas">
<div class="tarjeta"><div class="cifra">{productos}</div><div class="rotulo">Productos</div></div>
<div class="tarjeta"><div class="cifra">{marcas}</div><div class="rotulo">Marcas</div></div>
<div class="tarjeta"><div class="cifra">{precio_promedio}</div><div class="rotulo">Precio promedio ({MONEDA})</div></div>
<div class="tarjeta"><div class="cifra">{calificacion}</div><div class="rotulo">Calificación media</div></div>
<div class="tarjeta"><div class="cifra">{resenas}</div><div class="rotulo">Reseñas totales</div></div>
<div class="tarjeta"><div class="cifra">{descuento}</div><div class="rotulo">Descuento medio</div></div>
</section>

<h2>Distribución por tramo de precio</h2>
{barras}

<div class="dos-col">
<div>
<h2>Mayores descuentos</h2>
{descuentos}
</div>
<div>
<h2>Mejor calificados</h2>
{calificados}
</div>
</div>

<h2>Resumen por marca</h2>
<table>
<thead><tr><th>Marca</th><th>Productos</th><th>Precio promedio</th><th>Calificación media</th></tr></thead>
<tbody>{tabla_marcas}</tbody>
</table>

<h2>Catálogo completo</h2>
<table>
<thead><tr><th>ASIN</th><th>Título</th><th>Marca</th><th>Precio</th><th>Calif.</th><th>Reseñas</th><th>Disponibilidad</th></tr></thead>
<tbody>{tabla_productos}</tbody>
</table>

<p class="nota">Correlación precio&ndash;calificación (Pearson): <strong>{correlacion}</strong> sobre
{con_precio} productos con precio conocido. Datos obtenidos por <em>web scraping</em> en la
Evidencia de aprendizaje 1; la extracción se limitó a fichas públicas, respetando robots.txt.
Fuente: <a href="datos.json">datos.json</a>.</p>
</main>
</body>
</html>
"""


def construir_datos(productos: list[Producto]) -> dict:
    """Estructura plana que se escribe en datos.json y alimenta la plantilla."""
    return {
        "generado_el": FECHA_DATOS,
        "resumen": resumen_general(productos),
        "por_marca": por_marca(productos),
        "tramos_precio": distribucion_precio(productos),
        "mejores_descuentos": mejores_descuentos(productos),
        "mejor_calificados": mejor_calificado(productos),
        "correlacion_precio_calificacion": correlacion_precio_calificacion(productos),
        "productos": [asdict(p) for p in productos],
    }


def construir_html(productos: list[Producto]) -> str:
    """Rellena la plantilla con los indicadores y el catálogo escapados."""
    resumen = resumen_general(productos)
    precio = resumen["precio_promedio"]
    correlacion = correlacion_precio_calificacion(productos)
    huecos = {
        "productos": resumen["productos"],
        "marcas": resumen["marcas"],
        "precio_promedio": "&mdash;" if precio is None else _precio(precio),
        "calificacion": f"{resumen['calificacion_promedio']:.2f} / 5",
        "resenas": f"{resumen['resenas_totales']:,}".replace(",", "."),
        "descuento": "&mdash;" if resumen["descuento_promedio"] is None else f"{resumen['descuento_promedio']:.1f} %",
        "barras": _barras_tramos(distribucion_precio(productos)),
        "descuentos": _lista_descuentos(mejores_descuentos(productos)),
        "calificados": _lista_calificados(mejor_calificado(productos)),
        "tabla_marcas": _tabla_marcas(por_marca(productos)),
        "tabla_productos": _tabla_productos(productos),
        "correlacion": "sin datos suficientes" if correlacion is None else f"{correlacion:+.3f}",
        "con_precio": resumen["con_precio"],
        "FECHA_DATOS": FECHA_DATOS,
        "MONEDA": MONEDA,
    }
    return PLANTILLA.format(**huecos)


def escribir(salida: str | Path, productos: list[Producto]) -> Path:
    """Escribe index.html y datos.json en la carpeta indicada y la devuelve."""
    carpeta = Path(salida)
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "index.html").write_text(construir_html(productos), encoding="utf-8")
    (carpeta / "datos.json").write_text(
        json.dumps(construir_datos(productos), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return carpeta
