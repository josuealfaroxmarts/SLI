# -*- coding: utf-8 -*-
{
    'name': "sli_trafitec",
    'summary': """
       SLI Trafitec, software de logística integral.
    """,

    'description': """
       Modulo de logística SLI Trafitec.
    """,
    'author':  "XMarts, Luis Alfredo Valencia Díaz",
    'website': "http://www.xmarts.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'SLI',
    'version': '10.0.411',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'fleet',
        'product',
        'l10n_mx_sat_models',
        'argil_invoice_cancel',
        'web'
    ],

    # always loaded
    'data': [
        'views/assets_backend.xml',
        'security/seguridad.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/quotation.xml',
        'views/viajes.xml',
        'views/contrarecibo.xml',
        'views/cargo.xml',

        'views/facturas.xml',
        'views/facturas_automaticas.xml',
        'views/facturas_comision.xml',
        'views/invoice_from_fletex.xml',
        'views/invoice_from_fletex.xml',
 
        'views/templates.xml',
        'views/crm_trafico.xml',
        'views/proyectos.xml',
        'views/routers.xml',
        'views/trafitec.xml',

        'data/email_refuse.xml',
        'data/email_approve.xml',
        'data/invoices_due_automatic.xml',
    ],
    
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'css': ['static/src/css/trafitec.css'],
    'installable': True,
    'auto_install': False,
    'application': True

}

