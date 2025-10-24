from odoo import api, fields, models, _


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def _default_invoice_type_id(self):
        return self.env['edi.document.type'].search([('code', '=', 'X')])

    invoice_type = fields.Selection([
        ('1', 'Factura electrónica'),
        ('2', 'Factura electrónica de Exportación Futuro'),
        ('3', 'Factura electrónica de Importación Futuro'),
        ('4', 'Autofactura Electrónica'),
        ('5', 'Nota de crédito electrónica'),
        ('6', 'Nota de débito electrónica'),
        ('7', 'Nota de remisión electrónica'),
        ('8', 'Comprobante de retención electrónico Futuro')
    ], default="1", required=True,
    )
    invoice_type_id = fields.Many2one('edi.document.type',
                                      string="Electronic Document Type",
                                      default=_default_invoice_type_id,
                                      help="Tipo de Documento Electrónico (C002)")

    reversal_journal_id = fields.Many2one('account.journal', string="Reversal Journal",
                                          domain=[('type', 'in', ('sale', 'purchase'))],
                                          help="Journal used to post the reversal entries for entries posted in this journal."
                                          )
    establishment = fields.Char("Establishment Code", size=3)
    issuance_point_ids = fields.One2many('account.journal.issue.point', 'parent_id', string="Dispatch Point")

    def next_sequence(self, cur_seq):
        a, b = ord(cur_seq[0]), ord(cur_seq[1])
        b = b + 1
        if b == 91:
            a = a + 1
            b = 65
        return "%s%s" % (chr(a), chr(b))


class AccountJournalIssuePoint(models.Model):
    _name = 'account.journal.issue.point'
    _description = 'Issue Point'

    parent_id = fields.Many2one('account.journal', string="Account Journal", ondelete="cascade")
    sequence = fields.Integer('Sequence')
    issuance_point = fields.Char("Issuance Point", size=3, required=True)

    sequence_id = fields.Many2one('ir.sequence', string="Sequence Id")
    sequence_use = fields.Float('Use %', compute='_compute_sequence_use')
    sequence_next_actual = fields.Integer("Next Actual", related="sequence_id.number_next_actual")
    sequence_remain = fields.Integer("Remain", compute='_compute_sequence_use')
    salesman_id = fields.Many2one('res.users', string="Salesman")

    @api.depends('sequence_id.number_next')
    def _compute_sequence_use(self):
        for rec in self:
            if not rec.sequence_id:
                rec.sequence_use = 0
                rec.sequence_remain = 0
            else:
                from_number = 1
                to_number = int("9" * rec.sequence_id.padding or 7)
                numbers = to_number - from_number + 1
                rec.sequence_use = (rec.sequence_id.number_next_actual + 1 - from_number) * 100 / numbers
                rec.sequence_remain = to_number - rec.sequence_id.number_next_actual + 1

    def next_sequence(self, cur_seq):
        a, b = ord(cur_seq[0]), ord(cur_seq[1])
        b = b + 1
        if b == 91:
            a = a + 1
            b = 65
        return "%s%s" % (chr(a), chr(b))

    def action_create_sequence(self):
        svars = {}
        code = 'account.move.%s.%s' % (self.parent_id.establishment, self.issuance_point)
        svars["code"] = code
        last_seq = self.env['ir.sequence'].search(
                [
                    ('code', '=', code),
                    ('journal_id', '=', self.parent_id.id)
                ], order='create_date desc', limit=1)
        code_char_ord = ""
        if last_seq:
            if len(last_seq[0].prefix.split("-")) == 3:
                code_char_ord = "AA"
            if len(last_seq[0].prefix.split("-")) == 4:
                code_char_ord = last_seq[0].prefix.split("-")[0]
                code_char_ord = self.next_sequence(code_char_ord)
        if code_char_ord:
            prefix = "%s-%s-%s-" % (code_char_ord, self.parent_id.establishment, self.issuance_point)
        else:
            prefix = "%s-%s-" % (self.parent_id.establishment, self.issuance_point)

        svars["prefix"] = prefix
        svars["name"] = "%s %s" % (self.parent_id.name, prefix[:-1])
        svars["establishment"] = self.parent_id.establishment
        svars["issuance_point"] = self.issuance_point
        vat = self.env.company.partner_id.vat
        if vat and "-" in vat:
            svars["stamped_number"] = vat.split("-")[0]
        else:
            svars["stamped_number"] = "00000000"
        svars["padding"] = 7
        svars["binding_model_id"] = self.env.ref('account.model_account_move').id
        svars["from_number"] = 1
        svars["to_number"] = 9999999
        svars["from_date"] = fields.Date.today()
        svars["to_date"] = fields.Date.today().replace(year=2099)
        svars["journal_id"] = self.parent_id.id
        seq = self.env['ir.sequence'].create(svars)
        if seq:
            self.sequence_id = seq.id
        return {
            'type'     : 'ir.actions.act_window',
            'name'     : 'Invoices Sequence',
            'res_model': 'ir.sequence',
            'view_mode': 'form',
            'view_id'  : self.env.ref('base.sequence_view').id,
            'target'   : 'new',
            'res_id'   : seq.id
        }
