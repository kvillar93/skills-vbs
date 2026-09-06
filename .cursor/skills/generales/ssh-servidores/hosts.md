# Inventario SSH importado desde Tabby

Alias para `ssh <alias>`. Las claves PEM viven en `~/.ssh/` (nunca en este archivo).
En 1Password el vault es `SSH-Infra`: el título del **documento** PEM es el mismo que la columna **Clave PEM**.
En Cloud Agents `ssh_via_op.py` usa Host/Usuario/Puerto de esta tabla (no hace falta `~/.ssh/config`).
Los hosts `password` tienen ítem Login con el alias canónico (`aurora`, `backup-sti`, …) y **no se automatizan**.

| Alias | Nombre Tabby | Host | Usuario | Puerto | Auth | Clave PEM |
|---|---|---|---|---|---|---|
| `75-grados-vbsolutions` (75g-vbs) | 75 Grados VBSOLUTIONS | `75g.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `abitare` | ABITARE | `abitare.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `abudo` | abudo | `abudo.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `ajp` | AJP | `ajp.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `alofoke` | ALOFOKE | `alofoke.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `alter-legal` | ALTER LEGAL | `alterlegal.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `ashton-school` | ASHTON SCHOOL | `ashtonschool.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `ashton-school-santo-domingo` (ashtonschool-sd) | ASHTON SCHOOL SANTO DOMINGO | `tas.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `baralaktech` | baralaktech | `baralaktech.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `capellier` | CAPELLIER | `capellier.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `cgdg` | CGDG | `cgdg.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `circe` | CIRCE | `circe.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `clinia` | CLINIA | `clinia.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `cmp` | CMP | `cmp.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `collado` | COLLADO | `collado.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `csi` | CSI | `csi.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `encf-vbsolutions` (encf-vbs) | ENCF VBSOLUTIONS | `encf.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `fiducaribe` | Fiducaribe | `fiducaribe.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `ica-vanessa` | ICA VANESSA | `ica.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `ifsolutions` | IFSOLUTIONS | `ifsolutions.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `inc` | INC | `inc.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `incomendam` | Incomendam | `incomendan.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `inecar` | INECAR | `inecar.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `jc` | JC | `jc.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `jdg` | JDG | `jdg.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `jm-ss` | JM SS | `jm.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `joseda` | JOSEDA | `joseda.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `minicompsa` | MINICOMPSA | `minicompsa.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `nakajima` | NAKAJIMA | `nakajima.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `nk` | NK | `nk.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `nmp` | NMP | `nmp.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `nmp-guud-store` (nmp-guud) | NMP (GUUD STORE) | `nmp.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `odoo-test-vbsolu` | ODOO TEST (VBSOLU) | `test.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `odoo-test-vbs` | ODOO TEST VBS | `test.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `odootest` | ODOOTEST | `odootest.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `oh-farma` | OH FARMA | `ohfarma.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `oppein` | OPPEIN | `oppein.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `permesa` (perm) | PERMESA | `permesa.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `petronam` | PETRONAM | `petronan.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `proidec` | PROIDEC | `proidec.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `rca` | RCA | `rca.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `recubre` | RECUBRE | `recubre.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `rm-tech` | RM TECH | `rm.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `saas-vbs` | SAAS VBS | `saas.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `selite` | SELITE | `selite.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `soluciones-contables` | Soluciones Contables | `sc.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `sti-vb` | STI VB | `sti.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `tgr` | TGR | `tgr.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `umbra` | UMBRA | `umbragroup.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `umbra-finance-copy` (umbra-finance) | UMBRA Finance copy | `umbrafinance.vbsolutions.app` | ubuntu | 22 | publicKey | `umbrafinance` |
| `umbratest` | UMBRATEST | `umbratest.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `vbs-hermes` | VBS HERMES | `44.217.48.118` | ubuntu | 22 | publicKey | `vbsolutions` |
| `vbs-hermes-chatwoot` | VBS HERMES-CHATWOOT | `54.144.100.40` | ubuntu | 22 | publicKey | `vbsolutions` |
| `vbsolutions` | VBSOLUTIONS | `vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `visionary` | VISIONARY | `vs.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `vvl` | VVL | `vvl.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `vvl-ppk` | VVL PPK | `vvl.vbsolutions.app` | ubuntu | 22 | publicKey | `vvl` |
| `valdesia-water-company-vwc` (vwc) | VALDESIA WATER COMPANY (VWC) | `vwc.vbsolutions.app` | ubuntu | 22 | publicKey | `vbsolutions` |
| `75-grados` (75grados) | 75 Grados | `75grados.lifterdo.com` | ubuntu | 22 | publicKey | `odoo_xolver` |
| `acso` | ACSO | `acso.lifterdo.com` | ubuntu | 22 | publicKey | `odoo_xolver` |
| `adl` | ADL | `adl.lifterdo.com` | ubuntu | 22 | publicKey | `odoo_xolver` |
| `aromelia` | AROMELIA | `aromelia.lifterdo.com` | ubuntu | 22 | publicKey | `odoo_xolver` |
| `atlantic-shutters` | ATLANTIC SHUTTERS | `atlanticshutters.lifterdo.com` | ubuntu | 22 | publicKey | `odoo_xolver` |
| `encf-lifter` | ENCF LIFTER | `encf.lifterdo.com` | ubuntu | 22 | publicKey | `odoo_xolver` |
| `farmacia-vip` (farmaciasvip) | Farmacia VIP | `farmaciasvip.lifterdo.com` | ubuntu | 22 | publicKey | `odoo_xolver` |
| `go-transfer` | GO TRANSFER | `gotransfer.lifterdo.com` | ubuntu | 22 | publicKey | `odoo_xolver` |
| `gti` (gtiseguridad) | GTI | `gtiseguridad.lifterdo.com` | ubuntu | 22 | publicKey | `odoo_xolver` |
| `lifter` | LIFTER | `lifterdo.com` | ubuntu | 22 | publicKey | `odoo_xolver` |
| `newmed` | NEWMED | `newmed.lifterdo.com` | ubuntu | 22 | publicKey | `odoo_xolver` |
| `perfilmar` | PERFILMAR | `perfilmar.lifterdo.com` | ubuntu | 22 | publicKey | `odoo_xolver` |
| `plastivo` | PLASTIVO | `erp.plastivord.com` | ubuntu | 22 | publicKey | `odoo_xolver` |
| `qtek` | QTEK | `qtek.lifterdo.com` | ubuntu | 22 | publicKey | `odoo_xolver` |
| `ribo` | RIBO | `ribo.lifterdo.com` | ubuntu | 22 | publicKey | `odoo_xolver` |
| `saas` (saas-lifter) | SAAS | `saas.lifterdo.com` | ubuntu | 22 | publicKey | `odoo_xolver` |
| `salud-integral` | SALUD INTEGRAL | `saludintegral.lifterdo.com` | ubuntu | 22 | publicKey | `odoo_xolver` |
| `ssh-tercero-stocaklu` (stockalu-tercero) | SSH TERCERO STOCAKLU | `stockalu.lifterdo.com` | tercero | 22 | password | `—` |
| `stockalu` | STOCKALU | `stockalu.lifterdo.com` | ubuntu | 22 | publicKey | `externo` |
| `tsheila` | TSHEILA | `tsheila.lifterdo.com` | ubuntu | 22 | publicKey | `odoo_xolver` |
| `xolver` | XOLVER | `erp.xolver.com` | ubuntu | 4525 | publicKey | `odoo_xolver` |
| `bmcvmod` | bmcvmod | `34.66.100.94` | kvillar | 22 | publicKey | `NO CONVERTIDA` |
| `bmcvmod-test` | bmcvmod test | `34.57.162.99` | kvillar | 22 | publicKey | `NO CONVERTIDA` |
| `epx` | EPX | `50.19.192.35` | ubuntu | 22 | publicKey | `OdooEPX` |
| `florespax-shinhyo` | Florespax Shinhyo | `florespax.com` | ubuntu | 22 | publicKey | `fpaxv3` |
| `infracero` | INFRACERO | `3.218.206.53` | ubuntu | 22 | publicKey | `vbsolutions` |
| `minigp` | Minigp | `minigpperformance.com` | ubuntu | 22 | publicKey | `vbsolutions` |
| `proyesdo` | PROYESDO | `34.233.241.242` | ubuntu | 22 | publicKey | `vbsolutions` |
| `tsheila-test` | TSHEILA TEST | `ec2-13-59-19-59.us-east-2.compute.amazonaws.com` | ubuntu | 22 | publicKey | `odoo_xolver` |
| `aurora` | Aurora | `167.71.168.215` | kvillar | 22000 | password | `—` |
| `backup-sti` | Backup STI | `135.119.168.29` | desarrollador | 22 | password | `—` |
| `odoo-quickbooks-jean` | ODOO QUICKBOOKS JEAN | `167.172.242.143` | — | 22 | password | `—` |
| `power-bi-server` | Power BI Server | `34.205.70.32` | Administrator | 22 | password | `—` |
| `sti-nuevo-server` (sti-nuevo) | STI NUEVO SERVER | `172.206.64.101` | stiadmin | 22 | password | `—` |
