from odoo import api, models, fields, _


class EDITag(models.Model):
    _name = 'edi.tag'
    _description = "EDI Tag"

    name = fields.Char("Name")
    color = fields.Integer("Color")