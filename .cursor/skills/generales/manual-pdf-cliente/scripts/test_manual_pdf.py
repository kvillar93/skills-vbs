# -*- coding: utf-8 -*-
"""Prueba mínima del motor de manuales."""
import tempfile
import unittest
from pathlib import Path

from manual_pdf import Manual, cargar_spec, destinos_salida, _registrar_fuentes


DIR = Path(__file__).resolve().parent


class TestManualPdf(unittest.TestCase):
    def test_ejemplo_genera_pdf(self):
        spec = cargar_spec(DIR / "ejemplo_spec.json")
        _registrar_fuentes()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "out.pdf"
            escritos = Manual(spec, DIR).generar([dest])
            self.assertTrue(escritos[0].is_file())
            self.assertGreater(escritos[0].stat().st_size, 2000)

    def test_destinos_incluyen_descargas(self):
        destinos = destinos_salida({"salida": "X.pdf"}, Path("."), descargas=True)
        self.assertEqual(destinos[0].name, "X.pdf")
        self.assertEqual(destinos[1], Path.home() / "Downloads" / "X.pdf")

    def test_paleta_invalida(self):
        _registrar_fuentes()
        with self.assertRaises(ValueError):
            Manual({"paleta": "noexiste", "paginas": []}, DIR)


if __name__ == "__main__":
    unittest.main()
