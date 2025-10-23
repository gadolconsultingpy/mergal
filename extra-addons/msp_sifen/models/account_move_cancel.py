from odoo import api, models, fields, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AccountMoveCancel(models.Model):
    _inherit = 'account.move.cancel'

    edi_event_qty = fields.Integer('EDI Events Qty', compute='_compute_edi_event_qty')

    sifen_state = fields.Selection(
            [
                ('skip', "Skip"),
                ('pending', "Pending"),
                ('approved', "Approved"),
                ('rejected', 'Rejected'),
            ], default='pending', string="SIFEN State", copy=False, tracking=True
    )
    sifen_state_code = fields.Char("SIFEN State Code", copy=False, tracking=True)
    sifen_state_message = fields.Text("SIFEN State Message", copy=False, tracking=True)
    sifen_authorization = fields.Char("SIFEN Authorization", copy=False, tracking=True)

    def _compute_edi_event_qty(self):
        for rec in self:
            rec.edi_event_qty = self.env['edi.event'].search_count(
                    [
                        ('res_model', '=', self._name), ('res_id', '=', rec.id)
                    ]
            )

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

    def send(self):
        self.env['edi.procedure'].run_procedure(record=self, procedure="sifen.account.move.cancel")

    def sifen_notify(self, vals):
        pass

    @api.model
    def _cron_edi_send(self):
        companies = self.env['res.company'].search([])
        for comp in companies:
            config = self.env['res.config.custom'].get_company_custom_config(company_id=comp.id)
            if not config:
                continue
            # Pending Cancellations
            cancellations = self.env['account.move.cancel'].search(
                    [
                        ('company_id', '=', comp.id),
                        ('state', '=', 'confirm'),
                        ('sifen_state', '=', 'pending')
                    ], order="create_date, id "
            )
            for cancel in cancellations:
                setting = self.env['res.config.custom'].search([('company_id', '=', cancel.company_id.id)])
                if not setting:
                    msg = _("Setting for Send Invoice Missing")
                    raise UserError(msg)
                _logger.info("Processing Invoice: %s" % (cancel.name))
                cancel.with_context(edi_procedure='sifen.account.move.cancel').sifen_procedure()

    def sifen_procedure(self, procedure='sifen.account.move.cancel'):
        ctx_proc = self.env.context.get('edi_procedure', procedure)
        self.env['edi.procedure'].run_procedure(record=self, procedure=ctx_proc)

    def create_edi_document_cancel(self):
        if self.env['edi.document.cancel'].search([('name', '=', self.name)]):
            raise UserError(_("A Document Cancellation with this name already exists."))
        vals = {}
        vals['name'] = self.name
        vals['edi_document_datetime'] = self.edi_document_date
        vals['edi_document_type'] = self.edi_document_type.id
        vals['company_id'] = self.company_id.id
        vals['invoice_id'] = self.invoice_id.id
        vals['picking_id'] = self.picking_id.id
        vals['reason'] = self.reason
        vals['state'] = self.state
        vals['sifen_state'] = self.sifen_state
        vals['sifen_state_code'] = self.sifen_state_code
        vals['sifen_state_message'] = self.sifen_state_message
        vals['sifen_authorization'] = self.sifen_authorization
        record = self.env['edi.document.cancel'].create(vals)
        return {
            'type'     : 'ir.actions.act_window',
            'name'     : _('Document Cancellation'),
            'res_model': 'edi.document.cancel',
            'view_mode': 'form',
            'target'   : 'new',
            'res_id'   : record.id,
        }
