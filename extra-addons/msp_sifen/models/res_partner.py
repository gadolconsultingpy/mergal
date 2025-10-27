from odoo import api, models, fields, _
import html


class ResPartner(models.Model):
    _inherit = 'res.partner'

    edi_event_qty = fields.Integer('EDI Events Qty', compute='_compute_edi_event_qty')
    edi_batch_qty = fields.Integer('EDI Batch Qty', compute='_compute_edi_batch_qty')

    def sifen_procedure(self):
        self.env['edi.procedure'].run_procedure(self, "sifen.res.partner.vat.consult")

    def get_escaped_name(self):
        return html.escape(self.name)

    def _compute_edi_event_qty(self):
        for rec in self:
            rec.edi_event_qty = self.env['edi.event'].search_count(
                    [('res_model', '=', self._name), ('res_id', '=', rec.id)])

    def _compute_edi_batch_qty(self):
        for rec in self:
            query = "SELECT COUNT(edi_batch_id) cnt "
            query += "FROM res_partner_edi_batch_rel "
            query += "WHERE res_partner_id = %s " % (rec.id)
            self._cr.execute(query)
            rec.edi_batch_qty = self._cr.dictfetchall()[0]['cnt']

    def open_edi_events(self):
        event_ids = self.env['edi.event'].search(
                [
                    ('res_model', '=', self._name), ('res_id', '=', self.id)
                ]
        )
        if not event_ids:
            return
        # for eve in event_ids:
        #     print("EVENTS", eve.id, eve.name)
        action = {'type'     : 'ir.actions.act_window',
                  'name'     : _('EDI Events'),
                  'res_model': 'edi.event'}
        if len(event_ids) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = event_ids.id
        elif len(event_ids) > 1:
            action['view_mode'] = 'list,form'
            action['domain'] = [('id', 'in', event_ids.ids)]
        return action