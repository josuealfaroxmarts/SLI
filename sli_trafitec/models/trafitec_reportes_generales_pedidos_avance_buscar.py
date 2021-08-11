# -*- coding: utf-8 -*-

import datetime
from odoo import models, fields, api, _, tools


class TrafitecReportesGeneralesPedidosAvance(models.Model):
	_name = 'trafitec.reportes.generales.pedidos.avance.buscar'
	_description = 'Reportes generales pedidos avance buscar'
	
	name = fields.Char(string='Nombre', required=True, help='Nombre')
	buscar_tipo = fields.Selection([
			('general', 'General'),
			('detalles', 'Detalles')
		],
		string='Tipo de busqueda'
	)
	buscar_cliente = fields.Char(
		string='Cliente',
		default='',
		help='Cliente de cotizacion.'
	)
	buscar_folio = fields.Char(
		string='Folio',
		default='',
		help='Folio de cotizacion.'
	)
	buscar_usuario = fields.Char(
		string='Usuario',
		default='',
		help='Usuario.'
	)
	buscar_origen = fields.Char(string='Origen', default='')
	buscar_destino = fields.Char(string='Destino', default='')
	buscar_fecha_inicial = fields.Date(
		string='Fecha inicial',
		default=datetime.datetime.today(),
		required=True,
		help='Fecha inicial de los viajes.'
	)
	buscar_fecha_final = fields.Date(
		string='Fecha final',
		default=datetime.datetime.today(),
		required=True,
		help='Fecha final de los viajes.')

	porcentaje_general = fields.Float(string='Porcentaje general', default=0)
	porcentaje_detalles = fields.Float(
		string='Porcentaje detalles',
		default=0
	)

	resultados_id = fields.One2many(
		string='Resultado',
		comodel_name='trafitec.reportes.generales.pedidos.avance.resultado',
		inverse_name='buscar_id'
	)
	detalles_id = fields.One2many(
		string='Detalles',
		comodel_name='trafitec.reportes.generales.pedidos.avance.detalles',
		inverse_name='buscar_id'
	)
	detalles_xmes_id = fields.One2many(
		string='Por mes',
		comodel_name='trafitec.reportes.generales.pedidos.avance.xmes',
		inverse_name='buscar_id'
	)
	detalles_xdia_id = fields.One2many(
		string='Por dia',
		comodel_name='trafitec.reportes.generales.pedidos.avance.xdia',
		inverse_name='buscar_id'
	)

	def general(self):
		for rec in self:
			general = []
			condicion = ""
			condicion_viaje = ""
			if rec.buscar_folio:
				condicion += " and ct.name ilike '%{}%' ".format(
					rec.buscar_folio or ''
				)
			if rec.buscar_cliente:
				condicion += " and cli.name ilike '%{}%' ".format(
					rec.buscar_cliente or ''
				)
			if rec.buscar_usuario:
				condicion_viaje += " and usu.login ilike '%{}%' ".format(
					rec.buscar_usuario or ''
				)
			sql = """
select
ct.id as id,
ct.name as folio,
ct.fecha as fecha,
cli.name as cliente,
coalesce((
select sum(v.peso_origen_total/1000)
from trafitec_viajes as v
inner join trafitec_cotizaciones_linea_origen as lo on(v.subpedido_id =lo.id)
inner join trafitec_cotizaciones_linea l on(lo.linea_id =l.id )
inner join res_users as usu on(v.create_uid =usu.id)
where v.state = 'Nueva' and l.cotizacion_id = ct.id and v.create_date >= '{0}' and v.create_date <= '{1}' {3}
),0) 
as actual,
coalesce((
select count(v.peso_origen_total)
from trafitec_viajes as v
inner join trafitec_cotizaciones_linea_origen as lo on(v.subpedido_id =lo.id)
inner join trafitec_cotizaciones_linea l on(lo.linea_id =l.id )
inner join res_users as usu on(v.create_uid =usu.id)
where v.state = 'Nueva' and l.cotizacion_id = ct.id and v.create_date >= '{0}' and v.create_date <= '{1}' {3}
),0) 
as viajes,
coalesce((
select sum(l.cantidad)
from trafitec_cotizaciones_linea_origen as lo 
inner join trafitec_cotizaciones_linea l on(lo.linea_id =l.id )
where l.cotizacion_id = ct.id
),0) 
as total,
0 as porcentaje,
ct.state as estado
from trafitec_cotizacion as ct
inner join res_partner as cli on(ct.cliente=cli.id)
where ct.state in('Disponible','EnEspera') {2}
""".format(
				rec.buscar_fecha_inicial,
				rec.buscar_fecha_final,
				condicion,
				condicion_viaje
			)
		self.env.cr.execute(sql)
		general = self.env.cr.dictfetchall()
		return general

	def detalles(self):
		for rec in self:
			detalles = []
			condicion = ""
			condicion_viaje = ""
			if rec.buscar_folio:
				condicion += " and c.name ilike '%{}%' ".format(
					rec.buscar_folio or ''
				)
			if rec.buscar_cliente:
				condicion += " and cli.name ilike '%{}%' ".format(
					rec.buscar_cliente or ''
				)
			if rec.buscar_usuario:
				condicion_viaje += " and usu.login ilike '%{}%' ".format(
					rec.buscar_usuario or ''
				)
			sql = """
select
c.name cotizacion_folio,
l.id subpedido,
max(cli.name) cliente,
max(muno.name||', '||esto.name) origen,
max(mund.name||', '||estd.name) destino, 
coalesce(
sum(
(
select
count(v.peso_origen_total)
from trafitec_viajes as v
	inner join trafitec_cotizaciones_linea_origen as vlo on(v.subpedido_id =vlo.id)
	inner join res_users as usu on(v.create_uid =usu.id)
where v.state = 'Nueva' and vlo.linea_id = l.id and v.create_date >= '{0}' and v.create_date <= '{1}' {3}
)
),0) viajes,

coalesce(
sum(
(
select
sum(v.peso_origen_total/1000)
from trafitec_viajes as v
	inner join trafitec_cotizaciones_linea_origen as vlo on(v.subpedido_id =vlo.id)
	inner join res_users as usu on(v.create_uid =usu.id)
where v.state = 'Nueva' and vlo.linea_id = l.id and v.create_date >= '{0}' and v.create_date <= '{1}' {3}
)
),0) actual,
coalesce(sum(l.cantidad),0) total,
0 porcentaje
from trafitec_cotizaciones_linea as l
inner join trafitec_cotizacion c on(l.cotizacion_id =c.id and c.state in('Disponible','EnEspera'))
inner join res_partner as cli on(c.cliente=cli.id)
inner join res_country_township_sat_code as muno on(l.municipio_origen_id=muno.id)
inner join res_country_state_sat_code as esto on(muno.state_sat_code =esto.id)
inner join res_country_township_sat_code as mund on(l.municipio_destino_id=mund.id)
inner join res_country_state_sat_code as estd on(mund.state_sat_code =estd.id)
where c.state in('Disponible','EnEspera') {2}
group by c.name,l.id
order by c.name,l.id		
""".format(
		rec.buscar_fecha_inicial,
		rec.buscar_fecha_final,
		condicion,
		condicion_viaje
	)
		self.env.cr.execute(sql)
		detalles = self.env.cr.dictfetchall()
		return detalles

	def detalles_xmes(self):
		for rec in self:
			detalles = []
			condicion = ""
			if rec.buscar_folio:
				condicion += " and ct.name ilike '%{}%' ".format(
					rec.buscar_folio or ''
				)
			if rec.buscar_cliente:
				condicion += " and cli.name ilike '%{}%' ".format(
					rec.buscar_cliente or ''
				)
			if rec.buscar_usuario:
				condicion += " and usu.login ilike '%{}%' ".format(
					rec.buscar_usuario or ''
				)
			sql = """
select 
--suc.name sucursal,
ct.name cotizacion,
max(cli.name) cliente,
extract(year from v.create_date) ano,
extract(month from v.create_date) mes,
count(*) viajes,
sum(v.peso_origen_total/1000) peso
from trafitec_viajes as v
	--inner join trafitec_sucursal as suc on(v.sucursal_id=suc.id)
	inner join trafitec_cotizaciones_linea_origen as lo on(v.subpedido_id =lo.id)
    inner join trafitec_cotizaciones_linea as l on(lo.linea_id =l.id)
    inner join trafitec_cotizacion  as ct on(l.cotizacion_id =ct.id )
    inner join res_partner as cli on(ct.cliente =cli.id)
	inner join res_users as usu on(v.create_uid =usu.id)
where v.state ='Nueva' and v.create_date>='{0}' and v.create_date<='{1}' {2} 
group by ct.name,extract(year from v.create_date),extract(month from v.create_date)
order by ct.name,extract(year from v.create_date),extract(month from v.create_date)
""".format(rec.buscar_fecha_inicial, rec.buscar_fecha_final, condicion)
		self.env.cr.execute(sql)
		detalles = self.env.cr.dictfetchall()
		return detalles

	def detalles_xdia(self):
		for rec in self:
			detalles = []
			condicion = ""
			if rec.buscar_folio:
				condicion += " and ct.name ilike '%{}%' ".format(
					rec.buscar_folio or ''
				)
			if rec.buscar_cliente:
				condicion += " and cli.name ilike '%{}%' ".format(
					rec.buscar_cliente or ''
				)
			if rec.buscar_usuario:
				condicion += " and usu.login ilike '%{}%' ".format(
					rec.buscar_usuario or ''
				)
			sql = """
select 
--suc.name sucursal,
ct.name cotizacion,
max(cli.name) cliente,
extract(year from v.create_date) ano,
extract(month from v.create_date) mes,
extract(day from v.create_date) dia,
count(*) viajes,
sum(v.peso_origen_total/1000) peso
from trafitec_viajes as v
	--inner join trafitec_sucursal as suc on(v.sucursal_id=suc.id)
	inner join trafitec_cotizaciones_linea_origen as lo on(v.subpedido_id =lo.id)
    inner join trafitec_cotizaciones_linea as l on(lo.linea_id =l.id)
    inner join trafitec_cotizacion  as ct on(l.cotizacion_id =ct.id )
    inner join res_partner as cli on(ct.cliente =cli.id)
	inner join res_users as usu on(v.create_uid =usu.id)
where v.state ='Nueva' and v.create_date>='{0}' and v.create_date<='{1}' {2} 
group by ct.name,extract(year from v.create_date),extract(month from v.create_date),extract(day from v.create_date)
order by ct.name,extract(year from v.create_date),extract(month from v.create_date),extract(day from v.create_date)
""".format(rec.buscar_fecha_inicial, rec.buscar_fecha_final, condicion)
		self.env.cr.execute(sql)
		detalles = self.env.cr.dictfetchall()
		return detalles

	def action_buscar(self):
		for rec in self:
			rec.resultados_id = [(5, _, _)]
			rec.detalles_id = [(5, _, _)]
			rec.detalles_xmes_id = [(5, _, _)]
			rec.detalles_xdia_id = [(5, _, _)] 
			rec.porcentaje_general = 0
			rec.porcentaje_detalles = 0
			lista = []
			detalles = []
			filtro = []
			filtro_viajes = []
			suma_general = 0
			suma_detalles = 0
			conteo_general = 0
			conteo_detalles = 0
			general = []
			general = self.general()
			for c in general:
				actual = 0
				total = 0
				porcentaje = 0
				actual = c.get('actual', 0)
				total = c.get('total', 0)
				if total > 0:
					porcentaje = actual * 100 / total
				suma_general += porcentaje
				conteo_general += 1
				#Genera los datos.
				nuevo = {
					'cotizacion_folio': c.get('folio', ''),
					'cotizacion_cliente': c.get('cliente', ''),
					'cotizacion_numeroviajes': c.get('viajes', 0),
					'cotizacion_peso_actual': actual,
					'cotizacion_peso_total': total,
					'cotizacion_porcentaje': porcentaje
				}
				lista.append(nuevo)
			conjunto = self.detalles()
			for i in conjunto:
				actual = 0
				total = 0
				porcentaje = 0
				actual = i.get('actual', 0)
				total = i.get('total', 0)
				if total > 0:
					porcentaje = actual * 100 / total

				suma_detalles += porcentaje
				conteo_detalles += 1
				nuevo = {
					'cotizacion_folio': i.get('cotizacion_folio', ''),
					'cotizacion_linea': i.get('subpedido', ''),
					'cotizacion_cliente': i.get('cliente', ''),
					'cotizacion_origen': i.get('origen', ''),
					'cotizacion_destino': i.get('destino', ''),
					'cotizacion_numeroviajes': i.get('viajes', 0),
					'cotizacion_peso_actual': actual,
					'cotizacion_peso_total': total,
					'cotizacion_porcentaje': porcentaje
				}
				detalles.append(nuevo)
			rec.detalles_xmes_id = rec.detalles_xmes()
			rec.detalles_xdia_id = rec.detalles_xdia()
			if conteo_general > 0:
				rec.porcentaje_general = suma_general / conteo_general
			if conteo_detalles > 0:
				rec.porcentaje_detalles = suma_detalles / conteo_detalles
			rec.resultados_id = lista
			rec.detalles_id = detalles