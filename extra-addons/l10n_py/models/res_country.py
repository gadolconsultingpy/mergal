from odoo import api, models, fields


class ResCountry(models.Model):
    _inherit = 'res.country'

    iso_code = fields.Char("Code ISO 3166 ", help="International Standard Organization ISO 3166-3 ")