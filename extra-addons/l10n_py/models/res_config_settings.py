import os

from odoo import api, models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    tax_payer_file_input = fields.Char("Tax Payer File Input", config_parameter='l10n_py.tax_payer_file_input')