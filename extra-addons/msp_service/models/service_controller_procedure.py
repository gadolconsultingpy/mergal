import os
from datetime import datetime

import pytz

from odoo import api, models, fields
import logging

_logger = logging.getLogger(__name__)


class ServiceControllerProcedure(models.Model):
    _name = 'service.controller.procedure'
    _description = 'Service Controller Procedure'

    name = fields.Char("Name")
    route = fields.Char("Route")
    procedure = fields.Text("Procedure")

    def string_to_datetime(self, date_string):
        from datetime import datetime, timezone
        import pytz

        local = pytz.timezone("America/Asuncion")

        # date_str = "2023-12-26 12:30:00"
        datetime_obj = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')

        local_dt = local.localize(datetime_obj, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)

        dd = utc_dt.date()
        tt = utc_dt.time()
        return datetime.combine(dd, tt)

    def service_process(self, **kwargs):
        request = kwargs.get('request')
        path = request.httprequest.path
        local_vars = locals()
        local_vars['request'] = request
        local_vars['response'] = {}
        local_vars['_logger'] = _logger
        local_vars['self'] = self
        exec(self.procedure, globals(), local_vars)
        return local_vars['response']

    def write(self, vals):
        res = super(ServiceControllerProcedure, self).write(vals)
        try:
            self.backup_record()
        except BaseException as errstr:
            pass
        return res

    def backup_record(self):
        path = "/mnt/extra-addons/msp_service/scripts/"
        filename = "%s_%s_.py" % (self._name.replace(".", "_"), self.route.replace("/", "_"))
        filepath = f"{path}{filename}"
        file_obj = open(filepath, "w")
        file_obj.write("# create_date: %s\n" % self.create_date)
        file_obj.write("# write_date: %s\n" % self.write_date)
        file_obj.write("# name: %s\n" % self.name)
        file_obj.write("# route: %s\n" % self.route)
        file_obj.write("\n")
        file_obj.write(self.procedure)
        file_obj.close()
