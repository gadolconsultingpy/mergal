from odoo import api, models, fields, _


class ResConfigCustom(models.Model):
    _inherit = 'res.config.custom'

    # check flow journals
    in_portfolio_journal_id = fields.Many2one('account.journal', string="In Portfolio", company_dependent=True)
    rejected_journal_id = fields.Many2one('account.journal', string="Rejected", company_dependent=True)
    cash_account_id = fields.Many2one('account.account', string="Cash Account", company_dependent=True,
                                      help="Used for Securities Deposit")
