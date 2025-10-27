# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
    'name'       : "MSP Sale",
    'summary'    : """MSP Sale""",
    'description': """ MSP Sale""",
    'license'    : 'LGPL-3',
    'author'     : "Gadol Consulting",
    'website'    : "http://www.gadolconsulting.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category'   : 'customizations',
    'version'    : '0.2',
    'sequence'   : 100,
    # any module necessary for this one to work correctly
    'depends'    : ['sale',
                    'l10n_py',
                    ],

    # always loaded
    'data'       : [
        # 'data/ir_sequence.xml',
        # 'data/paper_format.xml',

        # 'security/ir_module_category.xml',
        # 'security/res_groups.xml',
        # 'security/ir_model_access.xml',
        # 'security/ir_rule.xml',

        # 'entries/module_actions_act_window.xml',
        # 'entries/module_actions_report.xml',
        # 'entries/module_menu.xml',

        # 'views/petty_cash_concept.xml',
        # 'views/petty_cash_definition.xml',
        # 'views/account_payment.xml',
        # 'views/petty_cash_sheet.xml',
        # 'views/account_move.xml',
        # 'views/res_config_custom.xml',

        # 'wizard/petty_cash_sheet_create_invoice.xml',
        # 'wizard/petty_cash_create_payment.xml',

        # 'report/petty_cash_sheet_report.xml',

    ],
    # only loaded in demonstration mode
    'demo'       : [
    ],
    'installable': True,
    'application': False,
}
