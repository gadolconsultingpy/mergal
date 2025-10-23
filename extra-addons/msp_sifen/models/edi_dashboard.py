from odoo import api, models, fields, _


class EDIDashboard(models.Model):
    _name = 'edi.dashboard'
    _description = 'Dashboard'
    _order = 'sequence'

    name = fields.Char("Name", translate=True)
    edi_type = fields.Selection(
            [
                ('invoice', 'Invoice'),
                ('refund', 'Credit Note'),
                ('picking', 'Stock Picking'),
                ('cancel', 'Cancellation'),
                ('invalid', 'Invalidation'),
                ('batch', 'Batch'),
                ('event', 'Event'),
            ], default='invoice', string="Model"
    )
    stat_type = fields.Selection(
            [
                ('edi', 'EDI'),
                ('batch', 'Batch'),
                ('event', 'Event'),
            ], default='edi', string="Statistic Type"
    )
    sequence = fields.Integer("Sequence", readonly=True)
    # edi fields
    pending_qty = fields.Integer("Pending", compute="_compute_records")
    queue_qty = fields.Integer("Queue", compute="_compute_records")
    approved_qty = fields.Integer("Approved", compute="_compute_records")
    rejected_qty = fields.Integer("Rejected", compute="_compute_records")
    # batch fields
    open_qty = fields.Integer("Open", compute="_compute_records")
    prepared_qty = fields.Integer("Prepared", compute="_compute_records")
    sent_qty = fields.Integer("Sent", compute="_compute_records")
    sent_sifen_qty = fields.Integer("Sent to Sifen", compute="_compute_records")
    received_qty = fields.Integer("Received", compute="_compute_records")
    finished_qty = fields.Integer("Finished", compute="_compute_records")
    expired_qty = fields.Integer("Expired", compute="_compute_records")
    html_color = fields.Char("Html Color")

    # event fields
    def _compute_records(self):
        fields_map = ['pending_qty', 'queue_qty', 'approved_qty', 'rejected_qty',
                      'open_qty', 'prepared_qty', 'sent_qty', 'sent_sifen_qty', 'received_qty', 'finished_qty',
                      'expired_qty']
        search_map = {}
        # Invoice mapping
        search_map['invoice'] = {}
        search_map['invoice']['model'] = 'account.move'
        search_map['invoice']['pending_qty'] = [
            ('move_type', '=', 'out_invoice'),
            ('sifen_state', '=', 'pending'),
            ('state', '=', 'posted')
        ]
        search_map['invoice']['queue_qty'] = [
            ('move_type', '=', 'out_invoice'),
            ('sifen_state', 'in', ['queue', 'sent']),
            ('state', '=', 'posted')
        ]
        search_map['invoice']['approved_qty'] = [
            ('move_type', '=', 'out_invoice'),
            ('sifen_state', '=', 'approved'),
            ('state', '=', 'posted')
        ]
        search_map['invoice']['rejected_qty'] = [
            ('move_type', '=', 'out_invoice'),
            ('sifen_state', '=', 'rejected'),
            ('state', '=', 'posted')
        ]
        # Refund mapping
        search_map['refund'] = {}
        search_map['refund']['model'] = 'account.move'
        search_map['refund']['pending_qty'] = [
            ('move_type', '=', 'out_refund'),
            ('sifen_state', '=', 'pending'),
            ('state', '=', 'posted')
        ]
        search_map['refund']['queue_qty'] = [
            ('move_type', '=', 'out_refund'),
            ('sifen_state', 'in', ['queue', 'sent']),
            ('state', '=', 'posted')
        ]
        search_map['refund']['approved_qty'] = [
            ('move_type', '=', 'out_refund'),
            ('sifen_state', '=', 'approved'),
            ('state', '=', 'posted')
        ]
        search_map['refund']['rejected_qty'] = [
            ('move_type', '=', 'out_refund'),
            ('sifen_state', '=', 'rejected'),
            ('state', '=', 'posted')
        ]
        # Picking mapping
        search_map['picking'] = {}
        search_map['picking']['model'] = 'stock.picking'
        search_map['picking']['pending_qty'] = [
            ('picking_type_id.code', '=', 'outgoing'),
            ('sifen_state', '=', 'pending'),
            ('state', '=', 'done')
        ]
        search_map['picking']['queue_qty'] = [
            ('picking_type_id.code', '=', 'outgoing'),
            ('sifen_state', 'in', ['queue', 'sent']),
            ('state', '=', 'done')
        ]
        search_map['picking']['approved_qty'] = [
            ('picking_type_id.code', '=', 'outgoing'),
            ('sifen_state', '=', 'approved'),
            ('state', '=', 'done')
        ]
        search_map['picking']['rejected_qty'] = [
            ('picking_type_id.code', '=', 'outgoing'),
            ('sifen_state', '=', 'rejected'),
            ('state', '=', 'done')
        ]

        # Cancellation mapping
        search_map['cancel'] = {}
        search_map['cancel']['model'] = 'account.move.cancel'
        search_map['cancel']['pending_qty'] = [
            ('state', '=', 'confirm'),
            ('sifen_state', '=', 'pending')
        ]
        search_map['cancel']['queue_qty'] = [
            ('state', '=', 'confirm'),
            ('sifen_state', 'in', ['queue', 'sent'])
        ]
        search_map['cancel']['approved_qty'] = [
            ('state', '=', 'confirm'),
            ('sifen_state', '=', 'approved')
        ]
        search_map['cancel']['rejected_qty'] = [
            ('state', '=', 'confirm'),
            ('sifen_state', '=', 'rejected')
        ]

        # Invalidation mapping
        search_map['invalid'] = {}
        search_map['invalid']['model'] = 'account.move.invalid'
        search_map['invalid']['pending_qty'] = [
            ('state', '=', 'confirm'),
            ('sifen_state', '=', 'pending')
        ]
        search_map['invalid']['queue_qty'] = [
            ('state', '=', 'confirm'),
            ('sifen_state', 'in', ['queue', 'sent'])
        ]
        search_map['invalid']['approved_qty'] = [
            ('state', '=', 'confirm'),
            ('sifen_state', '=', 'approved')
        ]
        search_map['invalid']['rejected_qty'] = [
            ('state', '=', 'confirm'),
            ('sifen_state', '=', 'rejected')
        ]

        # Batch mapping
        search_map['batch'] = {}
        search_map['batch']['model'] = 'edi.batch'
        search_map['batch']['open_qty'] = [
            ('state', '=', 'open')
        ]
        search_map['batch']['prepared_qty'] = [
            ('state', '=', 'prepared')
        ]
        search_map['batch']['sent_qty'] = [
            ('state', '=', 'sent')
        ]

        search_map['batch']['queue_qty'] = [
            ('sifen_state', '=', 'queue')
        ]
        search_map['batch']['sent_sifen_qty'] = [
            ('sifen_state', '=', 'sent')
        ]
        search_map['batch']['received_qty'] = [
            ('sifen_state', '=', 'received')
        ]
        search_map['batch']['finished_qty'] = [
            ('sifen_state', '=', 'finish'),
            ('expired', '=', False)
        ]
        search_map['batch']['expired_qty'] = [
            ('sifen_state', '=', 'finish'),
            ('expired', '=', True)
        ]
        search_map['batch']['rejected_qty'] = [
            ('sifen_state', '=', 'rejected')
        ]

        # Event mapping
        search_map['event'] = {}
        search_map['event']['model'] = 'edi.event'
        search_map['event']['pending_qty'] = [
            ('state', '=', 'pending'),
        ]
        search_map['event']['sent_qty'] = [
            ('state', '=', 'sent'),
        ]
        search_map['event']['finished_qty'] = [
            ('state', '=', 'finished'),
        ]

        for rec in self:
            for fmap in fields_map:
                rec.write({fmap: 0})
                for edi_type in search_map.keys():
                    if fmap not in search_map[edi_type]:
                        continue
                    if rec.edi_type != edi_type:
                        continue
                    model = search_map[edi_type]['model']
                    filters = search_map[edi_type][fmap]
                    qty = self.env[model].search_count(filters)
                    rec.sudo().write({fmap: qty})

    def open_statistic_table(self):
        if self.edi_type == 'invoice':
            return {
                'type'     : 'ir.actions.act_window',
                'name'     : _('Invoice'),
                'res_model': 'account.move',
                'context'  : {'list_view_ref': 'account.view_out_invoice_tree',
                              'form_view_ref': 'account.view_move_form'},
                'view_mode': 'list,form',
                'target'   : 'current',
                'domain'   : [('state', '=', 'posted'), ('move_type', '=', 'out_invoice')],
            }
        elif self.edi_type == 'refund':
            return {
                'type'     : 'ir.actions.act_window',
                'name'     : _('Credit Note'),
                'res_model': 'account.move',
                'context'  : {'list_view_ref': 'account.view_out_invoice_tree',
                              'form_view_ref': 'account.view_move_form'},
                'view_mode': 'list,form',
                'target'   : 'current',
                'domain'   : [('state', '=', 'posted'), ('move_type', '=', 'out_refund')],
            }
        elif self.edi_type == 'picking':
            return {
                'type'     : 'ir.actions.act_window',
                'name'     : _('Transference'),
                'res_model': 'stock.picking',
                'view_mode': 'list,form',
                'target'   : 'current',
                'domain'   : [('state', '=', 'done'), ('picking_type_id.code', '=', 'outgoing')],
            }
        elif self.edi_type == 'cancel':
            return {
                'type'     : 'ir.actions.act_window',
                'name'     : _('Cancellation'),
                'res_model': 'account.move.cancel',
                'view_mode': 'list,form',
                'target'   : 'current',
                'domain'   : [],
            }
        elif self.edi_type == 'invalid':
            return {
                'type'     : 'ir.actions.act_window',
                'name'     : _('Invalidation'),
                'res_model': 'account.move.invalid',
                'view_mode': 'list,form',
                'target'   : 'current',
                'domain'   : [],
            }
        elif self.edi_type == 'batch':
            return {
                'type'     : 'ir.actions.act_window',
                'name'     : _('EDI Batch'),
                'res_model': 'edi.batch',
                'view_mode': 'list,form',
                'target'   : 'current',
                'context'  : {'search_default_group_sifen_state': 1},
                'domain'   : [],
            }
        elif self.edi_type == 'event':
            return {
                'type'     : 'ir.actions.act_window',
                'name'     : _('EDI Event'),
                'res_model': 'edi.event',
                'view_mode': 'list,form',
                'target'   : 'current',
                'context'  : {'search_default_group_state': 1},
                'domain'   : [],
            }
        return {}
