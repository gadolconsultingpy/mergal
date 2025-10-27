from odoo import api, models, fields


class EDIPresence(models.Model):
    _name = 'edi.presence'
    _description = "Presence Indicator"

    code = fields.Char("Code")
    name = fields.Char("Name")