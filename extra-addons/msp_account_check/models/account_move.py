import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"

    check_id = fields.Many2one('account.check', string="Check Id")
    deposit_id = fields.Many2one('account.securities.deposit', string="Deposit Id")
