{
    'name'        : 'MSP Base',
    'version'     : '0.1.1',
    'summary'     : 'Customizations to Base',
    'description' : "Custom Configurations for MSP Applications",
    'author'      : "Gadol Consulting",
    'website'     : 'http://www.gadolconsulting.com',
    'depends'     : [
        'base',
        'l10n_py_base',
        'mail'
    ],
    'category'    : 'Customizations',
    'sequence'    : 10,
    'demo'        : [

    ],
    'data'        : [
        'security/ir_model_access.xml',

        'views/res_config_custom.xml',
        'views/ir_sequence.xml',

        'wizard/generic_message_box.xml',

        'entries/module_actions_act_window.xml',
        'entries/module_menu.xml',
    ],
    'installable' : True,
    'application' : False,
    'auto_install': False,
    'assets'      : {},
    'license'     : 'LGPL-3',
}
