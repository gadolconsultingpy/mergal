# create_date: 2025-06-06 14:27:55.222215
<<<<<<< Updated upstream
# write_date: 2025-08-21 12:23:37.182879
=======
# write_date: 2025-08-21 13:10:17.018663
>>>>>>> Stashed changes
# name: sifen.account.move.check
# comment: Validaciones al Confirmar Facturas

from odoo.exceptions import UserError

if record.move_type in ['out_invoice','out_refund']:
    if not record.partner_id.vat:
      _logger.info("El Contacto no tiene RUC")
    if not record.partner_id.street_number:
      _logger.info("Falta Nro. de Casa en la Dirección del Cliente")
      # raise UserError()