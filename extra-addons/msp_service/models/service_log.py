from odoo import api, models, fields, _
import logging
import json
from collections import OrderedDict
import re
import html

_logger = logging.getLogger(__name__)


class ServiceLog(models.Model):
    _name = 'service.log'
    _description = 'Service Log'
    _order = 'datetime desc'

    datetime = fields.Datetime('Log Datetime')
    method = fields.Char("Method")
    path = fields.Char("Path")
    type = fields.Selection(
            [
                ('none', 'None'),
                ('inbound', 'Inbound'),
                ('outbound', 'Outbound'),
            ], default='none', string="Type"
    )
    headers = fields.Text("Headers")
    request = fields.Text("Request")
    response = fields.Text("Response")
    status_code = fields.Char("Status Code")
    reason = fields.Char("Reason")
    short_response = fields.Char("Short Response", compute="_compute_short_response")
    res_name = fields.Char("Resource Name")
    res_model = fields.Char("Resource Model")
    res_id = fields.Integer("Resource Id")
    tag = fields.Char("Log Tag", default="generic")
    response_ids = fields.One2many('service.log.response', 'parent_id', string="Response Keys")

    def process_response(self):
        response = self.get_response_dict()
        vals = [(5, 0, 0)]
        for key in response:
            vals.append((0, 0, {'key': key, 'value': html.unescape(response.get(key))}))
        self.response_ids = vals

    @api.depends('response')
    def _compute_short_response(self):
        for rec in self:
            rec.short_response = (rec.response or '')[:100].replace("\n", "")
            if len(rec.response or '') > 100:
                rec.short_response += " ..."

    def get_updatable_fields(self):
        return ['method', 'path', 'request', 'response', 'headers', 'tag', 'type','status_code','reason']

    @api.model
    def register(self, **kwargs):
        vals = {}
        vals['datetime'] = fields.Datetime.now()
        keys = self.get_updatable_fields()
        for fk in keys:
            vals[fk] = kwargs.get(fk, "")
        record = kwargs.get('record', None)
        if record:
            if hasattr(record, "_name"):
                vals['res_model'] = record._name
            if hasattr(record, "id"):
                vals['res_id'] = record.id
            if hasattr(record, "name"):
                vals['res_name'] = record.name
            elif hasattr(record, "display_name"):
                vals['res_name'] = record.display_name
            else:
                vals['res_name'] = "%s,%s" % (record._name, record.id)
        log = self.env[self._name].create(vals)

        try:
            if log:
                name = "service_log_%s_%s_%s" % (log.id, log.res_name or 'unknown', log.res_id or '0')
                request_file = open("/tmp/%s_request.xml" % (name), "w")
                request_file.write(str(kwargs.get('request')))
                request_file.close()

                response_file = open('/tmp/%s_response.html' % (name), "w")
                response_file.write(str(kwargs.get('response')))
                response_file.close()
            else:
                _logger.info("No Log created")
        except BaseException as errstr:
            _logger.warning(errstr)
        return log

    def get_response_dict(self):
        reg_exp = r'<ns2:(?P<node_key>.*)>(.*?)</ns2:\1>'
        exp_matched = re.findall(reg_exp, self.response)

        exp_res = {}

        for clave, valor in exp_matched:
            valor = html.unescape(valor)
            if clave not in exp_res:
                exp_res[clave] = valor
            else:
                if isinstance(exp_res[clave], list):
                    exp_res[clave].append(valor)
                else:
                    exp_res[clave] = [exp_res[clave], valor]
        print("Claves Encontradas: %s" % (exp_res.keys()))
        for kk in exp_res:
            print("Clave: %s\tValor: %s" % (kk, exp_res.get(kk)))
        return exp_res


class ServiceLogResponse(models.Model):
    _name = 'service.log.response'
    _description = 'Service Log Response'

    parent_id = fields.Many2one('service.log')
    key = fields.Char("Key")
    value = fields.Char("Value")
