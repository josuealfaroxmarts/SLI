
{
'name': 'SLI_TrafitecReportesX',
'version': '3.7',
'description': 'Formatos para Trafitec (Cotizaciones,Viajes,Contra recibos, Comisiones, Descuentos)',
'author': 'SOLUCIONES LOGISTICAS INTELIGENTES SA DE CV',
'website': 'http://www.sli.mx',
'category' : 'Utilerias',
'summary' : '',
'depends': ['base', 'sli_trafitec'],
'data': [

         #'reports/estilo.xml',
         'reports/reporte0.xml',
         'reports/reporte_viaje_general.xml',
         'reports/reporte_viaje_granel.xml',
         'reports/reporte_viaje_granel_cliente_original.xml',
         'reports/reporte_viaje_flete.xml',
         'reports/reporte_viaje_contenedor.xml',
         'reports/reporte_viaje_cartaporte.xml',
         'reports/reporte_viaje_cartaporte_otro.xml',
         'reports/reporte_viaje_cartainstruccion.xml',

         'reports/reporte_cotizacion_general.xml',
         'reports/reporte_contrarecibo_general.xml',

         'reports/reporte_comisiones.xml',
         'reports/reporte_descuentos.xml',
         'reports/reporte_cancelacion_cuentas.xml',
         'reports/reporte_factura_general.xml',
         'reports/reporte_factura_agroteck_servicio.xml',
         'reports/reporte_factura_agroteck_maiz.xml',
         'reports/reporte_pagos_masivos.xml',
    
         'views/trafitec_parametros.xml',
         'reports/reporte_top10_clientes.xml',
         'reports/reporte_top10_asociados.xml',
         'reports/reporte_venta_vendedor.xml',
         'reports/reporte_venta_periodo.xml',
         'views/trafitec_reportes_generales.xml'
         ],
'demo': [],
'installable': True,
'auto_install': False,
}
