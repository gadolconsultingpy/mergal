# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
    'name'        : "MSP Printing Format",
    'summary'     : """MSP Printing Format""",
    'description' : """MSP Printing Format""",
    'license'     : 'LGPL-3',
    'author'      : "Gadol Consulting",
    'website'     : "www.gadolconsulting.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category'    : 'customizations',
    'version'     : '0.1',
    'sequence'    : 150,

    # any module necessary for this one to work correctly
    'depends'     : [
        'base',
        'msp_base',
    ],
    'assets'      : {
    },
    # always loaded
    'data'        : [
        # 'data/paper_format.xml',

        'security/ir_model_access.xml',
        'security/ir_rule.xml',

        'views/res_printing_format.xml',
        'views/ir_actions_report.xml',
        'views/res_signature.xml',


        # 'wizard/general_journal_report_wizard.xml',

        # 'reports/account_payment_customer_report.xml',
        # 'reports/account_payment_supplier_report.xml',

        'entries/module_actions_act_window.xml',
        # 'entries/module_actions_report.xml',
        'entries/module_menu.xml',
    ],
    # only loaded in demonstration mode
    'demo'        : [
    ],
    'installable' : True,
    'application' : False,
    'auto_install': False,
}
