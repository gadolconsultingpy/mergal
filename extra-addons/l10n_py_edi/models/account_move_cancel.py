from odoo import api, models, fields, _
from odoo.exceptions import UserError


class AccountMoveCancel(models.Model):
    _inherit = ['mail.thread']
    _name = 'account.move.cancel'
    _description = 'Invoice Cancellation'

    name = fields.Char("Name")
    edi_document_type = fields.Many2one('edi.document.type', string='Document Type')
    edi_document_type_code = fields.Char(related='edi_document_type.code', string="Document Type Code")
    edi_document_date = fields.Date("Document Date", default=fields.Date.context_today, copy=False, tracking=True)
    invoice_id = fields.Many2one('account.move', string="Invoice")
    picking_id = fields.Many2one('stock.picking', string="Picking")
    reason = fields.Char("Cancellation Reason")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company.id)
    state = fields.Selection(
            [
                ('draft', 'Draft'),
                ('confirm', 'Confirmed'),
                ('sent', 'Sent'),
            ], default='draft', string="State"
    )

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Only records in draft status can be deleted."))
        return super(AccountMoveCancel, self).unlink()

    def action_confirm(self):
        sequence = self.env['ir.sequence'].search([('code', '=', 'account.move.cancel')])
        if not sequence:
            msg = _("Missing Sequence: %s" % ("account.move.cancel"))
            raise UserError(msg)
        self.name = sequence.next_by_id()
        self.state = 'confirm'

    def send(self):
        pass
