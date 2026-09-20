# Vault 1Password SSH Implementation Plan

> **For agentic workers:** ejecutar en esta sesión (inline). No commitear: la skill no es un repo de producto y Kevin no pidió commit.

**Goal:** Dejar lista la skill `ssh-servidores` para usar 1Password como vault (local Agent + Cloud `op`) sin filtrar PEM al chat.

**Architecture:** Mapa alias→ítem sin secretos; script de subida por plantilla; wrapper Cloud que escribe la PEM a un temp y la borra; skill documenta el orden de backends.

**Tech Stack:** Python 3, OpenSSH de Windows, 1Password CLI `op`, PowerShell.

## Global Constraints

- Cadenas de usuario y errores en español.
- Nunca imprimir PEM, `.ppk`, contraseñas, `config.yaml` de Tabby ni `OP_SERVICE_ACCOUNT_TOKEN`.
- Vault: `SSH-Infra`. Secret de Cursor: `OP_SERVICE_ACCOUNT_TOKEN`.
- Hosts password no se automatizan.
- Drive no se toca.
- Servicio `ssh-agent` de Windows permanece Disabled.
- No commitear.

---

### Task 1: Mapa vault + tests

**Files:**
- Create: `scripts/vault_map.py`
- Create: `scripts/test_vault_map.py`

**Interfaces:**
- Produce: `VAULT_NOMBRE`, `item_para_pem()`, `item_para_alias()`, `es_host_password()`, `referencia_clave_privada()`, `aliases_password()`, `nombres_pem()`

- [x] Implementar mapa y tests
- [x] Correr `python scripts/test_vault_map.py`

### Task 2: Scripts op (subida, SSH Cloud, setup VM)

**Files:**
- Create: `scripts/subir_a_1password.py`
- Create: `scripts/ssh_via_op.py`
- Create: `scripts/setup_op_cloud.sh`

- [x] Subida sin echo de material
- [x] SSH Cloud con temp + `finally`
- [x] Setup Linux instala `op` oficial

### Task 3: Documentación de la skill

**Files:**
- Modify: `SKILL.md`
- Modify: `hosts.md` (nota de nombres de ítem)
- Create: `docs/GUIA-1PASSWORD.md`

- [x] Orden de backends y prohibiciones
- [x] Pasos humanos (cuenta, token en dashboard, no en el chat)
