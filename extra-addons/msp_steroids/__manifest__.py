{
    'name'        : 'MSP Steroids',
    'summary'     : 'MSP Steroids',
    'description' : "Features not needed but nice to have",
    'version'     : '0.1',
    'author'      : "Gadol Consulting",
    'website'     : 'http://www.gadolconsulting.com',
    'depends'     : [
        'base',
        'account',
    ],
    'category'    : 'Customizations',
    'sequence'    : 10,
    'demo'        : [

    ],
    'data'        : [
        # 'security/ir_model_access.xml',

        'views/ir_default.xml',

        # 'wizard/generic_message_box.xml',

        # 'entries/module_actions_act_window.xml',
        # 'entries/module_menu.xml',
    ],
    'installable' : True,
    'application' : False,
    'auto_install': False,
    'assets'      : {},
    'license'     : 'LGPL-3',
}
