from odoo import api, models, fields, _
from odoo.exceptions import UserError


class EDIDocumentNomination(models.Model):
    _inherit = ['mail.thread']
    _name = 'edi.document.nomination'
    _description = 'Document Nomination'

    name = fields.Char("Name")
    edi_document_type = fields.Many2one('edi.document.type', string="Document Type")
    edi_document_type_code = fields.Char("Document Type Code", related='edi_document_type.code')
    invoice_id = fields.Many2one('account.move', string="Invoice")
    picking_id = fields.Many2one('stock.picking', string="Picking")
    control_code = fields.Char("Control Code", compute="_compute_control_code")
    document_number = fields.Char("Document Number", compute="_compute_document_number")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company.id)
    partner_id = fields.Many2one('res.partner', string="New Partner")
    unnamed_partner_id = fields.Many2one('res.partner', string="Unnamed Partner")
    reason = fields.Char("Reason")
    state = fields.Selection(
            [
                ('draft', 'Draft'),
                ('confirm', 'Confirmed'),
                ('sent', 'Sent'),
            ], default='draft', string="State"
    )

    @api.depends('invoice_id', 'picking_id')
    def _compute_control_code(self):
        for rec in self:
            if rec.invoice_id:
                rec.control_code = rec.invoice_id.control_code
            elif rec.picking_id:
                rec.control_code = rec.picking_id.control_code
            else:
                rec.control_code = False

    @api.depends('invoice_id', 'picking_id')
    def _compute_document_number(self):
        for rec in self:
            if rec.invoice_id:
                rec.document_number = rec.invoice_id.name
            elif rec.picking_id:
                rec.document_number = rec.picking_id.name
            else:
                rec.document_number = False

    def default_get(self, fields):
        vals = super(EDIDocumentNomination, self).default_get(fields)
        config = self.env['res.config.custom'].get_company_custom_config(company_id=self.company_id.id)
        if not config:
            msg = _("Missing Custom Configuration for Company: %s" % (self.company_id.name))
            raise UserError(msg)
        vals['unnamed_partner_id'] = config.unnamed_partner_id.id
        return vals

    def get_operation_type(self):
        otype = {}
        otype['B'] = '1'
        otype["C"] = '2'
        otype["G"] = '3'
        otype["F"] = '4'
        return otype.get(self.partner_id.business_partner_type)

    def action_draft(self):
        if self.state == 'confirm':
            self.state = 'draft'

    def action_reset_to_confirm(self):
        if self.state == 'sent':
            self.state = 'confirm'

    def action_confirm(self):
        sequence = self.env['ir.sequence'].search([('code', '=', 'edi.document.nomination')], limit=1)
        if not sequence:
            msg = _("Missing Sequence: %s" % ("edi.document.nomination"))
            raise UserError(msg)
        self.name = sequence.next_by_id()
        self.state = 'confirm'

    def send(self):
        pass

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Only records in draft status can be deleted."))
        return super(EDIDocumentNomination, self).unlink()
