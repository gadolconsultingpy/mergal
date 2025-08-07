from odoo import api, models, fields


class ResNeighborhood(models.Model):
    _name = 'res.neighborhood'
    _description = 'Neighborhood'

    code = fields.Char("Code")
    name = fields.Char("Name")
    location_id = fields.Many2one('res.location', string="Location")
