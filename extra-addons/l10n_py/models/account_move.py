from odoo import _, api, models, fields


# Los textos quedan literal es español ya que forman parte del catálogo de la SET,
# no se deben traducir para evitar errores en el envio de datos.

class AccountMove(models.Model):
    _inherit = 'account.move'
    _name = 'account.move'

    payment_type = fields.Selection(
            [
                ('1', "Contado"),
                ('2', "Crédito"),
            ], default='1', required=True, compute="_compute_payment_type"
    )
    inverse_rate = fields.Float("User Inverse Rate", default=1.0)
    currency_rate = fields.Float("User Currency Rate", default=1.0)
    sequence_id = fields.Many2one('ir.sequence', string="Invoice Sequence")
    is_local_currency = fields.Boolean('Is Local Currency', compute="_compute_is_local_currency")

    @api.depends('currency_id')
    def _compute_is_local_currency(self):
        for rec in self:
            rec.is_local_currency = rec.currency_id.id == rec.company_id.currency_id.id

    @api.onchange('inverse_rate')
    def _onchange_inverse_rate(self):
        for rec in self:
            if not rec.is_local_currency:
                rec.currency_rate = 1 / rec.inverse_rate or 1.0
                rec.invoice_currency_rate = 1 / rec.inverse_rate or 1.0

    @api.depends('currency_id', 'company_currency_id', 'company_id', 'invoice_date')
    def _compute_invoice_currency_rate(self):
        for move in self:
            if move.is_invoice(include_receipts=True):
                if move.currency_id:
                    core_currency_rate = self.env['res.currency']._get_conversion_rate(
                            from_currency=move.company_currency_id,
                            to_currency=move.currency_id,
                            company=move.company_id,
                            date=move.invoice_date or fields.Date.context_today(move),
                    )
                    if not move.invoice_currency_rate:
                        move.invoice_currency_rate = core_currency_rate
                    else:
                        move.invoice_currency_rate = move.currency_rate
                else:
                    move.invoice_currency_rate = 1

    @api.onchange('currency_id', 'invoice_date', 'company_id')
    def _onchange_l10n_py_currency(self):
        invoice_date = self.invoice_date or fields.Date.context_today(self)
        rate_info = self.currency_id._get_rates(self.company_id, invoice_date)
        base_rate = rate_info.get(self.currency_id.id, 1.0)
        self.inverse_rate = 1.0 / base_rate
        self.currency_rate = base_rate

    @api.depends('invoice_payment_term_id')
    def _compute_payment_type(self):
        for rec in self:
            rec.payment_type = "1"
            if rec.invoice_payment_term_id and rec.invoice_payment_term_id.line_ids:
                if any([x.nb_days != 0 for x in rec.invoice_payment_term_id.line_ids]):
                    rec.payment_type = "2"

    def business_type(self):
        types = {'B2B': '1',
                 'B2C': '2',
                 'B2G': '3',
                 'B2F': '4'}
        return types.get("B2%s" % (self.partner_id.parent_id.business_partner_type or
                                   self.partner_id.business_partner_type), "2")

    # def _set_next_sequence(self):
    #     if self.sequence_id:
    #         if not self.name or self.name == _('Draft') or self.name == '/':
    #             self.name = self.sequence_id.next_by_id(sequence_date=self.invoice_date)
    #     else:
    #         super(AccountMove, self)._set_next_sequence()

    def convert_to_local(self, amount, currency=None):
        return self.currency_id.with_context({'commercial_currency_rate': self.inverse_rate})._convert(
                amount,
                to_currency=self.company_id.currency_id,
                company=self.company_id,
                date=self.invoice_date or fields.Date.context_today(self), round=True)

    def local_amount(self, value):
        res = value
        if self.is_local_currency:
            res = value
        ctx = dict(self.env.context)
        ctx["commercial_currency_rate"] = self.inverse_rate
        res = self.currency_id.with_context(ctx)._convert(from_amount=value,
                                                          to_currency=self.company_id.currency_id,
                                                          company=self.company_id,
                                                          date=self.invoice_date)
        return res
