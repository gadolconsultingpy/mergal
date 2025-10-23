import datetime

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class EDIDocumentCancel(models.Model):
    _inherit = ['mail.thread']
    _name = 'edi.document.cancel'
    _description = 'Document Cancellation'

    name = fields.Char("Name")
    edi_document_type = fields.Many2one('edi.document.type', string='Document Type')
    edi_document_type_code = fields.Char(related='edi_document_type.code', string="Document Type Code")
    edi_document_datetime = fields.Datetime("Document Date/Time", default=lambda self: fields.Datetime.now(),
                                            store=True)
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

    def action_confirm(self):
        sequence = self.env['ir.sequence'].search([('code', '=', 'edi.document.cancel')])
        if not sequence:
            msg = _("Missing Sequence: %s" % ("edi.document.cancel"))
            raise UserError(msg)
        self.name = sequence.next_by_id()
        self.state = 'confirm'

    def send(self):
        pass

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Only records in draft status can be deleted."))
        return super(EDIDocumentCancel, self).unlink()
