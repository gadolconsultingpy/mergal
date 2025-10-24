from odoo import _, api, models, fields
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    document_type_id = fields.Many2one('account.document.type',
                                       string='Document Type',
                                       compute="_compute_document_type_id",
                                       store=True)
    sale_document_type_id = fields.Many2one('account.document.type',
                                            string='Sale Document Type',
                                            domain=[('sales', '=', True)], )
    purchase_document_type_id = fields.Many2one('account.document.type',
                                                string='Purchase Document Type',
                                                domain=[('purchases', '=', True)],
                                                )
    stamped_id = fields.Many2one('res.partner.stamped', string="Stamped Number")
    stamped_control = fields.Boolean(related='document_type_id.stamped_control', string="Stamped Control")

    @api.onchange('journal_id')
    def _onchange_journal_id_document_type(self):
        if self.journal_id and self.journal_id.document_type_id:
            if self.journal_id.type == 'sale':
                self.sale_document_type_id = self.journal_id.document_type_id.id
            elif self.journal_id.type == 'purchase':
                self.purchase_document_type_id = self.journal_id.document_type_id.id


    def default_get(self, fields_list):
        vals = super(AccountMove, self).default_get(fields_list)
        ctx = self.env.context.copy()
        if ctx.get('default_move_type') in ('out_invoice', 'out_refund'):
            stamped = self.env['res.partner.stamped'].search(
                    [
                        ('partner_id', '=', self.company_id.partner_id.id),
                        ('to_date', '>=', fields.Date.context_today(self)),
                    ], order='from_date desc', limit=1
            )
            if stamped:
                self.stamped_id = stamped.id
        return vals

    @api.depends('sale_document_type_id', 'purchase_document_type_id')
    def _compute_document_type_id(self):
        for rec in self:
            if rec.move_type in ('out_invoice', 'out_refund'):
                rec.document_type_id = rec.sale_document_type_id
            elif rec.move_type in ('in_invoice', 'in_refund'):
                rec.document_type_id = rec.purchase_document_type_id
            else:
                rec.document_type_id = False

    @api.onchange('partner_id')
    def _onchange_partner_id_stamped(self):
        if self.move_type in ('in_invoice', 'in_refund'):
            if self.partner_id:
                stamped = self.env['res.partner.stamped'].search(
                        [
                            ('partner_id', '=', self.partner_id.id),
                            ('to_date', '>=', fields.Date.context_today(self)),
                        ], order='from_date desc'
                )
                if len(stamped) == 1:
                    self.stamped_id = stamped.id
                else:
                    self.stamped_id = False

    def action_post(self):  # Ok
        self.check_stamped_control()
        return super(AccountMove, self).action_post()

    @api.onchange('ref')
    def _onchange_ref_invoice_nr(self):
        separators = ["-", ".", " "]
        if self.document_type_id.stamped_control and self.move_type in ['in_invoice', 'in_refund']:
            for sep in separators:
                if self.ref and len(self.ref.split(sep)) == 3:
                    est, dp, nr = self.ref.split(sep)
                    self.ref = "%s-%s-%s" % (est.zfill(3), dp.zfill(3), nr.zfill(7))

    def check_stamped_control(self):
        for rec in self:
            if rec.move_type in ['in_invoice', 'in_refund'] and rec.document_type_id.stamped_control:
                try:
                    number = rec.ref.split("-")[2]
                except BaseException as errstr:
                    msg = _("The Number %s Does Not Match the Format 999-999-9999999") % (rec.ref)
                    raise UserError(msg)
                if not rec.invoice_date:
                    msg = _("Invoice Date Missing")
                    raise UserError(msg)
                if int(number) < rec.stamped_id.from_number or int(number) > rec.stamped_id.to_number:
                    msg = "Document Number %s Is Not in the Authorized Range: " % (number)
                    msg += "%s : %s" % (rec.stamped_id.from_number,
                                        rec.stamped_id.to_number)
                    raise UserError(msg)
                elif rec.invoice_date < rec.stamped_id.from_date or rec.invoice_date > rec.stamped_id.to_date:
                    date_format = "%d/%m/%Y"
                    msg = "Document Date %s Is Not in the Authorized Range: " % (rec.invoice_date)
                    msg += "%s : %s" % (rec.stamped_id.from_date.strftime(date_format),
                                        rec.stamped_id.to_date.strftime(date_format))
                    raise UserError(msg)
        return True
