from odoo import api, models, fields, _


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    document_type_id = fields.Many2one('account.document.type', string='Document Type', ondelete='restrict')
