# create_date: 2023-10-09 15:56:58.500921
# write_date: 2023-10-09 15:56:58.500921
# name: sifen.stock.picking.check
# comment: Validaciones al Confirmar Stock Picking


from odoo.exceptions import UserError

if record.sequence_id:
  # Contacto Entrega
  if not record.partner_id.state_id:
    raise UserError("Falta Departamento en Contacto de Entrega")
  if not record.partner_id.location_id:
    raise UserError("Falta Ciudad en Contacto de Entrega")
  # Vehiculo
  if not record.vehicle_id:
    raise UserError("Falta Datos del Vehiculo")
  # Chofer
  if not record.driver_id:
    raise UserError("Falta Datos del Chofer")
  if not record.driver_id.state_id:
    raise UserError("Falta Departamento en Dirección del Chofer")
