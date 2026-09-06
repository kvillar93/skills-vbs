---
name: odoo-module-icon
description: Genera iconos de módulos Odoo 16 con IA (GenerateImage), nunca a mano ni con SVG/código. Usar al crear un módulo nuevo, al pedir un icono, icon.png, static/description, o al clonar un módulo en addonsEP16/CE16/CE14.
---

# Iconos de módulos Odoo 16

## Obligatorio

- **Nunca** dibujar el icono con código (SVG escrito a mano, Pillow, Inkscape, FontAwesome, paths). El glifo y la baldosa salen de **IA**.
- **Siempre** generar el gráfico con `GenerateImage` (IA).
- Destino: `nombre_modulo/static/description/icon.png`
- Odoo 16 (`get_module_icon`) busca **solo** `icon.png`, no SVG.
- Tamaño final: **140×140 px** PNG (igual que Community y Enterprise).
- Si el módulo existe en varios árboles (`addonsEP16`, `addonsCE16`, `addonsCE14`), copiar el mismo PNG a todos.
- Tras generar: **esquinas transparentes** (alpha 0) y **sombra larga** del glifo. Verificar píxeles de esquina antes de dar por cerrado.

## Cómo son los iconos oficiales

Referencias a pasar SIEMPRE en `reference_image_paths`:

- `/odoo/odoo-server/addons/purchase/static/description/icon.png` — **radio de esquina + intensidad del brillo** (Community)
- `/odoo/odoo-server/addons/stock/static/description/icon.png` — misma baldosa y sombra
- `/odoo/enterprise/addons/iot/static/description/icon.png` — solo el *tipo* de bisel; **no** copiar su brillo fuerte ni el corte diagonal marcado
- `/odoo/odoo-server/addons/account/static/description/icon.png`
- `/odoo/odoo-server/addons/mrp/static/description/icon.png`
- `/odoo/enterprise/addons/account_asset/static/description/icon.png`

Estructura visual (para el prompt de IA, no para dibujarla):

1. Baldosa **casi cuadrada** con radio **modesto** como `purchase`/`stock` (rectángulo ligeramente redondeado). **Prohibido** squircle, pebble o esquinas tipo icono iOS. El postproceso aplica la máscara alpha de `purchase` para fijar el radio oficial.
2. Degradado de **un solo color de familia** según el dominio del módulo.
3. **Brillo sutil (Community, no halo):** filete fino y apagado arriba e izquierda; abajo y derecha un poco más oscuros. **No** anillo blanco grueso, **no** burbuja de cristal, **no** destello diagonal fuerte tipo IoT.
4. Glifo **blanco** centrado, geométrico, 1–2 formas, trazo grueso uniforme.
5. **Sombra larga a la izquierda:** copia plana del glifo, tinte más oscuro de la baldosa (no negro puro), **45° hacia abajo-izquierda**. Nunca a la derecha.
6. **Fuera de la baldosa: transparencia total.** Prohibido negro/gris en las esquinas. Prohibido trazo negro alrededor.
7. **Sin texto**, letras, logos, fotorealismo ni watermark.

## Color de fondo según el dominio

Elegir el degradado por el **tema de la app**, no un teal genérico para todo. No copiar el color de un módulo oficial vecino.

| Dominio del módulo | Familia de color | Ejemplos de glifo |
|--------------------|------------------|-------------------|
| Salud, clínica, odontología, higiene | Teal / cian | diente, cruz, estetoscopio |
| Naturaleza, agronomía, medio ambiente, calidad verde | Verde | hoja, planta, árbol |
| Energía, electricidad, iluminación | Amarillo / ámbar | rayo, sol, bombilla |
| Combustible, peligro, alertas, incendios | Rojo | surtidor, llama, tanque |
| Agua, océano, frío, logística húmeda | Azul | gota, ola |
| Finanzas, facturación, tesorería | Terracota / naranja tierra | documento, moneda (evitar si ya está `account`) |
| Inventario, almacén | Burdeos | caja (evitar si ya está `stock`) |
| Compras, proveedores | Azul grisáceo | documento (evitar si ya está `purchase`) |
| Personas, RR. HH., comunidad | Teal oscuro / cian profundo | siluetas (evitar si ya está `hr`) |
| Fabricación, taller | Verde menta | engranaje, llave (evitar si ya está `mrp`) |
| Proyectos, conocimiento, flota | Índigo / violeta apagado | tablero, libro, vehículo |
| POS, hardware, IoT | Gris | terminal, dispositivo |

Si el dominio no encaja, elegir una familia distinta a los módulos ya instalados en el mismo menú Apps.

