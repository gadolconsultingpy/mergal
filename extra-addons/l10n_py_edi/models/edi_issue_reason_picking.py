from odoo import api, models, fields


class EDIIssueReasonPicking(models.Model):
    _name = 'edi.issue.reason.picking'
    _description = "Picking Issue Reason"

    code = fields.Char("Code")
    name = fields.Char("Name")