import datetime

from odoo import models, fields, api, _, tools


class TrafitecReportesParametros(models.AbstractModel):
	_name = 'trafitec.reportes.parametros'
	_description = 'trafitec reportes parametros'

	fecha_inicial = fields.Date(
		string='Fecha incial',
		default=datetime.datetime.today()
	)
	fecha_final = fields.Date(
		string='Fecha final',
		default=datetime.datetime.today()
	)
	tipo=fields.Selection(
		string='Tipo', 
		selection=
		[
			('top_ten_clients', 'Top 10 de clientes'), 
			('top_ten_supplier', 'Top 10 de asociados'),
			('sales_by_saleman','Venta por vendedor'),
			('sales_by_period','Venta por periodo')
		],
		default=1,
		required=True
	)
	
	def FechaATexto(self, fecha):
		f = datetime.datetime.strptime(fecha, '%Y-%m-%d')
		return f.strftime('%d-%m-%Y')
	
	def run_sql(self, qry):
		self._cr.execute(qry)
		_res = self._cr.dictfetchall()
		return _res

	def reporte_clientes_top10(self):
		condicion = ''
		condicion +=" and cast(v.create_date as date)>=''+self.FechaATexto(self.fecha_inicial)+''" \
		            " and cast(v.create_date as date)<=''+self.FechaATexto(self.fecha_final)+'' "
		
		sql=""" 
			select
			p.display_name cliente,
			sum(v.flete_cliente) total,
			sum(v.flete_cliente-v.flete_asociado) diferencia,
			count(v.id) cantidad
			from trafitec_viajes as v
			  inner join res_partner as p on(v.cliente_id=p.id)
			where v.state='Nueva'
			"""+condicion+"""
			group by p.display_name
			order by sum(v.flete_cliente) desc
			limit 10
			"""
		return self.run_sql(sql)

	def reporte_asociados_top10(self):
			condicion = ''
			condicion += " and cast(v.create_date as date)>=''" + self.FechaATexto(
				self.fecha_inicial) + '' and cast(v.create_date as date)<='' + self.FechaATexto(self.fecha_final) + ''
			
			sql = """
				select
				p.display_name asociado,
				sum(v.flete_asociado) total,
				sum(v.flete_cliente-v.flete_asociado) diferencia,
				sum(v.peso_origen_total/1000) tons,
				count(v.id) cantidad
				from trafitec_viajes as v
					inner join res_partner as p on(v.asociado_id=p.id)
				where v.state='Nueva'
				""" + condicion + """
				group by p.display_name
				order by sum(v.flete_asociado) desc
				limit 10
				"""
		return self.run_sql(sql)
	
	def reporte_venta_vendedor(self):
		condicion = ''
		condicion += ' and cast(v.create_date as date)>='' + self.FechaATexto(
			self.fecha_inicial) + '' and cast(v.create_date as date)<='' + self.FechaATexto(self.fecha_final) + '' '
		
		sql = '''
	select
	uv.login vendedor,
	sum(v.flete_cliente) total,
	sum(v.flete_cliente-v.flete_asociado) diferencia,
	sum(v.peso_origen_total/1000) tons,
	count(v.id) cantidad
	from trafitec_viajes as v
		inner join res_partner as p on(v.asociado_id=p.id)
			inner join trafitec_cotizaciones_linea_origen as od on(v.subpedido_id=od.id)
				inner join trafitec_cotizaciones_linea as l on(od.linea_id=l.id)
					inner join trafitec_cotizacion as ct on(l.cotizacion_id=ct.id)
						inner join res_users as uv on(ct.create_uid=uv.id)
	where v.state='Nueva'
	''' + condicion + '''
	group by uv.login
	order by sum(v.flete_cliente) desc
	'''
		return self.run_sql(sql)
	
	def reporte_venta_periodo(self):
		condicion = ''
		condicion += ' and cast(v.create_date as date)>='' + self.FechaATexto(
			self.fecha_inicial) + '' and cast(v.create_date as date)<='' + self.FechaATexto(self.fecha_final) + '' '
		
		sql = '''
select
extract(year from v.create_date) ano,
extract(month from v.create_date) mes_n,
max(case extract(month from v.create_date)
when 1 then 'ENERO'
when 2 then 'FEBRERO'
when 3 then 'MARZO'
when 4 then 'ABRIL'
when 5 then 'MAYO'
when 6 then 'JUNIO'
when 7 then 'JULIO'
when 8 then 'AGOSTO'
when 9 then 'SEPTIEMBRE'
when 10 then 'OCTUBRE'
when 11 then 'NOVIEMBRE'
when 12 then 'DICIEMBRE'
else ''
end) mes_txt,
sum(v.flete_cliente) total,
sum(v.flete_cliente-v.flete_asociado) diferencia,
sum(v.peso_origen_total/1000) tons,
count(v.id) cantidad
from trafitec_viajes as v
where v.state='Nueva'
''' + condicion + '''
group by extract(year from v.create_date),extract(month from v.create_date)
order by extract(year from v.create_date),extract(month from v.create_date) asc
	'''
		return self.run_sql(sql)
	
	
	def reporte(self):
		report_obj = self.env['trafitec.reportes.parametros'].search([]).ids
		context = self.env.context
		
		datas = {
			'ids': [0],
			'model': 'trafitec.reportes.parametros',
			'form': report_obj,
			'rows': {'msg':'Que onda!!'},
			'msg': 'Prumer',
			'context' : {'valores':[]}
		}
		
		datos=[]
		info=''
		
		info='Periodo: '+self.fecha_inicial+', '+self.fecha_final
		if self.tipo == 'top_ten_clients':
			datos = self.reporte_clientes_top10()
			return {
			'type': 'ir.actions.report.xml',
			'report_name': 'SLI_TrafitecReportesX.reporte_top10_clientes',
			'datas': datas,
			'msg': 'Ajua nene!!',
			'context': {'info': info,'valores': datos }
			}
		elif self.tipo == 'top_ten_supplier':
			datos = self.reporte_asociados_top10()
			return {
				'type': 'ir.actions.report.xml',
				'report_name': 'SLI_TrafitecReportesX.reporte_top10_asociados',
				'datas': datas,
				'context': {'info': info,'valores': datos }
			}
		elif self.tipo == 'sales_by_saleman':
			datos = self.reporte_venta_vendedor()
			return {
				'type': 'ir.actions.report.xml',
				'report_name': 'SLI_TrafitecReportesX.reporte_venta_vendedor',
				'datas': datas,
				'context': {'info': info,'valores': datos }
			}
		elif self.tipo == 'sales_by_period':
			datos = self.reporte_venta_periodo()
			return {
				'type': 'ir.actions.report.xml',
				'report_name': 'SLI_TrafitecReportesX.reporte_venta_periodo',
				'datas': datas,
				'context': {'info': info,'valores': datos }
			}
