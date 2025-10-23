from odoo import api, models, fields, _


class IrSequence(models.Model):
    _inherit = ['ir.sequence', 'mail.thread', 'mail.activity.mixin']
    _name = 'ir.sequence'

    number_next_actual = fields.Integer(tracking=True)
