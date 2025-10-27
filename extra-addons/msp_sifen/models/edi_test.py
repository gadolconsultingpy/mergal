from odoo import api, models, fields, _


class EDITest(models.Model):
    _name = 'edi.test'
    _description = 'EDI Test'

    name = fields.Char('Name')
    description = fields.Text('Description')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)

    security_code_1 = fields.Char('Security Code 1', default="ABCD0000000000000000000000000000")
    security_code_2 = fields.Char('Security Code 2', default="EFGH0000000000000000000000000000")

    branch_id = fields.Many2one('res.branch', 'Branch')
    establishment = fields.Char('Establishment')
    dispatch_point = fields.Char('Dispatch Point')
    stamped_number = fields.Char('Stamped Number')
    from_date = fields.Date('From Date')

    def action_apply_test(self):
        self.company_id.write({
            'security_code_1'  : self.security_code_1,
            'security_code_2'  : self.security_code_2,
            'sifen_environment': '0',
        })

        self.branch_id.write({'establishment': self.establishment})
        for dp in self.branch_id.dispatch_point_ids:
            dp.write({'dispatch_point': self.dispatch_point})
            if dp.move_type == 'out_invoice':
                new_jname = "Factura de Venta %s-%s" % (self.establishment, self.dispatch_point)
            elif dp.move_type == 'out_refund':
                new_jname = "Nota de Crédito %s-%s" % (self.establishment, self.dispatch_point)
            elif dp.move_type == 'out_receipt':
                new_jname = "Recibo de Venta %s-%s" % (self.establishment, self.dispatch_point)
            dp.journal_id.write({'name': new_jname})
            dp.sequence_id.write({'name'          : new_jname,
                                  'code'          : 'account.move.%s.%s' % (self.establishment, self.dispatch_point),
                                  'stamped_number': self.stamped_number,
                                  'from_date'     : self.from_date,
                                  'prefix'        : '%s-%s-' % (self.establishment, self.dispatch_point),
                                  'establishment' : self.establishment,
                                  'dispatch_point': self.dispatch_point,
                                  })
