# encoding: utf-8
# noinspection PyStatementEffect
{
    'name'          : 'Localization for Paraguay - EDI',
    'version'       : '0.1.4',
    'summary'       : 'Localization for Paraguay - EDI',
    'description'   : """Estructura para cualquier empresa que vaya a generar Comprobantes con Facturación Electrónica
Conceptos Implementados
=======================
* Tipos de Comprobante (account.journal)
* Tipo de Transacción (edi.transaction.type)
* Tipo de Crédito (account.payment.term)
* Tipo de Afectación de IVA y Tipo de IVA(account.tax)
* Categoría de Impuesto al Consumo (account.tax.excise.category)
* Motivos de Notas de Crédito (edi.issue.reason)
* Indicador de Presencia (edi.presence)
* 
Ajustes
=======
* Compañía. Tipo de Ambiente
* Unidad de Medida. Códigos Homologados
* Posición Fiscal. Código para Tipo de Régimen
""",
    'author'        : "Martin Salcedo Pacheco",
    'website'       : 'https://www.gadolconsulting.com/',
    'depends'       : ['base',
                       'account',
                       'product',
                       'uom',
                       'fleet',
                       'l10n_py',
                       'l10n_py_base',
                       'msp_base',
                       'msp_printing_format',
                       'l10n_py_latam_base',
                       ],
    'category'      : 'Customizations',
    'sequence'      : 41,
    'demo'          : [

    ],
    'data'          : [
        'data/edi_document_type.xml',
        'data/edi_reversion_document_type.xml',
        'data/edi_issue_reason.xml',
        'data/edi_issue_reason_picking.xml',
        'data/edi_issue_responsible.xml',
        'data/edi_presence.xml',
        'data/edi_transaction_type.xml',
        'data/account_fiscal_position.xml',
        'data/account_tax_application_type.xml',
        'data/account_tax_excise_category.xml',
        'data/account_tax_type.xml',
        'data/uom_uom.xml',
        'data/ir_sequence.xml',
        'data/paper_format.xml',
        'data/l10n_latam_identification_type.xml',
        'data/account_tax.xml',
        'data/account_journal.xml',
        'data/edi_transport.xml',

        'security/ir_model_access.xml',
        'security/ir_module_category.xml',
        'security/res_groups.xml',

        'views/account_fiscal_position.xml',
        'views/account_journal.xml',
        'views/account_move.xml',
        'views/account_move_cancel.xml',
        'views/account_move_invalid.xml',
        'views/account_payment_term.xml',
        'views/account_tax.xml',
        'views/account_tax_application_type.xml',
        'views/account_tax_excise_category.xml',
        'views/account_tax_type.xml',

        'views/edi_certificate.xml',
        'views/edi_document_cancel.xml',
        'views/edi_document_invalid.xml',
        'views/edi_document_nomination.xml',
        'views/edi_document_type.xml',
        'views/edi_issue_reason.xml',
        'views/edi_issue_reason_picking.xml',
        'views/edi_issue_responsible.xml',
        'views/edi_presence.xml',
        'views/edi_reversion_document_type.xml',
        'views/edi_transaction_type.xml',
        'views/edi_transport_mode.xml',
        'views/edi_transport_type.xml',
        'views/fleet_vehicle.xml',
        'views/l10n_latam_identification_type.xml',
        'views/res_company.xml',
        'views/res_config_custom.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner.xml',
        'views/stock_picking.xml',
        'views/stock_picking_type.xml',
        'views/uom_uom.xml',

        'report/account_eticket.xml',
        'report/account_einvoice.xml',

        'wizard/account_move_reversal.xml',
        'wizard/account_move_cancel_wizard.xml',

        'entries/module_actions_act_window.xml',
        'entries/module_actions_report.xml',
        'entries/module_menu.xml',
    ],
    'installable'   : True,
    'application'   : False,
    'auto_install'  : False,
    'assets'        : {},
    'license'       : 'LGPL-3',
    'post_init_hook': '_l10n_py_edi_updates',
}
