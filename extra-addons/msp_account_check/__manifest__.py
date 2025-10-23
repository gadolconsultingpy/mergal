{
    "name"          : "MSP Account Check",
    "version"       : "0.1.4",
    "summary"       : "MSP Account Check",
    "description"   : "Account Check",
    "author"        : "Martin Salcedo Pacheco",
    "website"       : "https://www.gadolcomsulting.com",
    "depends"       : [
        "account",
        "msp_account",
        "msp_account_payment",
        "msp_base",
    ],
    "category"      : 'Customizations',
    "sequence"      : 25,
    "data"          : [
        'data/ir_sequence.xml',
        'data/paper_format.xml',
        'data/ir_actions_server.xml',

        'security/ir_model_access.xml',
        'security/ir_rule.xml',

        'views/account_check.xml',
        'views/account_checkbook.xml',
        'views/account_checkbook_template.xml',
        'views/account_journal.xml',
        'views/account_securities_deposit.xml',
        'views/account_move.xml',
        'views/account_payment.xml',
        'views/res_config_custom.xml',

        # 'report/account_payment_supplier_report.xml',
        # 'report/account_payment_customer_report.xml',
        'report/account_checkbook_check_report.xml',
        'report/account_checkbook_continental.xml',
        'report/account_checkbook_continental_stub.xml',

        'wizard/assign_checkbook.xml',
        'wizard/account_checkbook_set_nr.xml',
        'wizard/account_payment_register.xml',

        'entries/module_actions_act_window.xml',
        'entries/module_menu.xml',
        'entries/module_actions_report.xml',

    ],
    "demo"          : [

    ],
    "installable"   : True,
    "application"   : False,
    "auto_install"  : False,
    "post_init_hook": "_post_init_hook",
    'uninstall_hook': '_uninstall_hook',
    "assets"        : {},
    "license"       : 'LGPL-3',
}
