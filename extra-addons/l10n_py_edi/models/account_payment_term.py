from odoo import _, api, models, fields
from odoo.exceptions import UserError


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    code = fields.Char("Code")
    credit_type = fields.Selection(
            [
                ('0', 'Contado'),
                ('1', 'Plazo'),
                ('2', 'Cuota')
            ], default='1', string="Condición Operación a Crédito"
    )

    # _sql_constraints = [('unique_code', 'unique(code)', 'The Code Must Be Unique by Company')]

    @api.constrains('code')
    def _check_code(self):
        if self.code:
            other = self.env['account.payment.term'].search(
                    [
                        ('code', '=', self.code),
                        ('id', '!=', self.id)
                    ], limit=1
            )
            if other:
                msg = _("The Code '%s' Is already Used for %s" % (self.code, other.name))
                raise UserError(msg)

