from odoo import api, models, fields


class EDIIssueReason(models.Model):
    _name = 'edi.issue.reason'
    _description = "Issue Reason"

    code = fields.Char("Code")
    name = fields.Char("Name")