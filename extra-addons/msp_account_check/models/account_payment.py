from odoo import api, models, fields, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    payment_method_check_type = fields.Selection(related='payment_method_line_id.check_type',
                                                 string="Payment Method Check Type")
    payment_bank_id = fields.Many2one('res.bank', string="Issue Bank")
    issue_date = fields.Date('Issue Date')
    accreditation_date = fields.Date("Accreditation Date")
    check_number = fields.Char("Check Number Legacy")
    check_number_py = fields.Char("Check Number", related='check_number', store=True)
    checkbook_id = fields.Many2one('account.checkbook', string="Checkbook")
    check_id = fields.Many2one('account.check', string="Check Id")

    def get_check_payment_origin(self):
        return ['manual']

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        for rec in self:
            if (rec.payment_origin in rec.get_check_payment_origin()
                    and rec.payment_method_line_id.check_type in ['check', 'deferred-check']):
                rec.create_checks()
        return res

    def action_draft(self):
        res = super(AccountPayment, self).action_draft()
        if self.payment_origin in self.get_check_payment_origin():
            if self.check_id:
                if self.check_id.state == 'in-portfolio':
                    self.check_id.action_draft()
                    self.check_id.unlink()
                else:
                    raise UserError("The Check State is not in In-Portfolio")
        return res

    @api.onchange('payment_method_line_id')
    def _onchange_journal_payment_method_line_id(self):
        if self.payment_method_line_id.check_type in ['check', 'deferred-check']:
            self.payment_bank_id = self.journal_id.bank_id.id
        if not self.journal_id.bank_id:
            self.payment_bank_id = False

    def create_checks(self):
        vals = {}
        vals['issue_date'] = self.issue_date
        vals['number'] = self.check_number_py
        vals['amount'] = self.amount
        vals['journal_id'] = self.journal_id.id
        vals['bank_id'] = self.payment_bank_id.id
        vals['payment_method_line_id'] = self.payment_method_line_id.id
        vals['reference'] = self.name
        vals['state'] = 'in-portfolio'
        vals['checkbook_id'] = self.checkbook_id.id
        if self.payment_method_line_id.check_type == 'deferred-check':
            vals['accreditation_date'] = self.accreditation_date
        if self.payment_type == 'inbound':
            vals['type'] = 'third'
            vals['partner_id'] = self.partner_id.id
            vals['issuer_name'] = self.partner_id.name
            vals['payee'] = self.company_id.name
        elif self.payment_type == 'outbound':
            vals['type'] = 'own'
            vals['checkbook_id'] = self.checkbook_id.id
            vals['partner_id'] = self.company_id.partner_id.id
            vals['issuer_name'] = self.company_id.partner_id.name
            vals['payee'] = self.partner_id.name
        check = self.env['account.check'].create(vals)
        # print("CHECK CREATED", check)
        res = self.write({'check_id': check.id})
        if not res:
            msg = _("Error Creating Check")
            raise UserError("%s: %s" % (msg, self.name))
        # print("RES", res)
