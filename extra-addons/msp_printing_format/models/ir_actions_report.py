import jinja2

from odoo import api, models, fields, _


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    printing_format_id = fields.Many2one('res.printing.format', string="Printing Format")
    printing_format_ids = fields.One2many('ir.actions.report.printing_format', 'parent_id', string="Printing Formats")

    def get_printing_format(self, **kwargs):
        record = kwargs.get('record', None)
        if record:
            if hasattr(record, 'printing_format_id') and record.printing_format_id:
                return record.printing_format_id
            company_id = record.company_id.id
        else:
            company_id = self.env.company.id
        print("IR_ACTIONS", self.name, self.id)
        printing_format = self.printing_format_id
        for line in self.printing_format_ids:
            if line.company_id.id == company_id:
                printing_format = line.printing_format_id
                break
        print("PRINTING FORMAT", printing_format.name)
        return printing_format

    def get_printing_format_header(self, **kwargs):
        env = jinja2.Environment()
        printing_format = self.get_printing_format(**kwargs)
        if not printing_format:
            return ''
        return env.from_string(printing_format.header).render(kwargs)

    def get_printing_format_footer(self, **kwargs):
        env = jinja2.Environment()
        printing_format = self.get_printing_format(**kwargs)
        if not printing_format:
            return ''
        return env.from_string(printing_format.footer).render(kwargs)


class IrActionsReportPrintingFormat(models.Model):
    _name = 'ir.actions.report.printing_format'
    _description = 'Printing Format'

    parent_id = fields.Many2one('ir.actions.report', string="Parent")
    company_id = fields.Many2one('res.company', string="Company")
    printing_format_id = fields.Many2one('res.printing.format', string="Printing Format")
    name = fields.Char(string="Name", related="printing_format_id.name")
