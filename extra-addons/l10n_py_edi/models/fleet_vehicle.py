from odoo import api, models, fields, _


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    @api.model
    def get_edi_transport_type_default(self):
        return self.env['edi.transport.type'].search([('code', '=', '1')], limit=1) or False

    @api.model
    def get_edi_transport_mode_default(self):
        return self.env['edi.transport.mode'].search([('code', '=', '1')], limit=1) or False

    edi_transport_type_id = fields.Many2one('edi.transport.type', string='EDI Transport Type',
                                            default=get_edi_transport_type_default, )

    edi_transport_mode_id = fields.Many2one('edi.transport.mode', string='EDI Transport Mode',
                                            default=get_edi_transport_mode_default, )
