# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
    'name'        : "MSP Tools",
    'summary'     : """MSP Tools""",
    'description' : """
        XML Export Format
        Python Interpreter
    """,
    'license'     : 'LGPL-3',
    'author'      : "Martin Salcedo Pacheco",
    'website'     : 'http://www.gadolconsulting.com',
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category'    : 'customizations',
    'version'     : '0.1.1',
    'sequence'    : 100,

    # any module necessary for this one to work correctly
    'depends'     : ['base'],
    'assets'      : {
    },
    # always loaded
    'data'        : [
        'data/ir_cron.xml',
        'entries/module_actions_act_prepare.xml',
        'entries/module_actions_act_window.xml',
        'entries/module_menu.xml',
        'security/ir_model_access.xml',
        'views/model_export_xml.xml',
        'views/python_interpreter.xml',
    ],
    # only loaded in demonstration mode
    'demo'        : [
    ],
    'installable' : True,
    'application' : False,
    'auto_install': False,
}
