---
name: revision-ecf
description: >-
  Revisión periódica de facturación electrónica e-CF (DGII) en los servidores
  Odoo de clientes: aceptaciones condicionales y rechazos nuevos, envío del
  e-CF al cliente (acuse ARECF), recepción de e-CF y aprobaciones comerciales
  (ACECF), errores del log. Clasifica datos vs código, corrige quirúrgicamente
  en los 4 repos (addonsCE14, addonsCE16, addonsEP14, addonsEP16) sin campos
  nuevos, commit/push y, si el chat lo pide, pull + restart_odoo con
  verificación. Usar cuando pidan "revisa los servers de e-CF", "pasa por las
  instancias", "revisa aceptaciones condicionales", "revisa envíos de recibos a
  clientes" o una revisión de este estilo.
---

# Revisión e-CF en servidores (DGII)

Skills relacionadas: `ssh-servidores` (SSH, recetas psql/stdin, `restart_odoo` en dos pasos).
Reglas que mandan: `addonsEP16/.cursor/rules/no-subir-servidor.mdc` (desplegar **solo** si el chat lo pide).

## Reglas de oro

- **Sin campos nuevos** ni vistas/datos: solo funciones existentes o funciones nuevas. Así basta reiniciar Odoo, sin `-u`.
- **Quirúrgico** y en los **4 repos** (CE14, CE16, EP14, EP16). CE16 ≈ EP16 en `l10n_do_ecf_*`; CE14 y EP14 difieren: adaptar, no copiar.
- **Trabajar sobre `origin/master`**: si la carpeta del repo está en una rama `cursor/*` (del usuario), usar `git worktree add ../_ecf_wt/<repo> master`; nunca commitear en su rama. CE16 es sparse checkout: `git sparse-checkout add <modulo>`.
- Commits en español, terminando con `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; identidad `-c user.name="Kevin Villar" -c user.email="kvillar@lifterdo.com"` (EP14 no tiene identidad local). Mensaje en archivo **dentro de `Projects`** (rutas largas fallan en git).
- Scripts temporales en una carpeta propia (scratchpad), **no en `/tmp`** compartido: otra sesión puede pisarlos.
- Solo lectura en servidores para revisar (`SELECT`, `tail -c`, `git fetch`). Nunca `grep` el log completo.
- No esquivar protecciones de terceros (Cloudflare "Just a moment", 403 bot): se reporta.

## Instancias (base de datos)

| Alias SSH | Repo | BD | Notas |
|---|---|---|---|
| permesa | addonsCE14 | permesa | |
| gti | addonsCE14 | gtiseguridad | |
| rm-tech | addonsCE14 | rm | commits de merge locales → pull **merge** |
| proyesdo | addonsCE14 | proyesdo | |
| infracero | addonsCE14 | infracero | |
| jm-ss | addonsEP16 | jm | tiene `.bak` sin versionar (no chocan) |
| aromelia | addonsEP16 | aromelia | |
| joseda | addonsEP16 | joseda (+ alofoke) | sin `l10n_do_ecf_reprocess` |

Ampliar la lista si el usuario agrega instancias. Inventario completo: `ssh-servidores/hosts.md`.

## Paso 1 — Estado y datos (solo lectura)

`DESDE` = fecha UTC del último despliegue (ej. `2026-10-08 04:10`). Scripts en `scripts/`:

```bash
sed "s/__DESDE__/$DESDE/g" scripts/revision.sql | ssh -o BatchMode=yes <alias> "sudo -u postgres psql -X -q -d <bd>"
sed "s/__DESDE__/$DESDE/g" scripts/recepcion.sql | ssh ... psql      # envío al cliente por último intento real
sed "s/__DESDE__/$DESDE/g" scripts/max_intentos.sql | ssh ... psql   # causa de fondo de "Máximo de intentos (3)"
ssh <alias> "bash -s -- '$DESDE'" < scripts/log_errores.sh
```

- `revision.sql` devuelve secciones `##COND` (condicionales/rechazos con el mensaje DGII), `##RECEP`, `##RECEP_DET`, `##CHATTER`, `##ACECF`.
- **Filtrar por `fechaRecepcion` del mensaje DGII ≥ despliegue**: `write_date` incluye facturas viejas tocadas por pagos u otros.
- Para envíos a clientes, usar `recepcion.sql` (por `l10n_do_ecf_reception_last_attempt`), no `write_date`.
- Si `revision.sql` da error de columna `l10n_do_ecf_reception_state`, la instancia no tiene `reprocess` (no aplica envío a clientes).

