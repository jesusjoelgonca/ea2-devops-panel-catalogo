"""Pruebas de la carga y validación del catálogo."""

import unittest
from pathlib import Path

from src.panel.datos import CatalogoNoValido, Producto, cargar, con_precio

CATALOGO = Path("data/catalogo_consolidado.csv")


class PruebaCargarCatalogo(unittest.TestCase):
    def test_carga_todos_los_productos(self):
        productos = cargar(CATALOGO)
        self.assertEqual(len(productos), 16)

    def test_campos_del_articulo_principal(self):
        productos = {p.asin: p for p in cargar(CATALOGO)}
        principal = productos["B0GW9TVHJB"]
        self.assertEqual(principal.marca, "Samsung")
        self.assertEqual(principal.moneda, "USD")
        self.assertAlmostEqual(principal.precio, 499.99)
        self.assertAlmostEqual(principal.calificacion, 4.4)
        self.assertEqual(principal.resenas, 209)
        self.assertTrue(principal.url.startswith("https://www.amazon.com/dp/"))

    def test_producto_sin_precio_se_acepta(self):
        # El buybox suprimido deja la celda de precio vacía: el registro es válido.
        productos = {p.asin: p for p in cargar(CATALOGO)}
        self.assertIsNone(productos["B0DJBV4VBJ"].precio)

    def test_con_precio_excluye_al_producto_sin_buybox(self):
        con_p = con_precio(cargar(CATALOGO))
        self.assertEqual(len(con_p), 15)
        self.assertTrue(all(p.precio is not None for p in con_p))

    def test_asin_duplicado_se_detecta_como_estructura_simple(self):
        productos = cargar(CATALOGO)
        asines = [p.asin for p in productos]
        self.assertEqual(len(asines), len(set(asines)))

    def test_archivo_inexistente_da_error_claro(self):
        with self.assertRaises(CatalogoNoValido) as contexto:
            cargar("data/no_existe.csv")
        self.assertIn("No se encontró", str(contexto.exception))


class PruebaValidacion(unittest.TestCase):
    def _catalogo_temporal(self, texto):
        archivo = Path("data/_prueba_temporal.csv")
        archivo.write_text(texto, encoding="utf-8")
        self.addCleanup(archivo.unlink)
        return archivo

    def _fila_base(self, **cambios):
        valores = {
            "asin": "TEST0001",
            "titulo": "Teléfono de prueba",
            "marca": "Acme",
            "precio": "199.99",
            "moneda": "USD",
            "precio_lista": "",
            "descuento_pct": "",
            "calificacion": "4.5",
            "resenas": "12",
            "disponibilidad": "In Stock",
            "url": "https://www.amazon.com/dp/TEST0001",
        }
        valores.update(cambios)
        cabecera = ",".join(valores)
        fila = ",".join(str(v) for v in valores.values())
        return cabecera + "\n" + fila + "\n"

    def test_catalogo_vacio_rechazado(self):
        ruta = self._catalogo_temporal("asin,titulo,marca\n")
        with self.assertRaises(CatalogoNoValido):
            cargar(ruta)

    def test_columna_faltante_rechazada(self):
        texto = self._fila_base().replace(",calificacion,", ",")
        ruta = self._catalogo_temporal(texto)
        with self.assertRaises(CatalogoNoValido) as contexto:
            cargar(ruta)
        self.assertIn("columna", str(contexto.exception))

    def test_precio_negativo_rechazado(self):
        ruta = self._catalogo_temporal(self._fila_base(precio="-5"))
        with self.assertRaises(CatalogoNoValido) as contexto:
            cargar(ruta)
        self.assertIn("negativo", str(contexto.exception))

    def test_calificacion_fuera_de_rango_rechazada(self):
        ruta = self._catalogo_temporal(self._fila_base(calificacion="5.6"))
        with self.assertRaises(CatalogoNoValido) as contexto:
            cargar(ruta)
        self.assertIn("fuera de rango", str(contexto.exception))

    def test_sin_asin_rechazado(self):
        ruta = self._catalogo_temporal(self._fila_base(asin=""))
        with self.assertRaises(CatalogoNoValido) as contexto:
            cargar(ruta)
        self.assertIn("ASIN", str(contexto.exception))

    def test_producto_inmutable(self):
        producto = cargar(CATALOGO)[0]
        self.assertIsInstance(producto, Producto)
        with self.assertRaises(Exception):
            producto.precio = 1.0  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