## Prompt de generación

`aspect_ratio`: `1:1`. `filename`: `icon.png`.

Incluir en `description` (en inglés, para la IA de imagen):

- “Odoo 16 Community Apps icon. Match the SMALL corner radius of the attached purchase/stock icons — slightly rounded rectangle, NOT a squircle, NOT iOS-round”
- “SUBTLE bezel like purchase/stock: faint light rim on top and left only, slightly darker bottom/right. NO thick white halo, NO strong glass bubble, NO heavy diagonal gloss”
- Tile color: **[familia del dominio]**
- White geometric glyph: **[pictograma]**
- “Long flat shadow of the glyph 45° toward BOTTOM-LEFT (left side), darker shade of the same tile color, sharp. Never shadow to the right”
- “Transparent PNG corners (alpha 0), no black outside the tile, no outline, no text, no watermark”
- Primera referencia: `purchase` y `stock` (forma, radio, brillo sutil, sombra). IoT solo como pista de bisel, no de intensidad.

## Después de GenerateImage (obligatorio)

La IA suele pintar las esquinas de **negro opaco**. Eso se ve como “bordes negros” en el menú Apps. Corregirlo así:

1. Redimensionar el PNG generado a **140×140** (LANCZOS).
2. **Aplicar la máscara alpha** de un icono oficial Odoo 16 (`purchase` o `account`, 140×140) sobre el RGB generado: las esquinas quedan transparentes con el mismo radio. No dibujar el glifo ni la baldosa con Pillow; solo copiar el canal alpha oficial.
3. Si quedan píxeles casi negros (R,G,B < 18) con alpha 255 en el margen, pasarlos a alpha 0.
4. Guardar en `static/description/icon.png`.
5. **Verificar** que `(0,0)`, `(139,0)`, `(0,139)` y `(139,139)` tienen **alpha 0**. Si no, repetir el paso 2.
6. No dejar el asset solo en la carpeta de Cursor.
7. No crear `icon.svg` a mano como sustituto.

Ejemplo de postproceso (solo recorte + máscara oficial, **no** dibujar el glifo).  
**No** pintar de transparente todos los píxeles blancos: el glifo es blanco y se destruiría.

```python
from collections import deque
from PIL import Image

src = Image.open('GENERADO.png').convert('RGB')
px, w, h = src.load(), *src.size

def es_fondo(r, g, b):
    if r < 22 and g < 22 and b < 22:
        return True
    if r > 230 and g > 230 and b > 230:
        return True
    return abs(r - g) < 14 and abs(g - b) < 14 and r > 200

seen = [[False] * w for _ in range(h)]
q = deque([(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)])
for x, y in list(q):
    seen[y][x] = True
while q:
    x, y = q.popleft()
    if not es_fondo(*px[x, y]):
        continue
    for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
        if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx]:
            seen[ny][nx] = True
            q.append((nx, ny))

xs = [x for y in range(h) for x in range(w) if not es_fondo(*px[x, y])]
ys = [y for y in range(h) for x in range(w) if not es_fondo(*px[x, y])]
# Inset mínimo: un inset grande recorta el filete sutil del borde
inset = max(4, int(0.01 * (max(xs) - min(xs))))
minx, maxx = min(xs) + inset, max(xs) - inset
miny, maxy = min(ys) + inset, max(ys) - inset
side = max(maxx - minx + 1, maxy - miny + 1)
cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
x0, y0 = int(cx - side / 2), int(cy - side / 2)
crop = src.crop((x0, y0, x0 + side, y0 + side)).resize((140, 140), Image.Resampling.LANCZOS).convert('RGBA')
mask = Image.open('/odoo/odoo-server/addons/purchase/static/description/icon.png').convert('RGBA').split()[-1]
r, g, b, _a = crop.split()
rp, gp, bp, mp = r.load(), g.load(), b.load(), mask.load()
for y in range(140):
    for x in range(140):
        if mp[x, y] == 0:
            rp[x, y] = gp[x, y] = bp[x, y] = 0
out = Image.merge('RGBA', (r, g, b, mask))
out.save('nombre_modulo/static/description/icon.png')
```

## Pictogramas (ejemplos)

- Odontología: molar **sólido relleno** (silueta blanca, no contorno hueco), con un relieve plano suave (brillo arriba-izquierda); 1–2 raíces; sin texto.
- Liquidaciones aduanales: documento con esquina doblada + sello de aduana.
- Liquidaciones de activos: documento + edificio/activo fijo.
- Inventario: caja/ palé isométrico simple.
- Solo un concepto; no saturar.
