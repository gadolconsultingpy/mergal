from odoo import api, models, fields, _


class ResBranch(models.Model):
    _name = "res.branch"
    _description = "Establishment"
    _order = 'sequence, id'

    _sql_constraints = [('unique_branch', 'unique(company_id, code)', 'Branch Code Must Be Unique per Company')]

    name = fields.Char(index=True, required=True)
    code = fields.Char(string="Code", required=True)
    company_id = fields.Many2one('res.company', string="Related Company")
    company_partner_id = fields.Many2one('res.partner', 'Company Partner', related='company_id.partner_id')
    partner_id = fields.Many2one('res.partner', string='Related Address', required=True)
    sequence = fields.Integer('Sequence')
    active = fields.Boolean(string="Active", default=True)
