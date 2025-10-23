{
    'name'        : 'MSP Service',
    'version'     : '0.1',
    'summary'     : 'EDI Services',
    'description' : """EDI Services""",
    'author'      : "Martin Salcedo Pacheco",
    'website'     : 'https://www.gadolconsulting.com/',
    'depends'     : [
        'base',
        'account',
        'msp_account',
        'l10n_py_edi',
        'l10n_py',
        'hr',
    ],
    'category'    : 'customizations',
    'sequence'    : 51,
    'demo'        : [

    ],
    'data'        : [
        'entries/module_actions_act_window.xml',
        'entries/module_menu.xml',

        # 'data/de_ws_sync_recibe.xml',
        # 'data/db_ws_sync_product.xml',
        # 'data/db_ws_sync_partner.xml',
        # 'data/service.controller.procedure.csv',

        'security/ir_model_access.xml',

        'views/service_controller_procedure.xml',
        'views/service_log.xml',

    ],
    'installable' : True,
    'application' : False,
    'auto_install': False,
    'assets'      : {},
    'license'     : 'LGPL-3',
}
