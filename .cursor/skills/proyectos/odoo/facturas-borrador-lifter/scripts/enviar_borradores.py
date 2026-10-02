# Corre dentro de: odoo-bin shell -d lifter
# Confirma out_invoice en borrador, espera aceptacion DGII y envia el correo
# al cliente y a sus contactos hijos (misma regla que la automatizacion
# Account Invoice Send). SOLO_ID=<id> limita a una factura.
import os
import traceback

SOLO = os.environ.get("SOLO_ID", "").strip()


def enviar(move):
    template = env.ref("account.email_template_edi_invoice")
    ctx = {
        "active_model": "account.move",
        "active_ids": move.ids,
        "active_id": move.id,
        "default_model": "account.move",
        "default_res_id": move.id,
        "default_res_model": "account.move",
        "default_use_template": True,
        "default_template_id": template.id,
        "default_composition_mode": "comment",
        "mark_invoice_as_sent": True,
        "custom_layout": "mail.mail_notification_paynow",
        "force_email": True,
    }
    wizard = env["account.invoice.send"].with_user(2).with_context(ctx).create({
        "is_email": True,
        "is_print": False,
        "template_id": template.id,
    })
    wizard.onchange_template_id()
    destinatarios = move.partner_id.child_ids + move.partner_id
    wizard.partner_ids = destinatarios
    wizard.with_context(ctx).send_and_print_action()
    env.cr.commit()
    msg = env["mail.message"].search([
        ("model", "=", "account.move"),
        ("res_id", "=", move.id),
        ("message_type", "=", "comment"),
    ], order="id desc", limit=1)
    notifs = env["mail.notification"].search([("mail_message_id", "=", msg.id)])
    print(
        "ENVIO",
        move.id,
        move.name,
        move.ref,
        msg.email_from,
        [(n.res_partner_id.email, n.notification_status) for n in notifs],
        flush=True,
    )


domain = [("move_type", "=", "out_invoice"), ("state", "=", "draft")]
if SOLO:
    domain.append(("id", "=", int(SOLO)))
drafts = env["account.move"].search(domain, order="id")
print("PENDIENTES", drafts.ids, flush=True)
for move in drafts:
    try:
        move.action_post()
    except Exception as exc:
        env.cr.rollback()
        print("ERROR_POST", move.id, type(exc).__name__, exc, flush=True)
        continue
    env.cr.commit()
    move.invalidate_cache()
    print(
        "POSTED",
        move.id,
        move.name,
        move.ref,
        move.state,
        move.l10n_do_ecf_send_state,
        flush=True,
    )
    if move.l10n_do_ecf_send_state == "delivered_pending":
        try:
            move.get_track_id_status()
            env.cr.commit()
            move.invalidate_cache()
            print("RECHECK", move.id, move.l10n_do_ecf_send_state, flush=True)
        except Exception as exc:
            env.cr.rollback()
            print("ERROR_RECHECK", move.id, type(exc).__name__, exc, flush=True)
    if move.state == "posted" and move.l10n_do_ecf_send_state in (
        "delivered_accepted",
        "conditionally_accepted",
    ):
        try:
            enviar(move)
        except Exception as exc:
            env.cr.rollback()
            print("ERROR_MAIL", move.id, move.name, type(exc).__name__, exc, flush=True)
            traceback.print_exc()
    else:
        print(
            "NO_EMAIL",
            move.id,
            move.name,
            move.ref,
            move.state,
            move.l10n_do_ecf_send_state,
            flush=True,
        )
quedan = env["account.move"].search_count([
    ("move_type", "=", "out_invoice"),
    ("state", "=", "draft"),
])
print("BORRADORES_RESTANTES", quedan, flush=True)
