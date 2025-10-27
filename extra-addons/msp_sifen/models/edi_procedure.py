import os
import datetime

from odoo import api, models, fields, _
import traceback
import logging
import sys
import pytz

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EDIProcedure(models.Model):
    _name = 'edi.procedure'
    _description = 'EDI Procedure'
    _order = 'sequence'

    name = fields.Char("Name")
    sequence = fields.Integer("Sequence")
    comment = fields.Text("Comment")
    procedure = fields.Text("Procedure")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)
    tag_ids = fields.Many2many('edi.tag', string="Tags")

    @api.model
    def run_procedure(self, record, procedure):
        proc = self.env[self._name].search([('name', '=', procedure)])
        if proc:
            if proc.procedure:
                # print("Record Type received: %s" % (record._name))
                lcls = locals()
                lcls['record'] = record
                lcls['self'] = proc
                lcls['_logger'] = _logger
                _logger.info("Running: %s" % (proc.name))
                exec(proc.procedure, lcls, globals())
        else:
            msg = _("Procedure Not Found: %s") % (procedure)
            raise UserError(msg)

    def execute(self):
        try:
            _logger.info("Executing: %s" % (self.name))
            lcls = locals()
            lcls['record'] = self
            lcls['self'] = self
            lcls['_logger'] = _logger
            exec(self.procedure, lcls, globals())
        except SyntaxError as err:
            error_class = err.__class__.__name__
            detail = err.args[0]
            msg = "%s at line %d of \n%s: %s" % (error_class, err.lineno, self.procedure, detail)
            _logger.error(msg)
        except BaseException as err:
            error_class = err.__class__.__name__
            detail = err.args[0]
            cl, exc, tb = sys.exc_info()
            line_number = traceback.extract_tb(tb)[-1][1]
            msg = "%s at line %d of \n%s: %s" % (error_class, line_number, self.procedure, detail)
            _logger.error(msg)

    def write(self, vals):
        res = super(EDIProcedure, self).write(vals)
        self.backup_record()
        return res

    def backup_record(self):
        try:
            path = "/mnt/extra-addons/msp_sifen/scripts/"
            filename = "%s_%s_.py" % (self._name.replace(".", "_"), self.name.replace(".", "_"))
            filepath = f"{path}{filename}"
            file_obj = open(filepath, "w")
            file_obj.write("# create_date: %s\n" % self.create_date)
            file_obj.write("# write_date: %s\n" % self.write_date)
            file_obj.write("# name: %s\n" % self.name)
            file_obj.write("# comment: %s\n" % (self.comment or "").replace("\n", "\\n"))
            file_obj.write("\n")
            file_obj.write(self.procedure)
            file_obj.close()
        except BaseException as errstr:
            _logger.error("Error making backup of procedure: %s" % (errstr))

    def get_local_from_utc(self, utc_date, dt_format="%Y-%m-%d %H:%M:%S"):
        # utc_date = "2024-04-30 16:00"
        print(utc_date, dt_format)
        try:
            naive_datetime = datetime.datetime.strptime(utc_date, dt_format)
        except BaseException as errstr:
            naive_datetime = datetime.datetime.strptime(utc_date[:19], dt_format)
        print(utc_date, dt_format)

        utc_aware_datetime = pytz.utc.localize(naive_datetime)

        if not self.env.user.tz:
            raise BaseException("Timezone for User Missing")

        user_tz = pytz.timezone(self.env.user.tz)
        local_datetime = utc_aware_datetime.astimezone(user_tz)
        naive_local_datetime = local_datetime.replace(tzinfo=None)

        return naive_local_datetime
