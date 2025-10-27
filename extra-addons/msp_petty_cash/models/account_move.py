from odoo import api, models, fields, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    petty_cash_sheet_id = fields.Many2one('petty.cash.sheet', ondelete='restrict')

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    internal_note = fields.Char("Internal Note", help="Used to reconcile payments")