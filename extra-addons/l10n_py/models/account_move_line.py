from odoo import api, models, fields, _
from functools import lru_cache


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    inverse_rate = fields.Float("User Inverse Rate", compute="_compute_inverse_rate")

    @api.depends('currency_id', 'company_id', 'move_id.date')
    def _compute_inverse_rate(self):
        for line in self:
            line.inverse_rate = line.move_id.inverse_rate

    @api.depends('currency_id', 'company_id', 'move_id.date')
    def _compute_currency_rate(self):
        for line in self:
            line.currency_rate = 1 / (line.move_id.inverse_rate or 1.0)
