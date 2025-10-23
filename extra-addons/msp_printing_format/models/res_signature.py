from odoo import api, models, fields, _


class ResSignature(models.Model):
    _name = 'res.signature'
    _description = 'Signature'

    name = fields.Char("Name")
    signature = fields.Image("Signature")
    user_id = fields.Many2one('res.users', string="User")
