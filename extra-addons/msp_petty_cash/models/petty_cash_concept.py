from odoo import api, models, fields


class PettyCashConcept(models.Model):
    _name = 'petty.cash.concept'
    _description = 'Petty Cash Concept'
    _check_company_auto = True

    name = fields.Char("Name", required=True)
    account_id = fields.Many2one('account.account', string="Account", required=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account", company_dependent=True)
    amount = fields.Float("Amount")  # TODO: For now only in Company Currency
    deductible_amount = fields.Float("Deductible Amount")
    require_invoice = fields.Boolean('Require Invoice')
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company.id)
