# Recetas remotas desde PowerShell (Odoo / Postgres)

El agente local es Windows PowerShell + OpenSSH. Anidar comillas en `ssh <alias> "cmd -c '...'" ` **falla**. Toda consulta con SQL, `\d`, Python o comillas va **por stdin**.

En Cloud Agent (Linux) usa el wrapper, no `ssh tsheila`:

```bash
python3 ~/.cursor/skills/ssh-servidores/scripts/ssh_via_op.py tsheila -- sudo -u postgres psql -d tsheila
```

## SQL (psql)

```powershell
$sql = @'
SELECT id, name, code, active
FROM hr_salary_rule
WHERE code = 'Q2VACDIF2';
'@
$sql | ssh -o BatchMode=yes tsheila "sudo -u postgres psql -d tsheila"
```

Describe de tabla (nunca `psql -c '\d ...'` desde PowerShell: `\d` se come las comillas y Postgres intenta peer-auth como usuario `hr_salary_rule`):

```powershell
@'
\d hr_salary_rule
'@ | ssh -o BatchMode=yes tsheila "sudo -u postgres psql -d tsheila"
```

UPDATE largo: dollar-quoting de Postgres + here-string **simple** (`@'...'@`). Un solo `'` en literales SQL (`'draft'`). No uses `@"..."@` ni `''draft''`.

Salida ancha: `psql -A -t` o `-x`.

## Logs de Odoo

```powershell
ssh -o BatchMode=yes tsheila "sudo ls -lh /var/log/odoo/odoo-server.log"
ssh -o BatchMode=yes tsheila "sudo tail -c 2M /var/log/odoo/odoo-server.log | grep -a -E 'Q2VACDIF2|Wrong python|Codigo python' | tail -40"
```

No: `sudo grep -n PATRON /var/log/odoo/odoo-server.log` (34G+ en tsheila; `Binary file matches`; el comando no termina).

## Archivos y conf

```powershell
ssh -o BatchMode=yes tsheila "sudo grep -E '^(db_|logfile|addons_path|http_port|workers)' /etc/odoo-server.conf | grep -vE 'passwd|password'"
ssh -o BatchMode=yes tsheila "sed -n '1,80p' /odoo/odoo-server/addons/hr_contract/models/hr_employee.py"
```

No uses Read/Glob sobre `\\tsheila.lifterdo.com\odoo\...`.

## odoo-bin shell

```powershell
$py = @'
slip = env['hr.payslip'].browse(26538)
print(repr(slip.employee_id.first_contract_date), repr(slip.contract_id.date_start))
lines = env['hr.payslip']._get_payslip_lines(slip.contract_id.ids, slip.id)
print('lines', len(lines))
'@
$py | ssh -o BatchMode=yes tsheila "sudo -u odoo /odoo/odoo-server/odoo-bin shell -c /etc/odoo-server.conf -d tsheila --no-http --workers=0 --max-cron-threads=0"
```

- Timeout local >= 60–120s (arranca el registry).
- Metodo real: `_get_payslip_lines`. `get_payslip_lines` → AttributeError.
- No llames `compute_sheet` para probar una regla: borra/reescribe `line_ids`.

## Errores vistos (2026-08-27, tsheila / Q2VACDIF2)

| Sintoma | Causa | Que hacer |
|---|---|---|
| `unexpected EOF while looking for matching '"'` | PowerShell rompio el `-c` de ssh | stdin / here-string |
| `Peer authentication failed for user "hr_salary_rule"` / `"id,"` | `psql -c` recibio fragmentos, no SQL | pipe a `psql` sin `-c` |
| `extra command-line argument "name," ignored` | comillas de `SELECT id, name` se perdieron | idem |
| syntax error `''draft''` | here-string `@"..."@` dobleo comillas | usar `@'...'@` |
| `grep: /etc/odoo-server.conf: Permission denied` | falta sudo | `sudo grep` / `sudo cat` |
| `column "modules" does not exist` (ir_model_fields) | Odoo 14 no tiene esa columna | `\d ir_model_fields` antes de SELECT |
| `column "first_contract_date" does not exist` en `hr_employee` | campo compute, no stored | ORM o `hr_contract.date_start` |
| Read tool Permission denied en UNC | no hay share; es SSH | `ssh ... sed/cat` |
| grep log cuelga / `Binary file matches` | log 34G | `ls -lh` + `tail -c` + `grep -a` |
| `AttributeError: get_payslip_lines` | nombre viejo | `_get_payslip_lines` |
| UserError *Codigo python erróneo* en regla de nomina | `safe_eval` traga el traceback | reproducir con `_get_payslip_lines`; `False.month` si `first_contract_date` vacio (contratos `cancel`) |

Traducciones en tsheila: tanto *Wrong python code* como *Wrong python condition* salen como «Código python erróneo en la regla de salario %s (%s).» El mensaje **no** distingue condición vs importe.
