# -*- coding: utf-8 -*-

{
	'name': 'Reportes Financieros SLI',
	'version': '14.0.1.0.0',
	'summary': 'Reporte financieros',
	'category': 'Account',
	'depends': ['account'],
	'author': 'Soluciones Logísticas Inteligentes SA de CV, '
	          'Developer: Ing. Viridiana Cruz Santos',
	'data': [
		'security/ir.model.access.csv',
		'views/menu_main_views.xml',
		'reports/purchase_report_inherit.xml',
		'views/account_move_views.xml',
		'views/download_attachment_views.xml',
		'views/supplier_invoice_views.xml',
		'views/supplier_payment_term_views.xml',
	],
}