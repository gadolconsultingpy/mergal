# encoding: utf-8
# noinspection PyStatementEffect
{
    'name'        : 'MSP Account + Payment Form',
    'version'     : '0.2.1',
    'summary'     : 'Customizations to Account + Payment Form',
    'description' :
"""Estructuras para complementar información de Facturación Electrónica
Conceptos Implementados 
=======================
* Formas de Pago (account.payment.form)
* Tipos de Formas de Pago (account.payment.form.type)
* Emisores de Tarjeta (card.issuer)
* Forma de Procesamiento de Tarjetas (card.process.form)
""",
    'author'      : "Martin Salcedo Pacheco",
    'website'     : 'https://www.gadolconsulting.com/',
    'depends'     : [
        'account',
        'l10n_py',
        'l10n_py_edi',
        'msp_account',
        'msp_account_payment',
    ],
    'category'    : 'Customizations',
    'sequence'    : 20,
    'demo'        : [

    ],
    'data'        : [
        'data/card_issuer.xml',
        'data/card_process_form.xml',
        'data/account_payment_form_type.xml',
        'data/account_payment_form.xml',

        'security/ir_model_access.xml',

        'views/card_process_form.xml',
        'views/card_issuer.xml',
        'views/account_payment_form_type.xml',
        'views/account_payment_term.xml',
        'views/account_move.xml',
        'views/account_payment.xml',
        'views/account_payment_form.xml',
        'views/res_config_custom.xml',

        'entries/module_actions_act_window.xml',
        'entries/module_menu.xml',

        'wizard/account_payment_register.xml',
    ],
    'installable' : True,
    'application' : False,
    'auto_install': False,
    'assets'      : {},
    'license'     : 'LGPL-3',
}
