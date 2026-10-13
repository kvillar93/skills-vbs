\echo ##COND
\copy (select m.id, m.name, m.ref, dt.doc_code_prefix tipo, m.state, m.l10n_do_ecf_send_state, m.invoice_date, m.write_date, regexp_replace(coalesce(m.l10n_do_ecf_message_status,''),'\s+',' ','g') msg from account_move m left join l10n_latam_document_type dt on dt.id=m.l10n_latam_document_type_id where m.is_ecf_invoice and m.write_date >= '__DESDE__' and m.l10n_do_ecf_send_state in ('conditionally_accepted','delivered_refused','invalid','not_sent') order by m.id) to stdout csv header
\echo ##RECEP
\copy (select m.l10n_do_ecf_reception_state, count(*), left(regexp_replace(coalesce(m.l10n_do_ecf_reception_error,''),'\s+',' ','g'),220) err from account_move m where m.is_ecf_invoice and m.move_type in ('out_invoice','out_refund') and m.write_date >= '__DESDE__' and m.l10n_do_ecf_send_state in ('delivered_accepted','conditionally_accepted') group by 1,3 order by 2 desc) to stdout csv header
\echo ##RECEP_DET
\copy (select m.id, m.name, m.ref, p.name partner, m.l10n_do_ecf_reception_state, m.l10n_do_ecf_reception_attempts, m.l10n_do_ecf_reception_url, p.l10n_do_ecf_optional_url, left(regexp_replace(coalesce(m.l10n_do_ecf_reception_error,''),'\s+',' ','g'),400) err from account_move m join res_partner p on p.id=m.partner_id where m.is_ecf_invoice and m.move_type in ('out_invoice','out_refund') and m.write_date >= '__DESDE__' and m.l10n_do_ecf_reception_state in ('error','sent') order by m.id) to stdout csv header
\echo ##CHATTER
\copy (select coalesce(mm.subject,'(sin asunto)') asunto, count(*), count(distinct mm.res_id) from mail_message mm where mm.model='account.move' and mm.date >= '__DESDE__' and mm.message_type='notification' group by 1 order by 2 desc limit 15) to stdout csv header
\echo ##ACECF
\copy (select id, rnc_encf_ecf, estado, move_type, detalle_rechazo_ecf, create_date from aprobaciones_comerciales where create_date >= '__DESDE__' order by id) to stdout csv header
