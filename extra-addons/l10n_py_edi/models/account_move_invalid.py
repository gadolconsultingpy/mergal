from odoo import api, models, fields, _
from odoo.exceptions import UserError


class AccountMoveInvalid(models.Model):
    _inherit = ['mail.thread']
    _name = 'account.move.invalid'
    _description = 'Invalid Invoices'

    name = fields.Char("Name")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company.id)
    sequence_id = fields.Many2one('ir.sequence', string="Sequence")
    stamped_number = fields.Char("Stamped Number", related='sequence_id.stamped_number')
    establishment = fields.Char("Establishment", related='sequence_id.establishment')
    dispatch_point = fields.Char("Dispatch Point", related='sequence_id.dispatch_point')
    from_number = fields.Integer("From")
    to_number = fields.Integer("To")
    journal_id = fields.Many2one('account.journal', string="Journal")
    reason = fields.Char("Reason")
    invoice_ids = fields.Many2many('account.move', string="Invoices")
    picking_ids = fields.Many2many('stock.picking', string="Pickings")
    sequence_model = fields.Char(related='sequence_id.binding_model_id.model', string="Model")
    edi_transaction_type = fields.Many2one('edi.document.type', related='journal_id.invoice_type_id')
    edi_document_date = fields.Date("Document Date", default=fields.Date.context_today, copy=False, tracking=True)
    state = fields.Selection(
            [
                ('draft', 'Draft'),
                ('confirm', 'Confirmed'),
                ('sent', 'Sent'),
            ], default='draft', string="State"
    )

    @api.onchange('sequence_id')
    def _onchange_sequence_id(self):
        if self.sequence_id:
            self.from_number = self.sequence_id.number_next_actual
            self.journal_id = self.sequence_id.journal_id.id

    def action_draft(self):
        if self.state == 'confirm':
            self.state = 'draft'

    def action_confirm(self):
        sequence = self.env['ir.sequence'].search([('code', '=', 'account.move.invalid')])
        if not sequence:
            msg = _("Missing Sequence: %s" % ("account.move.invalid"))
            raise UserError(msg)
        self.name = sequence.next_by_id()
        numbers = range(self.from_number, self.to_number + 1)
        sequences = ["%s%s" % (self.sequence_id.prefix, str(x).zfill(self.sequence_id.padding)) for x in numbers]
        if self.sequence_id.binding_model_id.model == 'account.move':
            invoices = self.env['account.move'].search(
                    [
                        ('journal_id', '=', self.journal_id.id),
                        ('sequence_id', '=', self.sequence_id.id),
                        ('name', 'in', sequences)
                    ]
            )
            self.invoice_ids = [(4, x.id) for x in invoices]
        elif self.sequence_id.binding_model_id.model == 'stock.picking':
            pickings = self.env['stock.picking'].search(
                    [
                        ('journal_id', '=', self.journal_id.id),
                        ('sequence_id', '=', self.sequence_id.id),
                        ('name', 'in', sequences)
                    ]
            )
            self.picking_ids = [(4, x.id) for x in pickings]
        self.state = 'confirm'

    def send(self):
        pass

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Only records in draft status can be deleted."))
        return super(AccountMoveInvalid, self).unlink()
