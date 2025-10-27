from odoo import api, fields, models, _


class AccountPaymentForm(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'account.payment.form'
    _description = 'Payment Forms for Invoice Cancellations'
    _check_company_auto = True

    name = fields.Char("Name")
    code = fields.Char(string="Code", default="99", help="Especifique el código 99 para Formas de Pagos Adicionales")
    journal_id = fields.Many2one('account.journal', string="Journal")
    type = fields.Selection(
            [
                ('cash', 'Cash'),
                ('voucher', 'Voucher'),
                ('card', 'Card'),
                ('bank', 'Bank'),
                ('check', 'Check'),
                ('deferred-check', 'Deferred Check'),
                ('voucher', 'Voucher'),
                ('other', 'Other'),
            ], default='cash', required=True
    )
    payment_method_inbound_id = fields.Many2one('account.payment.method.line', string="Incoming Payment Method",
                                                tracking=True)
    payment_method_outbound_id = fields.Many2one('account.payment.method.line', string="Outgoing Payment Method",
                                                 tracking=True)
    edi_type_id = fields.Many2one('account.payment.form.type', string="EDI Payment Type")
    require_number = fields.Boolean("Require Number")
    voucher_partner = fields.Selection(
            [
                ('partner', 'Partner'),
            ]
    )
    require_bank = fields.Boolean("Require Bank")
    require_date = fields.Boolean("Require Date")
    active = fields.Boolean("Active", default=True)
    bank_id = fields.Many2one('res.bank', string="Bank")
    require_postdated_date = fields.Boolean("Require Postdated Date")
    require_issuer = fields.Boolean("Require Issuer")
    process_form_id = fields.Many2one('card.process.form', string="Card Process Form")
    use_customer = fields.Boolean("Use for Customer")
    use_supplier = fields.Boolean("Use for Supplier", tracking=True)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company.id,
                                 tracking=True)

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if self.journal_id.type == 'bank':
            self.bank_id = self.journal_id.bank_id.id
