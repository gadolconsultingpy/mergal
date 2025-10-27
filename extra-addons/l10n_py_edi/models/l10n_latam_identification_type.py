from odoo import api, models, fields, _


class L10NLatamIdentificationType(models.Model):
    _inherit = 'l10n_latam.identification.type'

    edi_code = fields.Char("EDI Code")
    edi_name = fields.Char("EDI Name")