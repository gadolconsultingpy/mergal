import base64
import datetime
from odoo import api, models, fields, _
from odoo.exceptions import UserError
import logging
import jinja2

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    sifen_state = fields.Selection(
            [
                ('skip', "Skip"),
                ('pending', "Pending"),
                ('queue', "In Queue"),
                ('sent', "Sent in Batch"),
                ('approved', "Approved"),
                ('rejected', 'Rejected'),
                ('cancel', 'Cancelled'),
                ('invalid', 'Invalidated'),
            ], default='pending', string="SIFEN State", copy=False, tracking=True
    )
    sifen_state_code = fields.Char("SIFEN State Code", copy=False, tracking=True)
    sifen_state_message = fields.Text("SIFEN State Message", copy=False, tracking=True)
    sifen_authorization = fields.Char("SIFEN Authorization", copy=False, tracking=True)
    sifen_send_mode = fields.Char("SIFEN Send Mode", compute='_compute_sifen_send_mode')
    edi_document_sent = fields.Boolean("EDI Document Sent", default=False, tracking=True)
    # EDI
    edi_event_qty = fields.Integer('EDI Events Qty', compute='_compute_edi_event_qty')
    edi_batch_qty = fields.Integer('EDI Batch Qty', compute='_compute_edi_batch_qty')
    cancellation_event_qty = fields.Integer('Cancelation Events Qty', compute='_compute_cancellation_event_qty')
    nomination_event_qty = fields.Integer('Nomination Events Qty', compute='_compute_nomination_event_qty')

    def open_edi_events(self):
        event_ids = self.env['edi.event'].search(
                [
                    ('res_model', '=', self._name), ('res_id', '=', self.id)
                ]
        )
        if not event_ids:
            return
        # for eve in event_ids:
        #     print("EVENTS", eve.id, eve.name)
        action = {'type'     : 'ir.actions.act_window',
                  'name'     : _('EDI Events'),
                  'res_model': 'edi.event'}
        if len(event_ids) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = event_ids.id
        elif len(event_ids) > 1:
            action['view_mode'] = 'list,form'
            action['domain'] = [('id', 'in', event_ids.ids)]
        return action

    def open_edi_batch(self):
        query = "SELECT edi_batch_id "
        query += "FROM account_move_edi_batch_rel "
        query += "WHERE account_move_id = %s " % (self.id)
        self._cr.execute(query)
        batch_ids = [x['edi_batch_id'] for x in self._cr.dictfetchall()]
        action = {'type'     : 'ir.actions.act_window',
                  'name'     : _('EDI Batch'),
                  'res_model': 'edi.batch'}
        if not batch_ids:
            return
        if len(batch_ids) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = batch_ids[0]
        elif len(batch_ids) > 1:
            action['view_mode'] = 'list,form'
            action['domain'] = [('id', 'in', [x for x in batch_ids])]
        return action

    def open_cancellation_events(self):
        event_ids = self.env['edi.document.cancel'].search(
                [
                    ('invoice_id', '=', self.id)
                ]
        )
        if not event_ids:
            return
        action = {'type'     : 'ir.actions.act_window',
                  'name'     : _('Cancellation Events'),
                  'res_model': 'edi.document.cancel'}
        if len(event_ids) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = event_ids.id
        elif len(event_ids) > 1:
            action['view_mode'] = 'list,form'
            action['domain'] = [('id', 'in', event_ids.ids)]
        return action

    def open_nomination_events(self):
        event_ids = self.env['edi.document.nomination'].search(
                [
                    ('invoice_id', '=', self.id)
                ]
        )
        if not event_ids:
            return
        action = {'type'     : 'ir.actions.act_window',
                  'name'     : _('Nomination Events'),
                  'res_model': 'edi.document.nomination'}
        if len(event_ids) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = event_ids.id
        elif len(event_ids) > 1:
            action['view_mode'] = 'list,form'
            action['domain'] = [('id', 'in', event_ids.ids)]
        return action

    def _compute_cancellation_event_qty(self):
        for rec in self:
            rec.cancellation_event_qty = self.env['edi.document.cancel'].search_count(
                    [('invoice_id', '=', rec.id)])

    def _compute_nomination_event_qty(self):
        for rec in self:
            rec.nomination_event_qty = self.env['edi.document.nomination'].search_count(
                    [('invoice_id', '=', rec.id)])

    def _compute_edi_event_qty(self):
        for rec in self:
            rec.edi_event_qty = self.env['edi.event'].search_count(
                    [('res_model', '=', self._name), ('res_id', '=', rec.id)])

    def _compute_edi_batch_qty(self):
        for rec in self:
            query = "SELECT COUNT(edi_batch_id) cnt "
            query += "FROM account_move_edi_batch_rel "
            query += "WHERE account_move_id = %s " % (rec.id)
            self._cr.execute(query)
            rec.edi_batch_qty = self._cr.dictfetchall()[0]['cnt']

    def _compute_sifen_send_mode(self):
        for rec in self:
            rec.sifen_send_mode = "de"
            setting = self.env['res.config.custom'].search([('company_id', '=', rec.company_id.id)])
            if setting:
                if setting.invoice_batch:
                    rec.sifen_send_mode = 'batch'

    def sifen_procedure(self, procedure='sifen.account.move.send'):
        if self.sifen_environment == 'X':
            _logger.info("SIFEN Environment is X - Skipping Procedure: %s" % (procedure))
            return
        self.env['edi.procedure'].run_procedure(record=self, procedure='sifen.account.move.check')
        ctx_proc = self.env.context.get('edi_procedure', procedure)
        self.env['edi.procedure'].run_procedure(record=self, procedure=ctx_proc)

    def button_edi_cancel(self):
        wizard = self.env['account.move.cancel.wizard'].create({'invoice_id': self.id})
        return {
            'type'     : 'ir.actions.act_window',
            'name'     : _("Cancellation Reason"),
            'view_mode': 'form',
            'target'   : 'new',
            'res_model': 'account.move.cancel.wizard',
            'res_id'   : wizard.id
        }

    @api.model
    def _cron_edi_send(self):
        companies = self.env['res.company'].search([('sifen_environment', '!=', 'X')])
        for comp in companies:
            config = self.env['res.config.custom'].get_company_custom_config(company_id=comp.id)
            if not config:
                continue
            date_limit = fields.Date.context_today(self) + datetime.timedelta(days=-config.edi_delayed_send_days)
            # Pending Invoices
            invoices = self.env['account.move'].search(
                    [
                        ('company_id', '=', comp.id),
                        ('invoice_date', '>=', date_limit),
                        ('state', '=', 'posted'),
                        ('move_type', 'in', ['out_invoice', 'out_refund']),
                        ('sifen_state', '=', 'pending')
                    ], order="invoice_date, name, id "
            )
            for inv in invoices:
                setting = self.env['res.config.custom'].search([('company_id', '=', inv.company_id.id)])
                if not setting:
                    msg = _("Setting for Send Invoice Missing")
                    raise UserError(msg)
                _logger.info("Procesing Invoice: %s" % (inv.name))
                if not setting.invoice_batch:
                    inv.with_context(edi_procedure='sifen.account.move.prepare').sifen_procedure()
                else:
                    inv.with_context(edi_procedure='sifen.account.move.batch.prepare').sifen_procedure()
            # Invoices for Consult
            invoices = self.env['account.move'].search(
                    [
                        ('company_id', '=', comp.id),
                        ('state', '=', 'posted'),
                        ('move_type', 'in', ['out_invoice', 'out_refund']),
                        ('sifen_state', '=', 'sent')
                    ], order="invoice_date, name, id "
            )
            for inv in invoices:
                setting = self.env['res.config.custom'].search([('company_id', '=', inv.company_id.id)])
                if not setting:
                    msg = _("Setting for Send Invoice Missing")
                    raise UserError(msg)
                _logger.info("Processing Invoice: %s" % (inv.name))
                inv.with_context(edi_procedure='sifen.account.move.consult').sifen_procedure()

    def _post(self, soft=True):
        for rec in self:
            config = rec.env['res.config.custom'].get_company_custom_config(company_id=rec.company_id.id)
            if not config:
                msg = _("Missing Additional Parameters")
                raise UserError(msg)
            if rec.invoice_date < config.edi_start_date:
                rec.sifen_state = 'skip'
        return super(AccountMove, self)._post(soft=soft)

    def action_post(self):  # OK
        if self.sifen_environment == 'X':
            _logger.info("SIFEN Environment is X - Skipping action_post")
        else:
            for rec in self:
                rec.env['edi.procedure'].run_procedure(record=rec, procedure='sifen.account.move.check')
        return super(AccountMove, self).action_post()

    def send_edi_document(self):
        if self.sifen_environment == 'X':
            _logger.info("SIFEN Environment is X - Skipping send_edi_document")
            return
        if self.edi_document_sent:
            return
        if self.sifen_state != 'approved':
            return

        # force server init
        config = self.env['res.config.custom'].get_company_custom_config(company_id=self.company_id.id)
        if config.edi_send_mode == 'disable':
            _logger.info("SEND MAIL DISABLED")
            return

        template = self.env['mail.template'].browse(config.edi_email_template_id.id)

        # report_action = self.env.ref('l10n_py_edi.account_einvoice_action')
        report_action = config.edi_report_action
        if not config.edi_report_action:
            return

        # Addressee Policy
        if config.edi_send_mode == 'test':
            email_to = config.test_email
            _logger.info("SENDING MAIL TEST MODE: %s" % (email_to))
        elif config.edi_send_mode == 'production':
            if self.partner_id.email:
                email_to = self.partner_id.email
                _logger.info("SENDING MAIL TO PARTNER: %s / %s" % (self.partner_id.name, email_to))
            if not self.partner_id.email:
                if config.edi_missing_email == 'template':
                    email_to = template.email_to or config.test_email
                    _logger.info("SENDING MAIL TEMPLATE OR TEST MODE: %s" % (email_to))
                elif config.edi_missing_email == 'default':
                    email_to = config.test_email
                    _logger.info("SENDING MISSING MAIL TO TEST: %s" % (email_to))
                elif config.edi_missing_email == 'skip':
                    _logger.info("MISSING PARTNER EMAIL - SKIPPING: %s" % (self.partner_id.name))
                    return

        res_ids = self.ids
        data = {}
        export_273S_pdf, dummy = self.env["ir.actions.report"].sudo()._render_qweb_pdf(report_action, res_ids=res_ids,
                                                                                       data=data)
        pdf_file = base64.encodebytes(export_273S_pdf)
        pdf_attachment = self.env['ir.attachment'].create({
            'name'     : "%s.pdf" % self.name,
            'datas'    : pdf_file,
            'type'     : 'binary',
            'res_model': self._name,
            'res_id'   : self.id,
        })

        xml_attachment = self.env['ir.attachment'].search(
                [
                    ('res_model', '=', 'account.move'),
                    ('name', 'like', '.xml'),
                    ('res_id', '=', self.id)
                ], order="create_date desc", limit=1
        )

        attachment_ids = []
        if pdf_attachment:
            attachment_ids.append(pdf_attachment.id)
        if xml_attachment:
            attachment_ids.append(xml_attachment.id)

        env = jinja2.Environment()
        template_html = env.from_string(template.body_html)
        kwargs = {'object': self}
        body_html = template_html.render(kwargs)

        values = {
            'email_from'    : config.edi_email_sender,
            'email_to'      : email_to,
            'body_html'     : body_html,
            'auto_delete'   : False,
            'attachment_ids': [(6, 0, attachment_ids)],
        }

        template.send_mail(self.id, force_send=True, email_values=values)
        self.edi_document_sent = True

    def sifen_notify(self, vals):
        pass
