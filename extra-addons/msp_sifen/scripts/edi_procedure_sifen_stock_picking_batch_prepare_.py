# create_date: 2023-10-09 15:56:58.500921
# write_date: 2023-10-09 15:56:58.500921
# name: sifen.stock.picking.batch.prepare
# comment: OK. Busca un edi.batch abierto y encola el comprobante.\nSi no existe el Lote lo crea y si se llega al limite por lineas o tiempo, lo deja en Preparado.

import hashlib
from odoo import fields
from lxml import etree
import re
import zipfile
import base64
import datetime
import requests
import xmltodict

try:
    invoice = record
except:
    pass

filters = []
filters.append(('state','=','open'))
filters.append(('move_type','=','stock_picking'))
filters.append(('company_id','=',invoice.company_id.id))

# Busca los registros edi.batch que contienen el account.move en el campo invoice_ids
edi_batches_containing_move = self.env['edi.batch'].search([('invoice_ids', 'in', [invoice.id])])

if edi_batches_containing_move:
    _logger.info("El account.move está agregado a los siguientes edi.batch:")
    for edi_batch in edi_batches_containing_move:
      _logger.info("EDI Batch ID: %s" %(edi_batch.id))
else:
    _logger.info("El account.move no está agregado a ningún edi.batch.")

edi_batch = self.env['edi.batch'].search(filters)
if not edi_batch:
  evals = {}
  evals['move_type'] = "stock_picking"
  evals['company_id'] = invoice.company_id.id
  edi_batch = self.env['edi.batch'].create(evals)
  invoice.write({'sifen_state':'queue'})
if edi_batch:
  edi_batch.write({'picking_ids':[(4,invoice.id)]})
  edi_batch.check_for_prepared()
  invoice.write({'sifen_state':'queue'})