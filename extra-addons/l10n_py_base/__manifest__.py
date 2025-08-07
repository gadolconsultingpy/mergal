{
    'name'        : 'Localization for Paraguay Base',
    'version'     : '0.1',
    'summary'     : 'Customizations to Base',
    'description' : "Implementación de Configuración Extendida para Empresas de Paraguay",
    'author'      : "Martin Salcedo Pacheco",
    'website'     : 'https://www.gadolconsulting.com',
    'depends'     : [
        'base'
    ],
    'category'    : 'Customizations',
    'sequence'    : 10,
    'demo'        : [

    ],
    'data'        : [
        'security/ir_model_access.xml',

        'views/res_config_custom.xml',

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
