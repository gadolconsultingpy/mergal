import datetime
from odoo import api, models, fields, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class EDIDocumentInvalid(models.Model):
    _inherit = ['mail.thread']
    _name = 'edi.document.invalid'
    _description = 'Document Invalidation'

    name = fields.Char("Name")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company.id)
    sequence_id = fields.Many2one('ir.sequence', string="Sequence")
    stamped_number = fields.Char("Stamped Number", related='sequence_id.stamped_number')
    establishment = fields.Char("Establishment", related='sequence_id.establishment')
    dispatch_point = fields.Char("Dispatch Point", related='sequence_id.issuance_point')
    from_number = fields.Integer("From")
    to_number = fields.Integer("To")
    journal_id = fields.Many2one('account.journal', string="Journal")
    reason = fields.Char("Reason")
    invoice_ids = fields.Many2many('account.move', string="Invoices")
    picking_ids = fields.Many2many('stock.picking', string="Pickings")
    sequence_model = fields.Char(related='sequence_id.binding_model_id.model', string="Model")
    edi_transaction_type = fields.Many2one('edi.document.type', related='journal_id.invoice_type_id')
    edi_document_datetime = fields.Datetime("Document Date/Time", default=lambda self: fields.Datetime.now(),
                                            store=True)
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

    def action_reset_to_confirm(self):
        if self.state == 'sent':
            self.state = 'confirm'

    def bring_invoices(self):
        config = self.env['res.config.custom'].get_company_custom_config(company_id=self.company_id.id)
        if not config:
            raise UserError(_("Missing configuration for company %s" % self.company_id.name))
        if not config.invalid_document_partner_id:
            raise UserError(_("Missing Partner Id for Invalid Documents"))
        if not config.invalid_document_payment_term_id:
            raise UserError(_("Missing Payment Term Id for Invalid Documents"))

        invoices = []
        for number in range(self.from_number, self.to_number + 1):
            sequence = "%s-%s-%s" % (self.establishment, self.dispatch_point, str(number).zfill(7))
            inv = self.env['account.move'].search(
                    [
                        ('journal_id', '=', self.journal_id.id),
                        ('sequence_id', '=', self.sequence_id.id),
                        ('name', '=', sequence)
                    ]
            )
            if inv:
                invoices.append((4, inv.id))
            else:
                inv = self.env['account.move'].create(
                        {
                            'name'                   : sequence,
                            'partner_id'             : config.invalid_document_partner_id.id,
                            'invoice_payment_term_id': config.invalid_document_payment_term_id.id,
                            'move_type'              : 'out_invoice',
                            'journal_id'             : self.journal_id.id,
                            'invoice_date'           : self.edi_document_datetime.date(),
                            'sequence_id'            : self.sequence_id.id,
                            'line_ids'               : [(0, 0, {'price_unit': 0.0})]
                        }
                )
                _logger.info("Invoice Created: %s" % inv.name)
                if inv:
                    invoices.append((4, inv.id))
        self.invoice_ids = [(5, 0, 0)] + invoices

    def bring_pickings(self, sequences):
        pickings = self.env['stock.picking'].search(
                [
                    ('journal_id', '=', self.journal_id.id),
                    ('sequence_id', '=', self.sequence_id.id),
                    ('name', 'in', sequences)
                ]
        )
        self.picking_ids = [(4, x.id) for x in pickings]

    def action_confirm(self):
        sequence = self.env['ir.sequence'].search([('code', '=', 'edi.document.invalid')])
        if not sequence:
            msg = _("Missing Sequence: %s" % ("edi.document.invalid"))
            raise UserError(msg)
        self.name = sequence.next_by_id()
        numbers = range(self.from_number, self.to_number + 1)
        sequences = ["%s%s" % (self.sequence_id.prefix, str(x).zfill(self.sequence_id.padding)) for x in numbers]
        if self.sequence_id.binding_model_id.model == 'account.move':
            self.bring_invoices()
        elif self.sequence_id.binding_model_id.model == 'stock.picking':
            self.bring_pickings(sequences)
        self.state = 'confirm'

    def send(self):
        pass

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Only records in draft status can be deleted."))
        return super(EDIDocumentInvalid, self).unlink()
