
{
'name': 'SLI Documentos y asignaciones (Viajes, contra recibos y facturas)',
'version': '1.0',
'description': 'Administrador de documentos y vigencias, y asignación de viajes, contra recibos y facturas.',
'author': 'SOLUCIONES LOGISTICAS INTELIGENTES SA DE CV',
'depends': ['base', 'hr', 'sli_trafitec'],
'data': [
    'views/sli_documentos.xml',
    'views/sli_seguimiento.xml',
    'views/cron.xml',
    'security/seguridad.xml',
    'security/ir.model.access.csv'
],
'demo': [],
'installable': True,
'auto_install': False,
}             