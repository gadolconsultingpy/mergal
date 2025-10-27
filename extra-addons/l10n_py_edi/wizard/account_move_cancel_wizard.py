from odoo import api, models, fields, _


class AccountMoveCancelWizard(models.TransientModel):
    _name = 'account.move.cancel.wizard'
    _description = 'Invoice Cancelation Request'

    invoice_id = fields.Many2one('account.move', string="Invoice")
    reason = fields.Char("Cancellation Reason")

    def process(self):
        record = self.env['account.move.cancel'].create({'invoice_id': self.invoice_id.id, 'reason': self.reason})
        return {
            'type'     : 'ir.actions.act_window',
            'name'     : _('Invoice Cancellation'),
            'res_model': 'account.move.cancel',
            'view_mode': 'form',
            'res_id'   : record.id,
        }
