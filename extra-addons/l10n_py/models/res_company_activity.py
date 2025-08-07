from odoo import api, models, fields


class ResCompanyActivity(models.Model):
    _name = 'res.company.activity'
    _description = "Company Economic Activity"

    code = fields.Char("Code")
    name = fields.Char("Name")
    display_name = fields.Char("Display Name", compute="_compute_display_name")

    @api.depends('code','name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "[%s] %s" %(rec.code, rec.name)

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None, order=None):
        if args is None:
            args = []

        search_domain = ['|', ('name', operator, name), ('code', operator, name)]
        ids = list(self._search(search_domain + args, limit=limit, order=order))
        return ids

