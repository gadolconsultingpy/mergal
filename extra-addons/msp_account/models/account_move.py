from odoo import api, models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    salesman_id = fields.Many2one('hr.employee', string="Salesman")