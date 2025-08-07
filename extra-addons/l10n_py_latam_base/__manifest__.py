{
    'name'        : 'Localization for Paraguay - LATAM Base',
    'version'     : '0.1',
    'summary'     : 'Localization for Paraguay - LATAM Base',
    'description' : "Latam Identification Types",
    'author'      : "Martin Salcedo Pacheco",
    'website'     : 'https://www.gadolconsulting.com/',
    'depends'     : [
        'l10n_latam_base',
        'l10n_py',
    ],
    'category'    : 'Customizations',
    'sequence'    : 11,
    'demo'        : [

    ],
    'data'        : [
        'data/identification_type.xml',

        'entries/module_actions_act_window.xml',

        'views/identification_type.xml',
    ],
    'installable' : True,
    'application' : False,
    'auto_install': False,
    # 'pre_init_hook': 'pre_init_hook',
    # 'post_init_hook': '_assign_default_mail_template_picking_id',
    'assets'      : {},
    'license'     : 'LGPL-3',
}
