from odoo import api, models, fields


class EDIIssueResponsible(models.Model):
    _name = 'edi.issue.responsible'
    _description = "Picking Issue Responsible"

    code = fields.Char("Code")
    name = fields.Char("Name")