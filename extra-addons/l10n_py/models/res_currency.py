from odoo import api, models, fields, _
import logging
import requests
from bs4 import BeautifulSoup
import datetime
import re

_logger = logging.getLogger(__name__)


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    plural_name = fields.Char("Plural Name")
    dnit_currency_date = fields.Boolean("Currency Rate from DNIT")

    def get_normal_currency_rate(self, rate_factor):
        if not rate_factor or rate_factor <= 0:
            return 1.0
        return self.round(1 / rate_factor)

    def _convert(self, from_amount, to_currency, company, date, round=True):
        """Returns the converted amount of ``from_amount``` from the currency
           ``self`` to the currency ``to_currency`` for the given ``date`` and
           company.

           :param company: The company from which we retrieve the convertion rate
           :param date: The nearest date from which we retriev the conversion rate.
           :param round: Round the result or not
        """
        self, to_currency = self or to_currency, to_currency or self
        assert self, "convert amount from unknown currency"
        assert to_currency, "convert amount to unknown currency"
        assert company, "convert amount from unknown company"
        assert date, "convert amount from unknown date"
        # apply conversion rate
        if self == to_currency:
            to_amount = from_amount
        elif from_amount:
            crate = self._get_conversion_rate(self, to_currency, company, date)
            ##### Taking in account the Commercial Currency Rate from Invoices
            if self.env.context.get("commercial_currency_rate", False):
                _logger.debug("Converting Using Commercial Currency Rate: %s" % (
                    self.env.context.get("commercial_currency_rate")))
            crate = self.env.context.get('commercial_currency_rate', crate)
            to_amount = from_amount * crate
        else:
            return 0.0

        # apply rounding
        return to_currency.round(to_amount) if round else to_amount

    @api.model
    def _cron_dnit_currency_rate(self, offset=0):
        try:
            _logger.info("Performing Currency Rate Update from DNIT")
            req = requests.get('https://www.dnit.gov.py/web/portal-institucional/cotizaciones')
            content = req.content.decode()
        except BaseException as errstr:
            _logger.info("Error: %s" % (errstr))
            return False

        soup = BeautifulSoup(content, 'html.parser')

        grand_class = soup.find('div', class_='lfr-layout-structure-item-listados')

        meses = {
            "Enero"     : 1,
            "Febrero"   : 2,
            "Marzo"     : 3,
            "Abril"     : 4,
            "Mayo"      : 5,
            "Junio"     : 6,
            "Julio"     : 7,
            "Agosto"    : 8,
            "Septiembre": 9,
            "Octubre"   : 10,
            "Noviembre" : 11,
            "Diciembre" : 12
        }
        rates = {}
        available_currencies = ['USD', 'BRL', 'ARS', 'JPY', 'EUR', 'GBP']
        #                         0      1      2     3       4      5
        #                         1,2    3,4   5,6   7,8     9,10  11,12
        enabled_currencies = self.env['res.currency'].search(
                [
                    ('name', 'in', available_currencies),
                    ('dnit_currency_date', '=', True)
                ]
        )
        date_rate_from = fields.Date.context_today(self.env.company) + datetime.timedelta(days=offset)
        date_rate_to = fields.Date.context_today(self.env.company)
        _logger.info("Searching from %s to %s" % (date_rate_from, date_rate_to))
        # date_rate = datetime.date(2024, 4, 15)
        for grand_class_item in grand_class:
            if grand_class_item.__class__.__name__ == 'Tag':
                sections = grand_class_item.find_all('section', class_="component-table")
                for section in sections:
                    title = section.find('h4', class_="section__midtitle")
                    # print(title.text)
                    try:
                        pattern = "Tipos de cambios del mes de (?P<month_name>.*) (?P<year>.*)"
                        res = re.match(pattern, title.text)
                        # print(res.groupdict())
                        month_nr = meses.get(res.groupdict().get('month_name', 0))
                        year_nr = int(res.groupdict().get('year', 0))
                        table_list = section.find_all('table', class_="table")
                        if month_nr and year_nr:
                            for table in table_list:
                                tbody = table.find('tbody')
                                tr_list = tbody.find_all('tr')
                                for tr in tr_list:
                                    td_list = tr.find_all('td')
                                    day = int(td_list[0].text)
                                    rate_date = datetime.date(year_nr, month_nr, int(day))
                                    # date_today = fields.Date.context_today(self.env.company)
                                    if rate_date < date_rate_from or rate_date > date_rate_to:
                                        continue
                                    else:
                                        print(rate_date)
                                    for cur in enabled_currencies:
                                        cur_idx = available_currencies.index(cur.name)
                                        cur_purc_idx = (cur_idx * 2) + 1
                                        cur_sale_idx = (cur_idx * 2) + 2
                                        print(cur.name, cur_purc_idx, cur_sale_idx)
                                        cur_purc = float(td_list[cur_purc_idx].text.replace(".", "").replace(",", "."))
                                        cur_sale = float(td_list[cur_sale_idx].text.replace(".", "").replace(",", "."))
                                        # print(day)
                                        print(rate_date, cur_purc, cur_sale)
                                        if cur.name not in rates:
                                            rates[cur.name] = {}
                                        rates[cur.name][rate_date] = (cur_purc, cur_sale)
                    except BaseException as errstr:
                        _logger.info("Error Parsing Data: %s - %s" % (title, errstr))
                        print(errstr)
        print(rates)
        Currency = self.env['res.currency']
        CurrencyRate = self.env['res.currency.rate']
        for name in rates.keys():
            currency_object = Currency.search([('name', '=', name)])
            cur_date = date_rate_from
            while cur_date <= date_rate_to:
                print("buscando fecha: ", cur_date)
                if cur_date in rates[name]:
                    already_existing_rate = CurrencyRate.search(
                            [
                                ('currency_id', '=', currency_object.id),
                                ('name', '=', cur_date),
                                ('company_id', '=', self.env.company.id)
                            ]
                    )
                    rate_value = rates[name][cur_date][0]
                    if already_existing_rate:

                        already_existing_rate.write(
                                {'rate'                : 1 / rate_value or 1,
                                 'fiscal_currency_rate': rate_value}
                        )
                        _logger.info("Currency Rate Updated: %s - %s - %s " % (name, cur_date, rate_value))
                    else:
                        CurrencyRate.create({'currency_id'         : currency_object.id,
                                             'rate'                : 1 / rate_value or 1,
                                             'fiscal_currency_rate': rate_value,
                                             'name'                : cur_date,
                                             'company_id'          : self.env.company.id})
                        _logger.info("Currency Rate Created: %s - %s - %s " % (name, cur_date, rate_value))
                cur_date = cur_date + datetime.timedelta(days=1)