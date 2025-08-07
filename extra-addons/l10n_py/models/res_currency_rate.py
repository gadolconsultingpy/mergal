from odoo import api, models, fields, _


class ResCurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    fiscal_currency_rate = fields.Float("Fiscal Currency Rate")

    @api.onchange('fiscal_currency_rate')
    def _onchange_fiscal_currency_rate(self):
        if self.fiscal_currency_rate:
            self.rate = 1 / self.fiscal_currency_rate
        else:
            self.rate = 0

    @api.onchange('rate')
    def _inverse_onchange_rate(self):
        if self.rate:
            self.fiscal_currency_rate = self.env.company.currency_id.round(1 / self.rate)
        else:
            self.rate = 0
