from odoo import _, fields, models, api
import logging
import jinja2

_logger = logging.getLogger(__name__)


class RecConfigCustom(models.Model):
    _inherit = 'res.config.custom'

    invoice_logo_text = fields.Html("Invoice Logo Text")
    invoice_header = fields.Html("Invoice Header")
    invoice_footer = fields.Html("Invoice Footer")
    invoice_footer_edi_text = fields.Html("Invoice Footer EDI")
    edi_email_template_id = fields.Many2one(comodel_name='mail.template',
                                            string="Email Template",
                                            domain=[('model_id.model', '=', 'account.move')])
    edi_email_sender = fields.Char("Email Sender")
    edi_email_to_partner = fields.Boolean("Send to Partner")
    edi_report_action = fields.Many2one('ir.actions.report',string="EDI Report")
    edi_start_date = fields.Date("EDI Start Date", default="2023-10-01")

    tax1_id = fields.Many2one('account.tax', "Tax 1")  # Excempt
    tax2_id = fields.Many2one('account.tax', "Tax 2")  # 5%
    tax3_id = fields.Many2one('account.tax', "Tax 3")  # 10%

    default_edi_transaction_type = fields.Many2one('edi.transaction.type', string="Default EDI Transaction Type")
    default_edi_tax_type = fields.Many2one('account.tax.type', string="Default EDI Tax Type")
    default_edi_presence_id = fields.Many2one('edi.presence', string="Default EDI Presence")

    invalid_document_partner_id = fields.Many2one('res.partner',string="Invalid Document Partner")
    invalid_document_payment_term_id = fields.Many2one('account.payment.term',string="Invalid Document Payment Term")
    unnamed_partner_id = fields.Many2one('res.partner',string="Unnamed Partner")

    def get_invoice_footer(self, **kwargs):
        env = jinja2.Environment()
        template = env.from_string(self.invoice_footer)
        content = template.render(kwargs)
        return content

    def get_invoice_footer_edi_text(self, **kwargs):
        env = jinja2.Environment()
        template = env.from_string(self.invoice_footer_edi_text)
        content = template.render(kwargs)
        return content
