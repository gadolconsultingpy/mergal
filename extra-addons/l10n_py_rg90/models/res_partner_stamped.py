from odoo import api, models, fields


class ResPartnerStamped(models.Model):
    _name = 'res.partner.stamped'
    _description = 'Partner Stamped'

    name = fields.Char("Stamped Nr.", required=True)
    from_date = fields.Date("From Date", required=True)
    to_date = fields.Date("To Date", required=True)
    from_number = fields.Integer("From Number", default=1, required=True)
    to_number = fields.Integer("To Number", default=9999999, required=True)
    partner_id = fields.Many2one('res.partner', string="Partner", required=True)
