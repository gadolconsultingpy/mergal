from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sifen_status = fields.Selection(
            [
                ('ACT', "Activo"),
                ('SUS', "Suspensión Temporal"),
                ('SAD', "Suspensión Administrativa"),
                ('BLQ', "Bloqueado"),
                ('CAN', "Cancelado"),
                ('CDE', "Cancelado Definitivo"),
            ], string="SIFEN Status"
    )
    sifen_issuer = fields.Boolean("Electronic Issuer")
    document_type_id = fields.Many2one('l10n_latam.identification.type', string="Document Type")
    document_number = fields.Char("Document Number")
