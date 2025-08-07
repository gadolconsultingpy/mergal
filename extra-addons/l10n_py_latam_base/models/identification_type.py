from odoo import api, models, fields, _


class IdentificationType(models.Model):
    _inherit = 'l10n_latam.identification.type'

    fiscal_code = fields.Char("Fiscal Code", help="Used for RG90 Reports")

    def name_get(self):
        result = []
        for record in self:
            name = record.name  # Obtener el campo que deseas mostrar como nombre
            display_name = f"[{record.fiscal_code}] {name}"  # Personalizar el formato del nombre
            result.append((record.id, display_name))
        return result
