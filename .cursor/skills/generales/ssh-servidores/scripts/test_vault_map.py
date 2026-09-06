"""Tests de vault_map (sin tocar 1Password ni archivos PEM)."""

from __future__ import annotations

import unittest

from vault_map import (
    VAULT_NOMBRE,
    destino_para_alias,
    es_host_password,
    item_para_alias,
    item_para_pem,
    nombres_pem,
    referencia_clave_privada,
    referencias_clave_privada,
)


class TestVaultMap(unittest.TestCase):
    def test_vault_nombre(self) -> None:
        self.assertEqual(VAULT_NOMBRE, "SSH-Infra")

    def test_siete_pems(self) -> None:
        self.assertEqual(len(nombres_pem()), 7)
        self.assertIn("vbsolutions", nombres_pem())

    def test_item_pem(self) -> None:
        self.assertEqual(item_para_pem("vbsolutions"), "vbsolutions")
        with self.assertRaises(ValueError) as ctx:
            item_para_pem("no-existe")
        self.assertIn("PEM desconocida", str(ctx.exception))

    def test_password_aliases(self) -> None:
        self.assertTrue(es_host_password("aurora"))
        self.assertTrue(es_host_password("STI-NUEVO"))
        self.assertTrue(es_host_password("ssh-tercero-stocaklu"))
        self.assertFalse(es_host_password("vbs-hermes"))
        self.assertEqual(item_para_alias("sti-nuevo-server"), "sti-nuevo")
        self.assertEqual(item_para_alias("stockalu-tercero"), "stockalu-tercero")

    def test_alias_con_pem_de_hosts(self) -> None:
        self.assertEqual(item_para_alias("vbs-hermes", "vbsolutions"), "vbsolutions")
        self.assertEqual(item_para_alias("vbs-hermes"), "vbsolutions")
        self.assertEqual(item_para_alias("lifter"), "odoo_xolver")
        self.assertEqual(item_para_alias("tsheila", "odoo_xolver"), "odoo_xolver")
        self.assertEqual(item_para_alias("75g-vbs", "vbsolutions"), "vbsolutions")
        self.assertEqual(item_para_alias("vvl-ppk"), "vvl")

    def test_alias_sin_pem_falla(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            item_para_alias("cliente-nuevo")
        self.assertIn("No pude resolver", str(ctx.exception))

    def test_destino_hermes(self) -> None:
        d = destino_para_alias("vbs-hermes")
        self.assertEqual(d.hostname, "44.217.48.118")
        self.assertEqual(d.usuario, "ubuntu")
        self.assertEqual(d.puerto, 22)
        self.assertEqual(d.pem, "vbsolutions")
        self.assertFalse(d.es_password)

    def test_destino_xolver_puerto(self) -> None:
        d = destino_para_alias("xolver")
        self.assertEqual(d.hostname, "erp.xolver.com")
        self.assertEqual(d.puerto, 4525)

    def test_destino_alias_corto(self) -> None:
        self.assertEqual(destino_para_alias("75g-vbs").pem, "vbsolutions")
        self.assertEqual(destino_para_alias("lifter").pem, "odoo_xolver")

    def test_destino_desconocido(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            destino_para_alias("no-existe-xyz")
        self.assertIn("hosts.md", str(ctx.exception))

    def test_referencia_no_filtra_material(self) -> None:
        ref = referencia_clave_privada("vbsolutions")
        self.assertTrue(ref.startswith("op://SSH-Infra/vbsolutions/"))
        self.assertIn("private key", ref)
        self.assertNotIn("BEGIN", ref)
        refs = referencias_clave_privada("vbsolutions")
        self.assertTrue(any(r.endswith("vbsolutions.pem") for r in refs))
        self.assertTrue(all("BEGIN" not in r for r in refs))


if __name__ == "__main__":
    unittest.main()
