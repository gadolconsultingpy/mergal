from odoo import api, models, fields


class AccountTaxExciseCategory(models.Model):
    _name = 'account.tax.excise.category'
    _description = 'Tax Excise Category'

    code = fields.Char("Code")
    name = fields.Char("Name")
