from odoo import api, models, fields, _


class ResConfigCustom(models.Model):
    _inherit = 'res.config.custom'
    _check_company_auto = True

    not_deductible_account_id = fields.Many2one('account.account', string='Not Deductible Account',
                                                company_dependent=True)
