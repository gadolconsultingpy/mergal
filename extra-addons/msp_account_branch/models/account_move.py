from odoo import api, models, fields, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    branch_id = fields.Many2one('res.branch', string="Branch")
    sequence_id = fields.Many2one('ir.sequence', string="Invoice Sequence")

    @api.onchange('journal_id', 'move_type')
    def _onchange_journal_id(self):
        invoice_user_id = self.invoice_user_id.id or self.env.user.id
        if not self.sequence_id:
            self.sequence_id = self._search_sequence_id(user_id=invoice_user_id, move_type=self.move_type)

    # @api.depends('journal_id', 'move_type')
    # def _compute_sequence_id(self):
    #     for rec in self:
    #         invoice_user_id = rec.invoice_user_id.id or rec.env.user.id
    #         if not rec.sequence_id:
    #             rec.sequence_id = rec._search_sequence_id(user_id=invoice_user_id, move_type=rec.move_type)
    #         else:
    #             rec.sequence_id = rec.sequence_id

    def default_get(self, fields_list):
        vars = super(AccountMove, self).default_get(fields_list)
        invoice_user_id = vars.get('invoice_user_id') or self.env.user.id
        salesman = self.env['res.users'].browse(invoice_user_id)
        branch = salesman.branch_id
        vars['branch_id'] = branch.id
        vars['invoice_date'] = fields.Date.context_today(self)
        return vars

    def copy(self, default=None):
        default_fields = ['user_id', 'sequence_id', 'branch_id']
        if not default:
            default = {}
        for df in default_fields:
            default[df] = getattr(self, df).id
        default['sequence_id'] = self._search_sequence_id(user_id=self.user_id.id,
                                                          move_type=self.move_type)
        new = super(AccountMove, self).copy(default)
        return new

    @api.onchange('invoice_user_id')
    def _onchange_invoice_user_id(self):
        if hasattr(super(AccountMove, self), "_onchange_invoice_user_id"):
            getattr(super(AccountMove, self), "_onchange_invoice_user_id")()
        self.branch_id = self.invoice_user_id.branch_id.id
        # print("_onchange_invoice_user_id")
        self._set_sequence_id()

    @api.onchange('journal_id', 'branch_id')
    def _onchange_journal_branch_for_sequence(self):
        self._set_sequence_id()

    def _set_sequence_id(self):
        if self.branch_id:
            if not self.sequence_id:
                dp = self.branch_id.get_dispatch_point(salesman_id=self.invoice_user_id.id,
                                                       move_type=self.move_type)
                if dp:
                    self.sequence_id = dp.sequence_id.id
        return

    def _search_sequence_id(self, user_id, move_type):
        branch = self.env['res.users'].browse(user_id).branch_id
        if branch:
            dp = branch.get_dispatch_point(salesman_id=user_id,
                                           move_type=move_type)
            if dp:
                return dp.sequence_id.id

    def action_post(self):  # OK
        for rec in self:
            if rec.move_type in ['out_invoice', 'out_refund', 'out_receipt']:
                if not rec.sequence_id:
                    msg = _("Missing Sequence Number")
                    raise UserError(msg)
                rec.sequence_id.check_stamped_number(rec.invoice_date)
        return super(AccountMove, self).action_post()

    def _set_next_sequence(self):
        if self.sequence_id and self.sifen_environment != 'X':
            if not self.name or self.name == _('Draft') or self.name == '/':
                self.name = self.sequence_id.next_by_id(sequence_date=self.invoice_date)
                print("_set_next_sequence.1", self.name, self.sequence_id.id, self.invoice_date)
        else:
            print("_set_next_sequence.2", self.name, self.sequence_id.id, self.invoice_date)
            super(AccountMove, self)._set_next_sequence()
