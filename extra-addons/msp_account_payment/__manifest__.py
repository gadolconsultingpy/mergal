{
    "name"        : "MSP Account Payment",
    "version"     : "0.1",
    "summary"     : "MSP Account Payment",
    "description" : "Account Payment Features",
    "author"      : "Gadol Consulting",
    "website"     : "https://www.gadolconsulting.com/",
    "depends"     : [
        "account",
    ],
    "category"    : 'Customizations',
    "sequence"    : 10,
    "demo"        : [

    ],
    "data"        : [
        # 'data/paper_format.xml',

        # 'security/ir_model_access.xml',
        # 'security/ir_rule.xml',

        'views/account_payment.xml',
        # 'views/res_config_custom.xml',

        # 'wizard/general_journal_report_wizard.xml',

        # 'reports/account_payment_customer_report.xml',
        # 'reports/account_payment_supplier_report.xml',

        # 'entries/module_actions_act_window.xml',
        # 'entries/module_actions_report.xml',
        # 'entries/module_menu.xml',

    ],
    "installable" : True,
    "application" : False,
    "auto_install": False,
    "assets"      : {},
    "license"     : 'LGPL-3',
}
