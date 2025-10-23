from odoo import api, models, fields, _
from odoo.exceptions import UserError


class AccountMoveInvalid(models.Model):
    _inherit = 'account.move.invalid'

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

    def action_draft(self):
        if self.sifen_state == 'approved':
            raise UserError(_("Cannot change state to Draft, the SIFEN state is Approved."))
        if self.state == 'confirm' and self.sifen_state != 'approved':
            self.state = 'draft'

    def action_reset_to_confirm(self):
        if self.state == 'sent' and self.sifen_state != 'approved':
            self.state = 'confirm'

    def send(self):
        self.env['edi.procedure'].run_procedure(record=self, procedure="sifen.account.move.invalid")

    def sifen_notify(self, vals):
        pass

    def create_edi_document_invalid(self):
        if self.env['edi.document.invalid'].search([('name', '=', self.name)]):
            raise UserError(_("A Document Invalidation with this name already exists."))
        vals = {}
        vals['name'] = self.name
        vals['company_id'] = self.company_id.id
        vals['sequence_id'] = self.sequence_id.id
        vals['from_number'] = self.from_number
        vals['to_number'] = self.to_number
        vals['journal_id'] = self.journal_id.id
        vals['reason'] = self.reason
        vals['invoice_ids'] = [(4, x.id) for x in self.invoice_ids]
        vals['picking_ids'] = [(4, x.id) for x in self.picking_ids]
        vals['state'] = self.state
        vals['edi_transaction_type'] = self.edi_transaction_type
        vals['sifen_state'] = self.sifen_state
        vals['sifen_state_code'] = self.sifen_state_code
        vals['sifen_state_message'] = self.sifen_state_message
        vals['sifen_authorization'] = self.sifen_authorization
        record = self.env['edi.document.invalid'].create(vals)
        return {
            'type'     : 'ir.actions.act_window',
            'name'     : _('Document Invalidation'),
            'res_model': 'edi.document.invalid',
            'view_mode': 'form',
            'target'   : 'new',
            'res_id'   : record.id,
        }
