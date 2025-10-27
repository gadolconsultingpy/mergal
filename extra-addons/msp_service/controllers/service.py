import datetime

from odoo import http
from odoo.http import request, Response
import json
import logging

_logger = logging.getLogger(__name__)


class EDIService(http.Controller):

    @http.route('/test', auth='public')
    def test(self):
        result = {}
        result["test"] = {}
        result["test"]["status"] = "200"
        result["test"]["date"] = str(datetime.datetime.now())
        result["test"]["objects"] = []

        invoices = request.env['account.move'].sudo().search([('move_type', 'in', ['out_invoice', 'out_refund'])])
        for inv in invoices:
            result["test"]["objects"].append(
                    {
                        'number'      : inv.name,
                        'amount_total': inv.amount_total,
                        'partner'     : inv.partner_id.name,
                        'invoice_date': str(inv.invoice_date),
                    }
            )

        return json.dumps(result)

    @http.route('/de/ws/sync/<method>', methods=['POST'], auth='public', type="json")
    def de_ws_sync(self, method):
        ##### Document Electronic Methods #####
        return self._processs_service_controller_procedure(method)

    @http.route('/db/ws/sync/<method>', methods=['POST', 'GET', 'PUT'], auth='public', type="json")
    def db_ws_sync(self, method):
        ##### Database Base Methods #####
        return self._processs_service_controller_procedure(method)

    def _processs_service_controller_procedure(self, method):
        path = http.request.httprequest.path

        log_data = {}
        log_data["method"] = http.request.httprequest.method
        log_data["path"] = http.request.httprequest.path
        log_data["request"] = json.dumps(http.request.get_json_data(), indent=4)
        log_data["type"] = 'inbound'
        log_data["tag"] = path

        response = {}
        controller = http.request.env['service.controller.procedure'].sudo().search([('route', '=', path)])
        if controller:
            log = http.request.env['service.log'].sudo().register(**log_data)
            try:
                _logger.info("----------------------------------------------")
                _logger.info("Controller Found: [%s] %s - %s" % (controller.route,
                                                                 http.request.httprequest.method,
                                                                 controller.name))
                _logger.info("----------------------------------------------")
                _logger.info("Data Received: %s" % (http.request.get_json_data()))
                _logger.info("----------------------------------------------")
                response = controller.service_process(request=http.request)
                log.write({'response': json.dumps(response, indent=4)})
                _logger.info("END Controller %s" % (controller.name))
            except BaseException as errstr:
                _logger.error(errstr)
                response['error'] = {'code'   : '9',
                                     'message': 'Controller Execution Error: %s' % (path)}
                response['error_context'] = errstr
                log.write({'response': errstr})
        else:
            log_data["response"] = "Controller Not Found: [%s]" % (path)
            http.request.env['service.log'].sudo().register(**log_data)

            _logger.info("Controller Not Found: [%s]" % (controller.route))
            _logger.info("Data Received: %s" % (http.request.get_json_data()))
            return http.request.not_found()
        _logger.info("Response: %s" % (response))
        return json.dumps(response, ensure_ascii=True)
