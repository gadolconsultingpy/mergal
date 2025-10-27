from odoo import api, models, fields

class CardIssuer(models.Model):
    _name = 'card.issuer'
    _description = 'Card Issuer'
    
    name = fields.Char("Name")
    code = fields.Char("Code")
    partner_id = fields.Many2one("res.partner", string="Processor Partner")