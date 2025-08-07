from odoo import api, models, fields


class AccountTax(models.Model):
    _inherit = 'account.tax'

    taxable_percent = fields.Float("Taxable Percent", default=100)