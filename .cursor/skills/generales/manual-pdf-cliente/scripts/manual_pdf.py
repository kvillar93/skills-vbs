# -*- coding: utf-8 -*-
"""Motor de manuales PDF estilo VBS (portada de marca, pasos, capturas o mock Odoo)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

W, H = A4
MARGEN = 42
ANCHO = W - 2 * MARGEN

_FONTS = {"reg": "ManualSans", "bold": "ManualSans-Bold"}

PALETAS = {
    "joseda": {
        "primario": "#1A4D3E",
        "medio": "#2D7A62",
        "suave": "#E6F2EE",
        "acento": "#C4A35A",
        "texto": "#1F2937",
        "gris": "#4B5563",
        "gris_claro": "#F3F4F6",
        "borde": "#D1D5DB",
        "chrome": "#714B67",
        "ok": "#15803D",
        "aviso": "#B45309",
    },
    "abitare": {
        "primario": "#0A3A42",
        "medio": "#0B5F6B",
        "suave": "#E6F4F5",
        "acento": "#14808F",
        "texto": "#1F2937",
        "gris": "#4B5563",
        "gris_claro": "#F3F4F6",
        "borde": "#D1D5DB",
        "chrome": "#714B67",
        "ok": "#15803D",
        "aviso": "#B45309",
    },
    "jm": {
        "primario": "#3D2B8C",
        "medio": "#5B45B5",
        "suave": "#F3F0FF",
        "acento": "#D6CFFF",
        "texto": "#1F2937",
        "gris": "#4B5563",
        "gris_claro": "#F3F4F6",
        "borde": "#E5E7EB",
        "chrome": "#714B67",
        "ok": "#15803D",
        "aviso": "#B45309",
    },
    "vbs": {
        "primario": "#1E3A5F",
        "medio": "#2B5A8A",
        "suave": "#E8F0F8",
        "acento": "#C9A227",
        "texto": "#1F2937",
        "gris": "#4B5563",
        "gris_claro": "#F3F4F6",
        "borde": "#D1D5DB",
        "chrome": "#714B67",
        "ok": "#15803D",
        "aviso": "#B45309",
    },
}


def _registrar_fuentes():
    pares = [
        (Path("C:/Windows/Fonts/calibri.ttf"), Path("C:/Windows/Fonts/calibrib.ttf")),
        (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ),
        (
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
        ),
    ]
    for regular, bold in pares:
        if regular.is_file() and bold.is_file():
            pdfmetrics.registerFont(TTFont(_FONTS["reg"], str(regular)))
            pdfmetrics.registerFont(TTFont(_FONTS["bold"], str(bold)))
            return
    _FONTS["reg"] = "Helvetica"
    _FONTS["bold"] = "Helvetica-Bold"


def _font(bold):
    return _FONTS["bold"] if bold else _FONTS["reg"]


def _hex(valor):
    return HexColor(valor)


class Manual:
    def __init__(self, spec, base_dir):
        self.spec = spec
        self.base = Path(base_dir)
        paleta_id = spec.get("paleta") or "vbs"
        if paleta_id not in PALETAS:
            raise ValueError("Paleta desconocida: %s" % paleta_id)
        self.p = {k: _hex(v) for k, v in PALETAS[paleta_id].items()}

    def texto(self, c, s, x, y, size=11, bold=False, color=None, max_w=None, leading=None):
        color = color if color is not None else self.p["texto"]
        c.setFillColor(color)
        c.setFont(_font(bold), size)
        leading = leading or (size + 4)
        if not max_w:
            c.drawString(x, y, s)
            return y - leading
        palabras = (s or "").split()
        linea = ""
        for palabra in palabras:
            prueba = (linea + " " + palabra).strip()
            if stringWidth(prueba, _font(bold), size) <= max_w:
                linea = prueba
            else:
                if linea:
                    c.drawString(x, y, linea)
                    y -= leading
                linea = palabra
        if linea:
            c.drawString(x, y, linea)
            y -= leading
        return y

    def rrect(self, c, x, y, w, h, fill, stroke=None, radius=6, lw=0.6):
        c.setFillColor(fill)
        if stroke:
            c.setStrokeColor(stroke)
            c.setLineWidth(lw)
            c.roundRect(x, y, w, h, radius, fill=1, stroke=1)
        else:
            c.setStrokeColor(fill)
            c.roundRect(x, y, w, h, radius, fill=1, stroke=0)

    def encabezado(self, c, titulo):
        c.setFillColor(self.p["primario"])
        c.rect(0, H - 48, W, 48, fill=1, stroke=0)
        c.setFillColor(self.p["acento"])
        c.rect(0, H - 52, W, 4, fill=1, stroke=0)
        marca = "%s  ·  %s" % (
            self.spec.get("cliente", "VBS"),
            self.spec.get("marca_corta") or self.spec.get("titulo", "Manual"),
        )
        self.texto(c, marca, MARGEN, H - 30, 11, True, white)
        self.texto(c, titulo, MARGEN, H - 72, 16, True, self.p["primario"])

    def pie(self, c, n, total):
        c.setFillColor(self.p["suave"])
        c.rect(0, 0, W, 36, fill=1, stroke=0)
        c.setFillColor(self.p["gris"])
        c.setFont(_font(False), 9)
        c.drawString(MARGEN, 16, self.spec.get("pie") or self.spec.get("cliente", "VBS"))
        c.drawRightString(W - MARGEN, 16, "Página %s de %s" % (n, total))

    def vineta(self, c, s, x, y, max_w, size=11, marca="•"):
        c.setFillColor(self.p["medio"])
        c.setFont(_font(True), size)
        c.drawString(x, y, marca)
        return self.texto(c, s, x + 14, y, size, False, self.p["texto"], max_w - 14)

    def boton(self, c, etiqueta, x, y, fill=None):
        fill = fill if fill is not None else self.p["ok"]
        bw = stringWidth(etiqueta, _font(True), 9) + 20
        self.rrect(c, x, y, bw, 18, fill, radius=3)
        self.texto(c, etiqueta, x + 10, y + 5, 9, True, white)
        return x + bw + 6

    def portada(self, c):
        c.setFillColor(self.p["primario"])
        c.rect(0, 0, W, H, fill=1, stroke=0)
        c.setFillColor(self.p["medio"])
        c.rect(0, H - 168, W, 168, fill=1, stroke=0)
        c.setFillColor(self.p["acento"])
        c.rect(0, H - 172, W, 4, fill=1, stroke=0)
        self.texto(c, self.spec.get("cliente", "VBS"), MARGEN, H - 70, 18, True, white)
        if self.spec.get("url"):
            self.texto(c, self.spec["url"], MARGEN, H - 92, 12, False, self.p["acento"])
        self.texto(c, "Manual de uso", MARGEN, H - 230, 18, False, self.p["acento"])
        self.texto(c, self.spec.get("titulo", "Manual"), MARGEN, H - 278, 32, True, white)
        if self.spec.get("subtitulo"):
            self.texto(c, self.spec["subtitulo"], MARGEN, H - 318, 32, True, white)
        y_desc = H - 368 if self.spec.get("subtitulo") else H - 328
        if self.spec.get("descripcion"):
            self.texto(
                c, self.spec["descripcion"], MARGEN, y_desc, 13, False, white, ANCHO,
            )
        self.rrect(c, MARGEN, 88, ANCHO, 54, self.p["medio"], radius=6)
        self.texto(
            c,
            self.spec.get("para_quien", "Para el equipo"),
            MARGEN + 16, 122, 12, True, white,
        )
        self.texto(
            c,
            self.spec.get("modulo", ""),
            MARGEN + 16, 102, 10, False, self.p["acento"],
        )
        c.showPage()

    def recuadro_imagen(self, c, path, y_top, max_h=340):
        from PIL import Image

        img = Image.open(path)
        max_w = ANCHO
        iw, ih = img.size
        escala = min(max_w / iw, max_h / ih)
        dw, dh = iw * escala, ih * escala
        x = (W - dw) / 2
        y = y_top - dh
        c.setStrokeColor(self.p["borde"])
        c.setLineWidth(0.6)
        c.rect(x - 2, y - 2, dw + 4, dh + 4, fill=0, stroke=1)
        c.drawImage(
            ImageReader(str(path)), x, y,
            width=dw, height=dh, preserveAspectRatio=True, mask="auto",
        )
        return y

    def pagina_resumen(self, c, pagina, n, total):
        self.encabezado(c, pagina.get("titulo") or "Qué puede hacer")
        y = H - 100
        if pagina.get("intro"):
            y = self.texto(c, pagina["intro"], MARGEN, y, 11, False, self.p["texto"], ANCHO)
            y -= 10
        for i, tarjeta in enumerate(pagina.get("tarjetas") or [], 1):
            if isinstance(tarjeta, dict):
                titulo = tarjeta.get("titulo") or ""
                desc = tarjeta.get("desc") or ""
            else:
                titulo, desc = tarjeta[0], tarjeta[1]
            self.rrect(c, MARGEN, y - 78, ANCHO, 84, self.p["suave"], radius=8)
            self.rrect(c, MARGEN + 12, y - 62, 28, 28, self.p["primario"], radius=14)
            c.setFillColor(white)
            c.setFont(_font(True), 13)
            c.drawCentredString(MARGEN + 26, y - 53, str(i))
            self.texto(c, titulo, MARGEN + 52, y - 42, 13, True, self.p["primario"])
            self.texto(c, desc, MARGEN + 52, y - 60, 10, False, self.p["texto"], ANCHO - 70)
            y -= 96
        self.pie(c, n, total)
        c.showPage()

    def pagina_pasos(self, c, pagina, n, total):
        self.encabezado(c, pagina.get("titulo") or "Pasos")
        y = H - 100
        if pagina.get("intro"):
            y = self.texto(c, pagina["intro"], MARGEN, y, 11, False, self.p["texto"], ANCHO)
            y -= 8
        for i, paso in enumerate(pagina.get("pasos") or [], 1):
            y = self.vineta(c, paso, MARGEN, y, ANCHO, marca="%s." % i)
            y -= 3
        if pagina.get("nota"):
            y -= 10
            self.rrect(
                c, MARGEN, y - 88, ANCHO, 96,
                HexColor("#FFF7ED"), HexColor("#FDBA74"), 8,
            )
            self.texto(
                c, pagina.get("nota_titulo") or "Nota",
                MARGEN + 14, y - 18, 12, True, self.p["aviso"],
            )
            self.texto(
                c, pagina["nota"], MARGEN + 14, y - 38, 10, False, self.p["texto"], ANCHO - 28,
            )
        self.pie(c, n, total)
        c.showPage()

    def pagina_captura(self, c, pagina, n, total):
        self.encabezado(c, pagina.get("titulo") or "Pantalla")
        y = H - 100
        for parrafo in pagina.get("parrafos") or []:
            y = self.texto(c, parrafo, MARGEN, y, 11, False, self.p["texto"], ANCHO)
            y -= 4
        if pagina.get("nota"):
            y = self.texto(c, pagina["nota"], MARGEN, y, 10, False, self.p["gris"], ANCHO)
        y -= 8
        imagen = pagina.get("imagen")
        if imagen:
            path = Path(imagen)
            if not path.is_file():
                path = self.base / imagen
            if not path.is_file():
                raise FileNotFoundError("No está la captura: %s" % imagen)
            self.recuadro_imagen(c, path, y, max_h=min(400, y - 50))
        self.pie(c, n, total)
        c.showPage()

    def pagina_mock_odoo(self, c, pagina, n, total):
        self.encabezado(c, pagina.get("titulo") or "Pantalla")
        y = H - 100
        for parrafo in pagina.get("parrafos") or []:
            y = self.texto(c, parrafo, MARGEN, y, 11, False, self.p["texto"], ANCHO)
            y -= 4
        for i, paso in enumerate(pagina.get("pasos") or [], 1):
            y = self.vineta(c, paso, MARGEN, y, ANCHO, marca="%s." % i)
            y -= 3
        y -= 10
        alto = float(pagina.get("alto_mock") or 176)
        top = y
        self.rrect(c, MARGEN, top - alto, ANCHO, alto, white, self.p["borde"], 5)
        c.setFillColor(self.p["chrome"])
        c.rect(MARGEN, top - 22, ANCHO, 22, fill=1, stroke=0)
        self.texto(
            c, pagina.get("ruta") or "Odoo",
            MARGEN + 10, top - 15, 8, False, HexColor("#E9D5E5"),
        )
        self.texto(
            c, pagina.get("chrome_titulo") or "",
            MARGEN + 12, top - 40, 12, True, self.p["texto"],
        )
        bx = MARGEN + 14
        by = top - 78
        for bot in pagina.get("botones") or []:
            if isinstance(bot, dict):
                etiqueta = bot.get("texto") or ""
                color = _hex(bot["color"]) if bot.get("color") else self.p["ok"]
            else:
                etiqueta, color = bot, self.p["ok"]
            bx = self.boton(c, etiqueta, bx, by, color)
        fy = top - 100
        for campo in pagina.get("campos") or []:
            if isinstance(campo, (list, tuple)) and len(campo) >= 2:
                et, val = campo[0], campo[1]
            else:
                continue
            self.texto(c, et, MARGEN + 14, fy, 8, False, self.p["gris"])
            self.texto(c, val, MARGEN + 200, fy, 10, True, self.p["texto"])
            fy -= 16
        y = top - alto - 14
        if pagina.get("nota"):
            self.texto(c, pagina["nota"], MARGEN, y, 10, False, self.p["gris"], ANCHO)
        self.pie(c, n, total)
        c.showPage()

    def pagina_faq(self, c, pagina, n, total):
        self.encabezado(c, pagina.get("titulo") or "Dudas frecuentes")
        y = H - 100
        for item in pagina.get("faqs") or []:
            if isinstance(item, dict):
                pregunta, respuesta = item.get("q") or "", item.get("a") or ""
            else:
                pregunta, respuesta = item[0], item[1]
            y = self.texto(c, pregunta, MARGEN, y, 11, True, self.p["primario"], ANCHO)
            y = self.texto(c, respuesta, MARGEN, y, 10, False, self.p["texto"], ANCHO)
            y -= 8
            if y < 70:
                break
        self.pie(c, n, total)
        c.showPage()

    def pagina_rutas(self, c, pagina, n, total):
        self.encabezado(c, pagina.get("titulo") or "Ruta rápida")
        y = H - 100
        if pagina.get("intro"):
            y = self.texto(c, pagina["intro"], MARGEN, y, 11, False, self.p["texto"], ANCHO)
            y -= 12
        for item in pagina.get("rutas") or []:
            if isinstance(item, dict):
                titulo, desc = item.get("titulo") or "", item.get("desc") or ""
            else:
                titulo, desc = item[0], item[1]
            self.rrect(c, MARGEN, y - 58, ANCHO, 64, self.p["suave"], radius=6)
            self.texto(c, titulo, MARGEN + 14, y - 16, 12, True, self.p["primario"])
            self.texto(c, desc, MARGEN + 14, y - 34, 10, False, self.p["texto"], ANCHO - 28)
            y -= 72
        self.pie(c, n, total)
        c.showPage()

    def pagina_texto(self, c, pagina, n, total):
        self.encabezado(c, pagina.get("titulo") or "Detalle")
        y = H - 100
        for linea in pagina.get("lineas") or pagina.get("parrafos") or []:
            y = self.texto(c, linea, MARGEN, y, 12, False, self.p["texto"], ANCHO)
            y -= 8
        if pagina.get("nota"):
            y -= 6
            self.texto(c, pagina["nota"], MARGEN, y, 11, False, self.p["gris"], ANCHO)
        self.pie(c, n, total)
        c.showPage()

    def _dibujar_pagina(self, c, pagina, n, total):
        tipo = pagina.get("tipo") or "texto"
        metodos = {
            "resumen": self.pagina_resumen,
            "pasos": self.pagina_pasos,
            "captura": self.pagina_captura,
            "mock_odoo": self.pagina_mock_odoo,
            "faq": self.pagina_faq,
            "rutas": self.pagina_rutas,
            "texto": self.pagina_texto,
        }
        if tipo not in metodos:
            raise ValueError("Tipo de página desconocido: %s" % tipo)
        metodos[tipo](c, pagina, n, total)

    def generar(self, destinos):
        paginas = list(self.spec.get("paginas") or [])
        total = 1 + len(paginas)
        escritos = []
        for out in destinos:
            out = Path(out)
            out.parent.mkdir(parents=True, exist_ok=True)
            c = canvas.Canvas(str(out), pagesize=A4)
            c.setTitle(self.spec.get("pdf_titulo") or self.spec.get("titulo") or "Manual")
            c.setAuthor(self.spec.get("autor") or self.spec.get("cliente") or "VBS")
            c.setSubject(self.spec.get("descripcion") or "")
            self.portada(c)
            for i, pagina in enumerate(paginas, start=2):
                self._dibujar_pagina(c, pagina, i, total)
            c.save()
            escritos.append(out)
        return escritos


def destinos_salida(spec, base_dir, descargas=True):
    nombre = spec.get("salida") or "Manual.pdf"
    destinos = [Path(base_dir) / nombre]
    if descargas:
        destinos.append(Path.home() / "Downloads" / nombre)
    return destinos


def previsualizar(pdf_path, out_dir):
    import pypdfium2 as pdfium

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = pdfium.PdfDocument(str(pdf_path))
    rutas = []
    for i in range(len(doc)):
        img = doc[i].render(scale=1.4).to_pil()
        dest = out_dir / ("p%02d.png" % (i + 1))
        img.save(dest)
        rutas.append(dest)
    return rutas


def cargar_spec(path):
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not data.get("paginas"):
        raise ValueError("El spec no tiene paginas")
    return data


def main(argv=None):
    parser = argparse.ArgumentParser(description="Genera un manual PDF estilo VBS")
    parser.add_argument("--spec", required=True, help="Ruta al manual.json")
    parser.add_argument("--sin-descargas", action="store_true")
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args(argv)
    spec_path = Path(args.spec).resolve()
    spec = cargar_spec(spec_path)
    base = spec_path.parent
    _registrar_fuentes()
    manual = Manual(spec, base)
    destinos = destinos_salida(spec, base, descargas=not args.sin_descargas)
    escritos = []
    for dest in destinos:
        try:
            escritos.extend(manual.generar([dest]))
        except OSError:
            continue
    if not escritos:
        raise SystemExit("No se pudo escribir el PDF")
    for dest in escritos:
        print(dest)
    if args.preview:
        for ruta in previsualizar(escritos[0], base / "_preview"):
            print(ruta)


if __name__ == "__main__":
    main()