## Paso 2 — Clasificar

**Datos o configuración (no se corrigen en código, se reportan):**
- 1385/1383/1503: RNC/cédula del comprador inválido, inexistente o con dígito verificador malo; pasaporte como RNC (cliente con país DO).
- 1209 / 75 "secuencia ya utilizada", 615 "NCF anulado/rechazado" o "no puede ser mayor al balance" (origen ya acreditado), 135/145 secuencias, 004 transitorio DGII, 645 código 2 con monto.
- TipoIngresos en E34 que anulan E41/E43/E47: la documentación DGII no define el valor; no tocar sin norma.
- ARECF Estado=1 motivo 1/2 de algunos receptores (especificación/firma propia del receptor), 401/403 con credenciales del receptor, 404/410/500/503 del receptor, servicios caídos, "RNC del token no corresponde al emisor", Cloudflare.
- `No se pudo obtener directorio para RNC X` → el cliente no es receptor electrónico (correcto `not_required`).

**Indicios de código (investigar y corregir):**
- Mismo error en muchas facturas o en varios clientes del mismo tipo de e-CF.
- Errores de Python en el log de módulos `l10n_do_ecf_*`, controladores `/fe/recepcion` o `/fe/aprobacioncomercial`.
- Reintentos sin límite (intentos en 0 con estado error), mensajes repetidos en el chatter.
- URLs mal armadas (ruta duplicada), formatos de respuesta no previstos (JSON vs XML, texto JSON con XML).

Referencias DGII (en `auditoria-ecf-2026-10/docs`): Informe Técnico e-CF, Descripción Técnica Servicios DGII y Emisores Electrónicos. Modelo: emisor envía e-CF a DGII y al receptor (`/fe/recepcion/api/ecf`, responde ARECF); la **aprobación comercial (ACECF) la emite el receptor**. Motivos ARECF: 1 especificación, 2 firma, 3 envío duplicado (= ya lo tenía → recibido), 4 RNC comprador no corresponde.

## Paso 3 — Corregir

1. Ubicar la función en los 4 repos (`git grep` sobre `origin/master`); comparar versiones.
2. Reemplazos exactos con conteo (script Python que falle si no calza); respetar CRLF.
3. `python -m py_compile` de cada archivo y borrar los `__pycache__/*.cpython-312.pyc` creados.
4. Probar la lógica nueva con datos reales (respuestas, URLs, XML) en un snippet.
5. Commit por repo (un tema por commit) y `push origin master` si el usuario lo pidió o lo pidió en el chat.

## Paso 4 — Desplegar (solo si el chat lo pide)

Por servidor, en orden y deteniéndose ante cualquier riesgo:

```bash
ssh <alias> "bash -s" < scripts/precheck.sh                       # fetch + choques con archivos sin versionar
ssh <alias> "python3 - /odoo/custom/addons/<repo> <bd>" < scripts/remote_columnas.py   # campos nuevos sin columna
```
- Riesgo = línea que **empieza** con `CHOQUE|` o `FALTA|` (ojo: `FIN_CHOQUES` no es choque). Si hay riesgo, no desplegar y reportar.
- Revisar **todas** las BD del servidor (ej. joseda + alofoke).

```bash
ssh <alias> "bash -s -- ff" < scripts/pull.sh        # 'merge' en rm-tech
ssh <alias> "printf '%s\n' 'shopt -s expand_aliases' 'restart_odoo' > /tmp/reiniciar.sh"
ssh <alias> "bash -i /tmp/reiniciar.sh"
ssh <alias> "bash -s -- '<inicio UTC>'" < scripts/verificar_odoo.sh   # servicio, HTTP 200, errores desde el reinicio
```
Solo reiniciar si `SINTAXIS_OK|1`. Tras desplegar, activar si hace falta el cron "Enviar Facturas ECF Aprobadas a Clientes" (no el de "Aprobación Comercial", que no aplica al emisor).

El cron "Enviar Facturas ECF Aprobadas a Clientes" va **cada 15 minutos** y el código espera 15 min (840 s) entre intentos, máximo 3. El data es `noupdate`: en bases existentes ajustar `ir_cron` (`interval_number=15`) por SQL.

## Paso 5 — Reporte

Tabla por servidor (commit antes/después, estado, errores), qué se corrigió (con commit por repo), qué es de datos/terceros y qué quedó sin desplegar y por qué. Ser explícito si algo no se verificó.
