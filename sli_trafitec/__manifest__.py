# -*- coding: utf-8 -*-
{
    'name': "Sli Trafitec",
    'summary': """ SLI Trafitec, software de logística integral.""",
    'description': """ Módulo de logística SLI Trafitec.""",
    'author':  "XMarts, Luis Alfredo Valencia Díaz",
    'website': "http://www.xmarts.com",

    'category': 'SLI',
    'version': '14.0.0.0.1',
    'depends': [        
        'account_accountant',
        'fleet',
        'product',
	    'sale_management'
	    'web',
    ],

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
    ],
    'css': ['static/src/css/trafitec.css'],
    'installable': True,
    'auto_install': False,
    'application': True
}

