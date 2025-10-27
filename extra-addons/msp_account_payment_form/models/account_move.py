from odoo import api, models, fields, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    payment_form_ids = fields.One2many('account.move.payment.form', 'move_id', string="Payment Forms")
    require_cash_payment = fields.Boolean('Require Cash Payment',
                                          related="invoice_payment_term_id.require_payment_form")
    payment_total = fields.Monetary("Payment Total", compute="_compute_payment_total",
                                    currency_field='company_currency_id')

    @api.depends('payment_form_ids')
    def _compute_payment_total(self):
        for rec in self:
            rec.payment_total = sum([x.amount for x in rec.payment_form_ids])

    def action_post(self):  # OK
        for rec in self:
            rec.check_cash_payments()
        return super(AccountMove, self).action_post()

    def _post(self, soft=False):
        records = super(AccountMove, self)._post(soft=soft)
        for rec in records:
            config = self.env['res.config.custom'].get_company_custom_config(company_id=rec.company_id.id)
            if not config:
                raise UserError(_('No config found for this account.'))
            if not config.skip_cash_payment_create:
                rec.create_cash_payments()
        return records

    def check_cash_payments(self):
        for record in self:
            if record.move_type not in ['out_refund', 'out_invoice']:
                return
            if record.invoice_payment_term_id.require_payment_form:
                if not record.payment_form_ids:
                    msg = _("Payment Forms Required for Term: %s") % (record.invoice_payment_term_id.name)
                    raise UserError(msg)
                if record.currency_id.compare_amounts(record.payment_total, abs(record.amount_total_signed)) != 0:
                    msg = _("Payment Total Does Not Match Invoice Total")
                    raise UserError(msg)

    def button_draft(self):
        for move in self:
            print("MOVE State", move.id, move.name, move.state)
        super(AccountMove, self).button_draft()
        for move in self:
            if move.payment_form_ids:
                for pform in move.payment_form_ids:
                    payment = move.env['account.payment'].search([('move_payment_form_id', '=', pform.id)])
                    if payment:
                        payment.action_draft()
                        _logger.info("Deleting Cash Payment %s" % (payment.name))
                        res = payment.unlink()
                        if not res:
                            msg = _("Can Not Delete Invoice Cash Payment")
                            raise UserError(msg)

    def create_cash_payments(self):
        for record in self:
            if record.state != 'posted':
                return
            if record.move_type not in ['out_refund', 'out_invoice']:
                return
            if record.payment_form_ids:
                for payment in record.payment_form_ids:
                    context = record._context.copy()
                    context['active_model'] = 'account.move'
                    context['active_ids'] = record.id

                    vals = {}
                    vals['journal_id'] = payment.payment_form_id.journal_id.id
                    vals['amount'] = payment.amount
                    vals['currency_id'] = payment.company_currency_id.id
                    vals['communication'] = record.name
                    vals['payment_date'] = record.invoice_date
                    vals['payment_form_id'] = payment.payment_form_id.id
                    vals['move_payment_form_id'] = payment.id

                    register_payments = record.env['account.payment.register'].with_context(context).create(vals)
                    payments = register_payments.with_context(context)._create_payments()
                    for pp in payments:
                        _logger.info("Creating Cash Payment %s" % (pp.name))

    def action_payment_auto(self):
        self.ensure_one()
        if not self.invoice_payment_term_id.require_payment_form:
            return
        """Create a payment form for the invoice and open the payment form view."""
        config = self.env['res.config.custom'].get_company_custom_config(company_id=self.company_id.id)
        if config.cash_payment_form_id:
            form_ids = [(5, 0, 0)]
            vals = {}
            vals['payment_form_id'] = config.cash_payment_form_id.id
            vals['payment_amount'] = self.amount_total
            vals['payment_currency_id'] = self.currency_id.id
            vals['amount'] = self.amount_total
            form_ids.append((0, 0, vals))
            self.payment_form_ids = form_ids

    def complete_security_code(self):
        if self.control_code and not self.security_code:
            security_code = self.control_code[34:-1]
            self.security_code = security_code


class AccountMovePaymentForm(models.Model):
    _name = 'account.move.payment.form'
    _description = 'Invoice Payment Form'

    display_name = fields.Char("Name", compute="_compute_display_name")
    move_id = fields.Many2one('account.move')
    # payment amount and currency as received from customer
    payment_currency_id = fields.Many2one('res.currency',
                                          string="Payment Currency",
                                          default=lambda self: self.env.company.currency_id.id)
    payment_amount = fields.Monetary('Payment Amount', currency_field='payment_currency_id')
    payment_currency_rate = fields.Float("Payment Currency Rate")
    # amount and currency_id always related to invoice currency
    company_currency_id = fields.Many2one('res.currency',
                                          string="Currency", related='move_id.company_currency_id')
    amount = fields.Monetary('Amount', required=True, currency_field='company_currency_id')
    payment_form_id = fields.Many2one('account.payment.form', string="Payment Form", required=True)
    payment_form_type = fields.Selection(related="payment_form_id.type")
    bank_id = fields.Many2one('res.bank', string="Bank")
    issuer_id = fields.Many2one('card.issuer', string="Issuer")
    number = fields.Char("Number")
    date = fields.Date("Date")
    postdated_date = fields.Date("Postdated Date")
    require_number = fields.Boolean("Require Number", related="payment_form_id.require_number")
    require_bank = fields.Boolean("Require Bank", related="payment_form_id.require_bank")
    require_date = fields.Boolean("Require Date", related="payment_form_id.require_date")
    require_postdated_date = fields.Boolean("Require Postdated Date", related="payment_form_id.require_postdated_date")
    require_issuer = fields.Boolean("Require Issuer", related="payment_form_id.require_issuer")

    @api.onchange('payment_amount', 'payment_currency_id', 'payment_currency_rate')
    def _onchange_amount(self):
        if self.payment_currency_id.id != self.company_currency_id.id:
            ctx = self.env.context.copy()
            ctx['custom_currency_rate'] = self.payment_currency_rate or 1
            self.amount = self.payment_currency_id.with_context(ctx)._convert(from_amount=self.payment_amount,
                                                                              to_currency=self.company_currency_id,
                                                                              company=self.move_id.company_id,
                                                                              date=self.move_id.invoice_date,
                                                                              round=True)
        else:
            self.payment_currency_rate = 1
            self.amount = self.payment_amount

    @api.depends('payment_form_id', 'bank_id', 'number', 'amount')
    def _compute_display_name(self):
        for rec in self:
            base_name = "%s %s" % (rec.payment_form_id.name, rec.company_currency_id.name)
            if rec.payment_form_type in ['check', 'deferred-check', 'bank']:
                rec.display_name = "%s, %s, %s" % (base_name, rec.bank_id.name, rec.number)
            elif rec.payment_form_type == 'voucher':
                rec.display_name = "%s, %s" % (base_name, rec.number)
            else:
                rec.display_name = base_name
