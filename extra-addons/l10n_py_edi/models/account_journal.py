from odoo import api, fields, models, _


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def _default_invoice_type_id(self):
        return self.env['edi.document.type'].search([('code', '=', 'X')])

    invoice_type = fields.Selection([
        ('1', 'Factura electrónica'),
        ('2', 'Factura electrónica de Exportación Futuro'),
        ('3', 'Factura electrónica de Importación Futuro'),
        ('4', 'Autofactura Electrónica'),
        ('5', 'Nota de crédito electrónica'),
        ('6', 'Nota de débito electrónica'),
        ('7', 'Nota de remisión electrónica'),
        ('8', 'Comprobante de retención electrónico Futuro')
    ], default="1", required=True,
    )
    invoice_type_id = fields.Many2one('edi.document.type',
                                      string="Electronic Document Type",
                                      default=_default_invoice_type_id,
                                      help="Tipo de Documento Electrónico (C002)")
