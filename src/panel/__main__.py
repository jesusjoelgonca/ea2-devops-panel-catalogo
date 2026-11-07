"""Punto de entrada del panel: ``python -m src.panel construir ...``."""

from __future__ import annotations

import argparse
import sys

from src.panel.datos import CatalogoNoValido, cargar
from src.panel.sitio import escribir

RUTA_CATALOGO = "data/catalogo_consolidado.csv"
RUTA_SALIDA = "site"


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="src.panel",
        description="Genera el panel web a partir del catálogo consolidado.",
    )
    sub = parser.add_subparsers(dest="comando", required=True)
    construir = sub.add_parser("construir", help="genera site/index.html y site/datos.json")
    construir.add_argument("--catalogo", default=RUTA_CATALOGO, help="ruta del CSV de entrada")
    construir.add_argument("--salida", default=RUTA_SALIDA, help="carpeta de salida del sitio")
    return parser


def main(argv: list[str] | None = None) -> int:
    argumentos = construir_parser().parse_args(argv)
    if argumentos.comando == "construir":
        try:
            productos = cargar(argumentos.catalogo)
        except CatalogoNoValido as error:
            print(f"Error: {error}", file=sys.stderr)
            return 1
        carpeta = escribir(argumentos.salida, productos)
        con_precio = sum(1 for p in productos if p.precio is not None)
        print(f"Panel generado en {carpeta}")
        print(f"Productos: {len(productos)} ({con_precio} con precio conocido)")
        print(f"Salidas: {carpeta}/index.html, {carpeta}/datos.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
