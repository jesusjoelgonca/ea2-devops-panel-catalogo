"""Pruebas de la generación del panel HTML y del JSON."""

import json
import tempfile
import unittest
from pathlib import Path

from src.panel.datos import Producto, cargar
from src.panel.sitio import construir_datos, construir_html, escribir

CATALOGO = Path("data/catalogo_consolidado.csv")


def _producto(asin, titulo="Teléfono normal", precio=100.0):
    return Producto(
        asin=asin,
        titulo=titulo,
        marca="Acme",
        precio=precio,
        moneda="USD",
        precio_lista=None,
        descuento_pct=None,
        calificacion=4.5,
        resenas=10,
        disponibilidad="In Stock",
        url=f"https://www.amazon.com/dp/{asin}",
    )


class PruebaConstruirHtml(unittest.TestCase):
    def setUp(self):
        self.productos = cargar(CATALOGO)
        self.html = construir_html(self.productos)

    def test_contiene_los_kpis_del_catalogo_real(self):
        self.assertIn("Panel del catálogo", self.html)
        self.assertIn("16</div>", self.html)  # número de productos
        self.assertIn("Samsung", self.html)  # marca presente en tablas

    def test_contiene_los_tres_bloques_de_tablas(self):
        self.assertIn("Distribución por tramo de precio", self.html)
        self.assertIn("Mayores descuentos", self.html)
        self.assertIn("Catálogo completo", self.html)

    def test_enlaces_de_asin_con_url_real(self):
        self.assertIn("https://www.amazon.com/dp/B0GW9TVHJB", self.html)

    def test_titulo_malicioso_queda_escapado(self):
        html = construir_html([_producto("EVIL01", titulo='<script>alert("x")</script>')])
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_producto_sin_precio_muestra_raya(self):
        html = construir_html([_producto("NOP01", precio=None)])
        self.assertIn("&mdash;", html)


class PruebaConstruirDatos(unittest.TestCase):
    def test_estructura_json_completa(self):
        datos = construir_datos(cargar(CATALOGO))
        esperadas = {
            "resumen",
            "por_marca",
            "tramos_precio",
            "mejores_descuentos",
            "mejor_calificados",
            "correlacion_precio_calificacion",
            "productos",
        }
        self.assertTrue(esperadas.issubset(datos.keys()))
        self.assertEqual(len(datos["productos"]), 16)
        self.assertEqual(len(datos["por_marca"]), 7)

    def test_json_serializable_sin_pierde_precision(self):
        datos = construir_datos([_producto("J01", precio=199.99)])
        texto = json.dumps(datos, ensure_ascii=False)
        rehidratado = json.loads(texto)
        self.assertEqual(rehidratado["productos"][0]["precio"], 199.99)


class PruebaEscribir(unittest.TestCase):
    def test_genera_los_dos_archivos(self):
        with tempfile.TemporaryDirectory() as temporal:
            carpeta = escribir(temporal, cargar(CATALOGO))
            indice = Path(carpeta) / "index.html"
            datos = Path(carpeta) / "datos.json"
            self.assertTrue(indice.is_file())
            self.assertTrue(datos.is_file())
            contenido = json.loads(datos.read_text(encoding="utf-8"))
            self.assertEqual(contenido["resumen"]["productos"], 16)
            self.assertIn("Panel del catálogo", indice.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
