---
name: manual-pdf-cliente
description: >-
  Genera manuales PDF de uso para clientes VBS (Odoo, JOSEDA, Abitare, JM)
  con portada de marca, pasos, capturas reales o mockups. Usar cuando pidan
  un manual, PDF para el cliente, guía de uso, manual de módulo, o capturas
  de una instancia (joseda.vbsolutions.app, abitare, jmsecuritysystem).
---

# Manual PDF para el cliente

Estilo de referencia: el de Gestión de cobros JOSEDA (portada de marca, pasos
numerados, mock Odoo o captura, FAQ, ruta rápida). Texto en **español**.
Copia siempre a **Descargas**.

## Obligatorio

1. Lee esta skill **antes** de escribir un `generar_pdf.py` nuevo.
2. Usa el helper `scripts/manual_pdf.py` (no copies el motor a cada módulo).
3. El contenido sale de las pantallas y strings reales del módulo, no de memoria.
4. Revisa las páginas renderizadas (`--preview`) antes de darlo por cerrado.
5. No subas el PDF al servidor salvo que el usuario lo pida.

## Dónde vive el manual

En el módulo:

```
nombre_modulo/doc_manual/
  manual.json
  01_lista.png          # solo si hay capturas
  Manual_Tema_Cliente.pdf
  .gitignore            # _preview/
```

Nombre del PDF: `Manual_<Tema>_<Cliente>.pdf` (sin espacios raros).

## Cómo generar

```powershell
pip install -r $env:USERPROFILE\.cursor\skills\manual-pdf-cliente\scripts\requirements.txt
python $env:USERPROFILE\.cursor\skills\manual-pdf-cliente\scripts\manual_pdf.py --spec ruta\doc_manual\manual.json --preview
```

Si no existe el junction plano, la ruta es
`~/.cursor/skills/generales/manual-pdf-cliente/scripts/manual_pdf.py`.

`--preview` deja PNG en `doc_manual/_preview/`. Ábrelos y corrige solapes.

## Spec (`manual.json`)

Campos de portada: `cliente`, `url`, `titulo`, `subtitulo`, `descripcion`,
`para_quien`, `modulo`, `pie`, `paleta`, `salida`, `pdf_titulo`, `autor`.

Paletas: `joseda` (verde), `abitare` (teal), `jm` (morado), `vbs` (azul).

`paginas` es una lista. Tipos:

| tipo | Usa cuando | Claves |
|------|------------|--------|
| `resumen` | Índice de funciones | `intro`, `tarjetas` (`titulo`,`desc`) |
| `pasos` | Checklist numerado | `intro`, `pasos[]`, `nota`, `nota_titulo` |
| `captura` | Hay screenshot real | `parrafos[]`, `imagen`, `nota` |
| `mock_odoo` | No hay instancia / módulo no instalado | `parrafos[]`, `pasos[]`, `ruta`, `chrome_titulo`, `botones[]`, `campos` `[[et,val]]`, `nota`, `alto_mock` |
| `faq` | Dudas | `faqs` (`q`,`a`) |
| `rutas` | Hoja rápida | `intro`, `rutas` (`titulo`,`desc`) |
| `texto` | Solo párrafos | `lineas[]` o `parrafos[]` |

La portada se dibuja sola. No la pongas en `paginas`.

## Capturas de una instancia (preferidas)

Si el usuario da URL o el módulo ya está en JOSEDA / Abitare / JM:

1. Inventario en `ssh-servidores` (`hosts.md`). No pidas ni pegues contraseñas.
2. Entra con el navegador (cursor-ide-browser o browser-use). Flujo real: login → menú → acción.
3. Una captura por paso. Nombre `01_...png`, `02_...png`.
4. Recorta chrome ajeno (otra pestaña, chat). Se ve el menú de Odoo y el dato.
5. En el spec usa `"tipo": "captura"` y `"imagen": "01_lista.png"`.
6. Si un login/MFA te bloquea, **para** y pide al usuario la sesión. Mientras tanto usa `mock_odoo`.

No inventes capturas con IA que parezcan Odoo. O es foto real o es mock dibujado.

## Mock Odoo (si no hay capturas)

Botones y menús con el **string exacto** del XML (`Enviar gestión de cobro`, no “enviar mail”).
Ruta real: `Properties → Ventas → Gestión de Cuotas → Cuotas Abiertas`.

## Tono

- Equipo del cliente, no desarrollador. Cero “xpath”, “cron ir.cron”, “ACL”.
- Sí: rutas de menú, nombres de botón, qué hace un clic, qué queda apagado.
- FAQ al final. Una página de “ruta rápida” si el manual pasa de 6 páginas.

## QA visual (no saltar)

Tras `--preview`, mira portada, una página de pasos y cada captura/mock:

- Nada se solapa (títulos vs recuadros).
- El pie no tapa texto.
- Las capturas se leen (no miniatura ilegible).
- El cliente y la URL de la portada son los correctos.

Si algo choca, acorta párrafos o parte la página. El helper ya baja `y` en cada línea.

## Ejemplo mínimo

`scripts/ejemplo_spec.json` — córrelo si cambias el helper:

```powershell
python ...\manual_pdf.py --spec ...\ejemplo_spec.json --sin-descargas --preview
```
