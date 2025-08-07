from odoo import models, api, fields, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    binding_model_id = fields.Many2one('ir.model', string="Model")
    stamped_number = fields.Char("Stamped Number")
    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    from_number = fields.Integer("Stamped From Number")
    to_number = fields.Integer("Stamped To Number")
    establishment = fields.Char("Establishment")
    dispatch_point = fields.Char("Dispatch Point")
    stamped_required = fields.Boolean('Stamped Required', compute="_compute_stamped_required")
    journal_id = fields.Many2one('account.journal', string="Journal")

    @api.depends('binding_model_id')
    def _compute_stamped_required(self):
        for rec in self:
            rec.stamped_required = False
            if rec.binding_model_id.model in ['account.move', 'stock.picking']:
                rec.stamped_required = True

    def check_stamped_number(self, date):
        if not self.stamped_number:
            return True
        msg = _("Number not available\nStamped number : %s\n%s - %s\n%s - %s" % (self.stamped_number,
                                                                                 self.from_date,
                                                                                 self.to_date,
                                                                                 self.from_number, self.to_number))

        if date and (date < self.from_date or date > self.to_date) \
                or (self.number_next_actual < self.from_number or self.number_next_actual > self.to_number):
            raise UserError(msg)

    def get_next_char(self, number_next):
        if self.code == 'sale.order' and self.prefix == "S" and number_next[0] >= 100000:
            if self.padding != 8:
                self.write({'padding': 8})
                _logger.info("NUEVO PADDING PARA sale.order", self.padding)
        interpolated_prefix, interpolated_suffix = self._get_prefix_suffix()
        return interpolated_prefix + '%%0%sd' % self.padding % number_next + interpolated_suffix
