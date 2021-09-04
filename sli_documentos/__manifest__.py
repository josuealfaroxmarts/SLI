
{
	'name': 'SLI Documentos y asignaciones (Viajes, contra recibos y facturas)',
	'version': '14.0.1.0.0',
	'description': 'Administrador de documentos y vigencias, '
	               'y asignación de viajes, contra recibos y facturas.',
	'author': 'SOLUCIONES LOGISTICAS INTELIGENTES SA DE CV',
	'depends': ['hr', 'sli_trafitec'],
	'data': [
		'views/ir_cron.xml',
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/sli_documentos_documentos_views.xml',
		'views/sli_seguimiento_views.xml',
	],

}
