"""Pruebas de los indicadores del mercado."""

import unittest

from src.panel.datos import Producto
from src.panel.metricas import (
    correlacion_precio_calificacion,
    distribucion_precio,
    mejor_calificado,
    mejores_descuentos,
    por_marca,
    resumen_general,
)


def _producto(asin, marca="Acme", precio=None, calificacion=4.0, resenas=10, descuento=None):
    return Producto(
        asin=asin,
        titulo=f"Teléfono {asin}",
        marca=marca,
        precio=precio,
        moneda="USD",
        precio_lista=None if descuento is None else (precio or 0) / (1 - descuento / 100),
        descuento_pct=descuento,
        calificacion=calificacion,
        resenas=resenas,
        disponibilidad="In Stock",
        url=f"https://www.amazon.com/dp/{asin}",
    )


class PruebaResumenGeneral(unittest.TestCase):
    def test_cifras_conocidas(self):
        productos = [
            _producto("A1", precio=100, calificacion=4.0, resenas=5),
            _producto("A2", precio=300, calificacion=5.0, resenas=15),
        ]
        resumen = resumen_general(productos)
        self.assertEqual(resumen["productos"], 2)
        self.assertEqual(resumen["con_precio"], 2)
        self.assertEqual(resumen["marcas"], 1)
        self.assertEqual(resumen["precio_promedio"], 200.0)
        self.assertEqual(resumen["precio_mediano"], 200.0)
        self.assertEqual(resumen["precio_minimo"], 100)
        self.assertEqual(resumen["precio_maximo"], 300)
        self.assertEqual(resumen["calificacion_promedio"], 4.5)
        self.assertEqual(resumen["resenas_totales"], 20)

    def test_producto_sin_precio_no_distorsiona_el_promedio(self):
        productos = [
            _producto("A1", precio=100, calificacion=4.0),
            _producto("A2", precio=None, calificacion=4.0),
        ]
        resumen = resumen_general(productos)
        self.assertEqual(resumen["productos"], 2)
        self.assertEqual(resumen["con_precio"], 1)
        self.assertEqual(resumen["precio_promedio"], 100.0)


class PruebaPorMarca(unittest.TestCase):
    def test_orden_descendente_por_precio(self):
        productos = [
            _producto("A1", marca="Barata", precio=100),
            _producto("A2", marca="Cara", precio=900),
            _producto("A3", marca="Cara", precio=500),
        ]
        filas = por_marca(productos)
        self.assertEqual([f["marca"] for f in filas], ["Cara", "Barata"])
        self.assertEqual(filas[0]["precio_promedio"], 700.0)
        self.assertEqual(filas[0]["productos"], 2)


class PruebaDescuentos(unittest.TestCase):
    def test_orden_y_recorte(self):
        productos = [
            _producto("A1", precio=100, descuento=10),
            _producto("A2", precio=200, descuento=30),
            _producto("A3", precio=300, descuento=20),
            _producto("A4", precio=400, descuento=40),
        ]
        top = mejores_descuentos(productos, cantidad=2)
        self.assertEqual([t["asin"] for t in top], ["A4", "A2"])

    def test_excluye_al_producto_sin_descuento(self):
        top = mejores_descuentos([_producto("A1", precio=100)], cantidad=5)
        self.assertEqual(top, [])


class PruebaDistribucion(unittest.TestCase):
    def test_tramos_correctos(self):
        productos = [
            _producto("A1", precio=100),
            _producto("A2", precio=350),
            _producto("A3", precio=600),
            _producto("A4", precio=900),
            _producto("A5", precio=None),
        ]
        tramos = {t["tramo"]: t["productos"] for t in distribucion_precio(productos)}
        self.assertEqual(tramos["< $300"], 1)
        self.assertEqual(tramos["$300 - $499"], 1)
        self.assertEqual(tramos["$500 - $799"], 1)
        self.assertEqual(tramos[">= $800"], 1)

    def test_limitede_rango_superior_incluido(self):
        tramos = {t["tramo"]: t["productos"] for t in distribucion_precio([_producto("A9", precio=800)])}
        self.assertEqual(tramos[">= $800"], 1)


class PruebaCorrelacion(unittest.TestCase):
    def test_correlacion_positiva_perfecta(self):
        productos = [_producto("A1", precio=100, calificacion=3.0), _producto("A2", precio=200, calificacion=4.0), _producto("A3", precio=300, calificacion=5.0)]
        self.assertAlmostEqual(correlacion_precio_calificacion(productos), 1.0)

    def test_correlacion_negativa_perfecta(self):
        productos = [_producto("A1", precio=100, calificacion=5.0), _producto("A2", precio=200, calificacion=4.0), _producto("A3", precio=300, calificacion=3.0)]
        self.assertAlmostEqual(correlacion_precio_calificacion(productos), -1.0)

    def test_muestra_insuficiente_devuelve_none(self):
        self.assertIsNone(correlacion_precio_calificacion([_producto("A1", precio=100), _producto("A2", precio=200)]))

    def test_sin_precios_devuelve_none(self):
        self.assertIsNone(correlacion_precio_calificacion([_producto("A1"), _producto("A2"), _producto("A3")]))


class PruebaMejorCalificado(unittest.TestCase):
    def test_empate_se_deshace_con_resenas(self):
        productos = [
            _producto("A1", calificacion=4.8, resenas=10),
            _producto("A2", calificacion=4.8, resenas=50),
            _producto("A3", calificacion=4.9, resenas=5),
        ]
        top = mejor_calificado(productos)
        self.assertEqual([t["asin"] for t in top], ["A3", "A2", "A1"])


if __name__ == "__main__":
    unittest.main()
