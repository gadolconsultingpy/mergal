from odoo import api, models, fields


class CardProcessForm(models.Model):
    _name = 'card.process.form'
    _description = 'Card Process Form'

    name = fields.Char("Name")
    code = fields.Char("Code")
