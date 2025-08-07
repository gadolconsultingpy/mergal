from odoo import api, models, fields


class TaxPayer(models.Model):
    _name = 'tax.payer'
    _description = 'Tax Payer'

    code = fields.Char("Code", index=True)
    name = fields.Char("Name", index=True)
    digit = fields.Char("Digit")
    legacy_code = fields.Char("Legacy Code")
    status = fields.Char("Status", index=True)

    _sql_constraints = [('unique_code','UNIQUE(code)','The Code must be Unique')]

    def dummy(self):
        a = self.env['sale.order']
