from odoo import api, models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    def get_default_branch(self):
        branch = self.env['res.branch'].search([('company_id','=',self.id)], order="sequence",limit=1)
        return branch