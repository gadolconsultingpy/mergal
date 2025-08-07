from odoo import api, models, fields


class ResDistrict(models.Model):
    _name = 'res.district'
    _description = 'District'

    code = fields.Char("Code")
    name = fields.Char("Name")
    state_id = fields.Many2one('res.country.state', string="State")
