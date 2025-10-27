from odoo import api, models, fields, _


class AssignCheckbook(models.TransientModel):
    _name = 'assign.checkbook'
    _description = 'Assign Checkbook'

    bank_id = fields.Many2one('res.bank', string="Bank")
    bank_account_id = fields.Many2one('res.partner.bank', string="Partner Bank")
    check_ids = fields.One2many('assign.checkbook.check', 'parent_id', string="Checks")

    def process(self):
        return {}


class AssignCheckbookCheck(models.TransientModel):
    _name = 'assign.checkbook.check'
    _description = 'Assign Checkbook Check'

    parent_id = fields.Many2one('assign.checkbook', string="Assign Checkbook")
    sequence = fields.Integer("Sequence")
    check_id = fields.Many2one('account.check')
    payee = fields.Char("Payee", related='check_id.payee')
    currency_id = fields.Many2one('res.currency', string="Currency", related='check_id.currency_id')
    amount = fields.Monetary("Amount", related='check_id.amount')
