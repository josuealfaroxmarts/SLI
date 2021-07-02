{
    'name': 'SLI reporte personalizado',
    'version': '1.0',
    'summary': 'Personalizacion de SLI',
    'description': 'Modificacion de factura',
    'category': 'Personalizacion',
    'author': 'Javier Hilario Dominguez, Pablo Osorio Gama',
    'website': 'www.xmarts.com',
    'depends': [
        'account',
                ],
    'data': [
        'reports/report_custom_invoice.xml',
        'reports/report_menu.xml',

    ],
    'installable': True,
    'auto_install': False,
}
