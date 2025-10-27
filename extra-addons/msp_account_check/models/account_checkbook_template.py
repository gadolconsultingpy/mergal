from odoo import api, models, fields, _


class AccountCheckbookTemplate(models.Model):
    _name = 'account.checkbook.template'
    _description = "Checkbook Template"

    name = fields.Char("Name")
    report_id = fields.Many2one('ir.actions.report', string="Report", domain=[('model', '=', 'account.checkbook')])
