from odoo import _, api, models, fields
from odoo.exceptions import UserError
import datetime
import string
import re
import stdnum
from stdnum.eu.vat import check_vies
from stdnum.exceptions import InvalidComponent
from stdnum.util import clean

import logging

from odoo import api, models, fields, tools, _
from odoo.tools.misc import ustr
from odoo.exceptions import ValidationError

_eu_country_vat = {
    'GR': 'EL'
}

_eu_country_vat_inverse = {v: k for k, v in _eu_country_vat.items()}


class ResPartner(models.Model):
    _inherit = "res.partner"

    # borrowed from base_address_extended
    # cannot install base_address_extended because the init_hook updates (it is not applicable to py)
    street_name = fields.Char('Street Name')
    street_number = fields.Char('House')
    street_number2 = fields.Char('Door')
    district_id = fields.Many2one('res.district', string="Py District")
    location_id = fields.Many2one('res.location', string="Py Location")
    neighborhood_id = fields.Many2one('res.neighborhood', string="Py Neighborhood")
    district_name = fields.Char("District Name", related='district_id.name')
    location_name = fields.Char("City or Location Name", related='location_id.name')
    neighborhood_name = fields.Char("Neighborhood Name", related='neighborhood_id.name')
    fantasy_name = fields.Char("Fantasy Name")

    def default_get(self, default_fields):
        values = super(ResPartner, self).default_get(default_fields)
        values['country_id'] = self.env.company.country_id.id
        return values

    @api.onchange('street_name')
    def _onchange_street_name(self):
        self.street = self.street_name

    nature = fields.Selection(
            [
                ('1', 'Contributor'),
                ('2', 'Not Contributor'),
            ], default='1', required=True
    )
    business_partner_type = fields.Selection(
            [
                ('B', 'Business'),
                ('C', 'Consumer'),
                ('G', 'Government'),
                ('F', 'Foreign'),
            ], default="C", required=True
    )
    tax_payer_type = fields.Selection(
            [
                ('1', 'Physic'),
                ('2', 'Juridic'),
            ], default='2'
    )

    @api.onchange('location_id')
    def _onchange_location_id(self):
        self.city = self.location_id.name

    @api.model
    def _address_fields(self):
        res = super(ResPartner, self)._address_fields()
        """Returns the list of address fields that are synced from the parent."""
        res.extend(
                ['district_id',
                 'location_id',
                 'neighborhood_id',
                 'district_name',
                 'location_name',
                 'neighborhood_name',
                 'street_name',
                 'street_number'])
        return res

    def check_address_fields(self):
        if not self.street_name or not self.street_name.strip():
            msg = _("Street Field is Mandatory")
            raise UserError(msg)
        check_fields = ['country_id', 'street_number', 'state_id', 'district_id', 'location_id']
        for cf in check_fields:
            value = getattr(self, cf)
            if not value:
                fieldlabel = self._fields[cf].get_description(self.env).get('string')
                msg = _("This Field on Partner Address is Mandatory")
                raise UserError("%s: %s" % (msg, fieldlabel))

    @api.model
    def check_vat_PY(self, vat):
        if vat == "XX":
            return True
        if len(vat.split("-")) != 2:
            return False
        pattern = "^[0-9A-Z]{5,9}-[0-9]$"
        if not re.match(pattern, vat):
            return False
        if len(vat.split("-")[1]) != 1:
            return False
        return True

    @api.model
    def check_vat_py(self, vat):
        res = self.check_vat_PY(vat)
        return res
