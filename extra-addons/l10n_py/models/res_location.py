from odoo import api, models, fields

class ResLocation(models.Model):
    _name = 'res.location'
    _description = 'Location'

    code = fields.Char("Code")
    name = fields.Char("Name")
    district_id = fields.Many2one('res.district', string="District")
