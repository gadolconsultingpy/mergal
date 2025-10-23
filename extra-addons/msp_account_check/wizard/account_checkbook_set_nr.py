from odoo import api, models, fields, _
from odoo.exceptions import UserError


class AccountCheckbookSetNr(models.Model):
    _name = 'account.checkbook.set.nr'
    _description = 'Checkbook Next Nr'

    checkbook_id = fields.Many2one('account.checkbook', string="Checkbook")
    from_number = fields.Integer("From Number")
    to_number = fields.Integer("To Number")
    next_number = fields.Integer("Next Number")

    def default_get(self, fields_list):
        vals = super(AccountCheckbookSetNr, self).default_get(fields_list)
        checkbook = self.env['account.checkbook'].browse(self.env.context.get('active_ids')[0])
        vals['checkbook_id'] = checkbook.id
        vals['from_number'] = checkbook.from_number
        vals['to_number'] = checkbook.to_number
        vals['next_number'] = checkbook.sequence_id.number_next_actual
        return vals

    def set_next_nr(self):
        if self.next_number < self.from_number or self.next_number > self.to_number:
            raise UserError("The Next Number must be between: %s - %s " % (self.from_number, self.to_number))
        sequence = self.env['ir.sequence'].browse(self.checkbook_id.sequence_id.id)
        sequence.write({'number_next_actual': self.next_number})
