from odoo import api, models, fields

# Los textos quedan literal es español ya que forman parte del catálogo de la SET,
# no se deben traducir para evitar errores en el envio de datos.

class ResCompany(models.Model):
    _inherit = 'res.company'

    # borrowed from base_address_extended
    # cannot install base_address_extended because the init_hook updates (it is not applicable to py)
    street_name = fields.Char('Street Name')
    street_number = fields.Char('House Number')
    street_number2 = fields.Char('Door Number')
    tax_payer_type = fields.Selection(
        [
            ('1', 'Persona Física'),
            ('2', 'Persona Jurídica'),
        ], default='2'
    )
    district_id = fields.Many2one('res.district', string="District", related='partner_id.district_id')
    location_id = fields.Many2one('res.location', string="Location", related='partner_id.location_id')
    neighborhood_id = fields.Many2one('res.neighborhood', string="Neighborhood", related='partner_id.neighborhood_id')
    company_activity_ids = fields.Many2many('res.company.activity', string="Company Economic Activity")

    @api.onchange('street_name')
    def _onchange_street_name(self):
        self.street = self.street_name

    @api.onchange('location_id')
    def _onchange_location_id(self):
        self.city = self.location_id.name
