from odoo import api, models, fields, _
from odoo.exceptions import UserError


class AccountCheckbook(models.Model):
    _name = 'account.checkbook'
    _description = 'Checkbook'
    _check_company_auto = True

    name = fields.Char("Name", compute="_compute_name")
    journal_id = fields.Many2one('account.journal', string="Journal", company_dependent=True)
    bank_id = fields.Many2one('res.bank', string="Bank", related='journal_id.bank_id')
    bank_account_id = fields.Many2one('res.partner.bank', string="Bank Account", related='journal_id.bank_account_id')
    sequence_id = fields.Many2one('ir.sequence', string="Sequence")
    from_number = fields.Integer("From Number", required=True)
    to_number = fields.Integer("To Number", required=True)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company.id)
    partner_id = fields.Many2one('res.partner', string="Partner", related='company_id.partner_id')

    number_next_actual = fields.Integer("Number Next", related='sequence_id.number_next_actual')
    check_ids = fields.One2many('account.checkbook.check', 'parent_id', string="Checks List")
    checks_to_print_qty = fields.Integer("Check to Print", compute="_compute_checks_to_print_qty")
    has_numbers_to_confirm = fields.Boolean("Numbers to Confirm", compute="_compute_has_numbers_to_confirm")
    has_checks_to_print = fields.Boolean("Checks to Print", compute="_compute_has_checks_to_print")
    check_type = fields.Selection(
            [
                ('check', "Check"),
                ('post-dated', "Deferred Check"),
            ], default='check', string="Check Type",
    )
    template_id = fields.Many2one('account.checkbook.template', string="Template")

    @api.depends('check_ids.printed')
    def _compute_has_checks_to_print(self):
        for rec in self:
            rec.has_checks_to_print = len(rec.check_ids.filtered(lambda c: not c.printed)) > 0

    def _compute_has_numbers_to_confirm(self):
        for rec in self:
            rec.has_numbers_to_confirm = len(rec.check_ids.filtered(lambda c: not c.check_id.number)) > 0

    def _compute_checks_to_print_qty(self):
        for rec in self:
            checks = rec.env['account.check'].search_count(
                    [
                        ('checkbook_id', '=', rec.id),
                        ('state', '=', 'in-portfolio'),
                    ]
            )
            rec.checks_to_print_qty = checks

    @api.model_create_multi
    def create(self, vals_list):
        records = super(AccountCheckbook, self).create(vals_list)
        for record in records:
            sequence = self.env['ir.sequence'].sudo().create({
                'name'       : '%s %s %s' % (_("Checkbook"), record.bank_id.name, record.bank_account_id.acc_number),
                'number_next': record.from_number,
                'code'       : 'checkbook.bank%s.account%s' % (record.bank_id.id, record.bank_account_id.id)
            })
            record.sequence_id = sequence
        return records

    @api.depends('bank_id', 'bank_account_id', 'from_number', 'to_number')
    def _compute_name(self):
        for rec in self:
            if not any([rec.bank_id.name, rec.bank_account_id.acc_number, rec.from_number, rec.to_number]):
                rec.name = "checkbook_%s" % (rec.id)
            else:
                rec.name = f"{rec.bank_id.name}-{rec.bank_account_id.acc_number}-[{rec.from_number}-{rec.to_number}]"

    def create_sequence(self, number):
        return "%s%s%s" % (self.sequence_id.prefix or "",
                           str(number).rjust(self.sequence_id.padding, "0"),
                           self.sequence_id.suffix or "")

    def preview_checks(self):
        checks = self.env['account.check'].search(
                [
                    ('checkbook_id', '=', self.id),
                    ('type', '=', 'own'),
                    ('state', '=', 'in-portfolio'),
                ], order="id"
        )
        check_ids = [(5, 0, 0)]
        sequence_nr = self.sequence_id.number_next_actual
        sequence_error = False
        for chk in checks:
            if chk.number:
                check_number = chk.number
            else:
                if sequence_nr >= self.from_number and sequence_nr <= self.to_number:
                    check_number = self.create_sequence(sequence_nr)
                else:
                    check_number = _("N/A")
                    sequence_error = True
                sequence_nr += 1
            check_ids.append(
                    (0, 0, {
                        'check_id'      : chk.id,
                        'preview_number': check_number,
                        'sequence_error': sequence_error,
                    })
            )
        self.check_ids = check_ids

    def confirm_numbers(self):
        for chk in sorted(self.check_ids, key=lambda c: c.sequence):
            if chk.sequence_error:
                chk.unlink()
                continue
            if not chk.check_id.number:
                sequence_do = self.sequence_id.next_by_id()
                chk.preview_number = sequence_do
                chk.check_id.write(
                        {'number'      : sequence_do,
                         'checkbook_id': self.id})

    @api.onchange('check_ids')
    def _onchange_check_ids(self):
        sequence_nr = self.sequence_id.number_next_actual
        for chk in sorted(self.check_ids, key=lambda c: c.sequence):
            if chk.number:
                chk.preview_number = chk.number
            else:
                chk.preview_number = self.create_sequence(sequence_nr)
                sequence_nr += 1

    def assign_checkbook(self):
        wizard = self.env['assign.checkbook'].create(
                {
                    'bank_id'        : self.bank_id.id,
                    'bank_account_id': self.bank_account_id.id,
                }
        )
        return {
            'type'     : 'ir.actions.act_window',
            'name'     : _('Assign Checkbook'),
            'res_model': 'assign.checkbook',
            'view_mode': 'form',
            'target'   : 'new',
            'res_id'   : wizard.id,
        }

    def print_checks(self):
        return self.template_id.report_id.report_action(self)


class AccountCheckbookCheck(models.Model):
    _name = 'account.checkbook.check'
    _description = 'Account Checkbook Check'

    parent_id = fields.Many2one('account.checkbook')
    sequence = fields.Integer("Sequence")
    check_id = fields.Many2one('account.check')
    preview_number = fields.Char("Preview Number")
    payee = fields.Char("Payee", related='check_id.payee')
    currency_id = fields.Many2one('res.currency', string="Currency", related='check_id.currency_id')
    amount = fields.Monetary("Amount", related='check_id.amount')
    number = fields.Char("Number", related='check_id.number')
    state = fields.Selection(related='check_id.state')
    printed = fields.Boolean("Printed")
    sequence_error = fields.Boolean("Sequence Error")
