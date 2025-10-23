from odoo import api, models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _default_branch_id(self):
        return self.env.user.branch_id.id

    branch_id = fields.Many2one('res.branch', string="Branch", default=_default_branch_id)