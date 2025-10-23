# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
    'name'        : "MSP Account",
    'summary'     : """MSP Account""",
    'description' : """MSP Account""",
    'license'     : 'LGPL-3',
    'author'      : "Gadol Consulting",
    'website'     : 'https://www.gadolconsulting.com/',
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category'    : 'customizations',
    'version'     : '0.1',
    'sequence'    : 20,
    # any module necessary for this one to work correctly
    'depends'     : [
        'account',
        'hr',
        'msp_printing_format',
    ],
    'assets'      : {
    },
    # always loaded
    'data'        : [
        'data/paper_format.xml',

        'views/account_move.xml',
        'views/account_payment.xml',

        'report/account_payment_report.xml',

        'entries/module_actions_report.xml',
    ],
    # only loaded in demonstration mode
    'demo'        : [
    ],
    'installable' : True,
    'application' : False,
    'auto_install': False,
}
