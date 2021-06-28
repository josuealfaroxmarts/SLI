## -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import logging
import xlsxwriter
import base64
import tempfile	

import datetime

_logger = logging.getLogger(__name__)


class TrafitecReportesGenerales(models.TransientModel):
	_name = 'trafitec.reportes.generales'
	_order = 'id desc'
	name = fields.Char(string="Nombre", required=True)
	fecha_inicial = fields.Date(string="Fecha incial")
	fecha_final = fields.Date(string="Fecha final")
	archivo_nombre = fields.Char(string="Nombre del archivo")
	archivo_archivo = fields.Binary(string="Archivo")
	tipo = fields.Selection(string="Tipo", selection=[('cliente_dias_cartera', 'Dias de cartera de cliente'),
														('proveedor_dias_cartera', 'Dias de cartera de proveedor'),
														('cuentasxcobrar','Cuentas por cobrar'),
														('cuentasxpagar','Cuentas por pagar'),
														('cuentasxcobrar_flete', 'Cuentas por cobrar flete'),
														('cuentasxpagar_flete','Cuentas por pagar flete'),
														('operaciones_pedidos_estado','Estado de pedidos')],required=True)

	#--------------------------------------------------------------------------------
	# EVENTOS
	#--------------------------------------------------------------------------------
	
	@api.model
	def create(self, vals):
		tipo = vals['tipo']
		
		
		vals['archivo_nombre'] = str(vals['name']) + '.xlsx'
		if tipo == 'cliente_dias_cartera':
			vals['archivo_archivo'] = self.reporte_clientes_dias_cartera()
		elif tipo == 'proveedor_dias_cartera':
			vals['archivo_archivo'] = self.reporte_proveedores_dias_cartera()
		elif tipo == 'cuentasxcobrar':
			vals['archivo_archivo'] = self.reporte_cuentasxcobrar()
		elif tipo == 'cuentasxpagar':
			vals['archivo_archivo'] = self.reporte_cuentasxpagar()
		elif tipo == 'cuentasxcobrar_flete':
			vals['archivo_archivo'] = self.reporte_cuentasxcobrar_flete()
		elif tipo == 'cuentasxpagar_flete':
			vals['archivo_archivo'] = self.reporte_cuentasxpagar_flete()
		elif tipo == 'operaciones_pedidos_estado':
			vals['archivo_archivo'] = self.reporte_operaciones_pedidos_estado()
		
		obj = super(TrafitecReportesGenerales, self).create(vals)
		return obj
	
	#--------------------------------------------------------------------------------
	# FUNCIONES DE UTILERIA
	#--------------------------------------------------------------------------------
	def cfg_formato_cabecera(self, workbook):
		formato = workbook.add_format({'bold': True, 'font_color': 'white'})
		formato.set_bg_color('black')
		formato.set_align('center')
		return formato

	def cfg_formato_moneda(self, workbook):
		formato= workbook.add_format()
		formato.set_align('right')
		formato.set_num_format('#,##0.00')
		return formato

	def cfg_formato_tons(self, workbook):
		formato= workbook.add_format()
		formato.set_align('right')
		formato.set_num_format('#,##0.000')
		return formato

	def cfg_formato_por(self, workbook):
		formato= workbook.add_format()
		formato.set_align('right')
		formato.set_num_format('#,##0.00')
		return formato

	def cfg_formato_moneda_bold(self, workbook):
		formato = workbook.add_format({'bold': True})
		formato.set_align('right')
		formato.set_num_format('#,##0.00')
		return formato

	def cfg_formato_titulo(self, workbook):
		formato= workbook.add_format({'bold': True, 'font_color': 'black'})
		formato.set_bg_color('silver')
		formato.set_align('center')
		return formato

	def cfg_formato_fecha(self, workbook):
		formato = workbook.add_format({'num_format': 'dd/mm/yyyy'})
		return formato

	def cfg_formato_fondo(self, workbook, color):
		formato = workbook.add_format()
		formato.set_bg_color(color)
		return formato


	#--------------------------------------------------------------------------------
	# REPORTES
	#--------------------------------------------------------------------------------
	
	def ruta_tmp(self):
		return tempfile.gettempdir() + '/temp.tmp'
	
	def empresa_id(self):
		return self.env.user.company_id.id
	
	def reporte_clientes_dias_cartera(self):
		file_name = self.ruta_tmp()
		print("ARCHIVO TEMPORAL")
		print(file_name)
		
		workbook = xlsxwriter.Workbook(file_name, {'in_memory': True})
		worksheet = workbook.add_worksheet("Días de cartera de clientes")
		fc = self.cfg_formato_cabecera(workbook)
		fm = self.cfg_formato_moneda(workbook)
		ft = self.cfg_formato_titulo(workbook)
		ff = self.cfg_formato_fecha(workbook)
		
		#Ancho de columnas.
		worksheet.set_column(1, 1, 50)
		worksheet.set_column(2, 2, 20)
		worksheet.set_column(3, 3, 20)
		worksheet.set_column(4, 4, 20)
		worksheet.set_column(5, 5, 20)
		worksheet.set_column(6, 6, 20)
		worksheet.set_column(7, 7, 20)
		
		rowi = 2
		coli = 1
		row = 0
		
		sql = """
		select
--f.id id,
--coalesce(f.number,'') as folio,
p.name persona,
max(p.id) persona_id,
--f.date_invoice fecha,
--f.date_due fecha_vencimiento,
--current_date-f.date_due dias,
sum(f.amount_total) total,
sum(f.residual) saldo,
	sum(case when (current_date-f.date_due)>1 and (current_date-f.date_due)<=15 then f.residual else 0 end) v_d1a15,
	sum(case when (current_date-f.date_due)>=16 and (current_date-f.date_due)<=30 then f.residual else 0 end) v_d16a30,
	sum(case when (current_date-f.date_due)>=31 and (current_date-f.date_due)<=45 then f.residual else 0 end) v_d31a45,
	sum(case when (current_date-f.date_due)>=46 then f.residual else 0 end) v_d46aN

from account_invoice as f
	inner join res_partner p on(f.partner_id=p.id)
	left join trafitec_contrarecibo as cr on(cr.invoice_id=f.id)
where
f.residual>1 and f.state='open' and f.type='out_invoice'
and f.company_id={}
group by p.name
""".format(self.empresa_id())
		self.env.cr.execute(sql)
		facturas = self.env.cr.dictfetchall()
		
		#General.
		worksheet.write_datetime('B1', datetime.datetime.now(), ff)
		worksheet.merge_range('B2:H2', 'SOLUCIONES LOGISTICAS INTELIGENTES SA DE CV', ft)
		
		
		#Cabecera.
		worksheet.write(rowi+row, coli+0, "CLIENTE", fc)
		worksheet.write(rowi+row, coli+1, "TOTAL", fc)
		worksheet.write(rowi+row, coli+2, "SALDO", fc)
		worksheet.write(rowi+row, coli+3, "D 1-15", fc)
		worksheet.write(rowi+row, coli+4, "D 16-30", fc)
		worksheet.write(rowi+row, coli+5, "D 31-45", fc)
		worksheet.write(rowi+row, coli+6, "D 45-N", fc)
		
		#Datos.
		for f in facturas:
			row += 1
			worksheet.write(rowi+row, coli+0, f['persona'])
			worksheet.write_number(rowi+row, coli+1, f['total'],fm)
			worksheet.write_number(rowi+row, coli+2, f['saldo'],fm)
			worksheet.write_number(rowi+row, coli+3, f['v_d1a15'],fm)
			worksheet.write_number(rowi+row, coli+4, f['v_d16a30'],fm)
			worksheet.write_number(rowi+row, coli+5, f['v_d31a45'],fm)
			worksheet.write_number(rowi+row, coli+6, f['v_d46an'],fm)
		
		workbook.close()
		with open(file_name, "rb") as file:
			file_base64 = base64.b64encode(file.read())
			
		# self.archivo_nombre = str(self.name) + '.xlsx'
		# self.write({'archivo_archivo': file_base64, })
		return file_base64
	
	def reporte_proveedores_dias_cartera(self):
		file_name = self.ruta_tmp()
		
		workbook = xlsxwriter.Workbook(file_name, {'in_memory': True})
		worksheet = workbook.add_worksheet("Días de cartera de asociados")
		fc = self.cfg_formato_cabecera(workbook)
		fm = self.cfg_formato_moneda(workbook)
		ft = self.cfg_formato_titulo(workbook)
		ff = self.cfg_formato_fecha(workbook)
		
		#Ancho de columnas.
		worksheet.set_column(1, 1, 50)
		worksheet.set_column(2, 2, 20)
		worksheet.set_column(3, 3, 20)
		worksheet.set_column(4, 4, 20)
		worksheet.set_column(5, 5, 20)
		worksheet.set_column(6, 6, 20)
		worksheet.set_column(7, 7, 20)
		
		rowi = 2
		coli = 1
		row = 0


		
		sql = """
		select
--f.id id,
--coalesce(f.number,'') as folio,
p.name persona,
max(p.id) persona_id,
--f.date_invoice fecha,
--f.date_due fecha_vencimiento,
--current_date-f.date_due dias,
sum(f.amount_total) total,
sum(f.residual) saldo,
	sum(case when (current_date-f.date_due)>1 and (current_date-f.date_due)<=15 then f.residual else 0 end) v_d1a15,
	sum(case when (current_date-f.date_due)>=16 and (current_date-f.date_due)<=30 then f.residual else 0 end) v_d16a30,
	sum(case when (current_date-f.date_due)>=31 and (current_date-f.date_due)<=45 then f.residual else 0 end) v_d31a45,
	sum(case when (current_date-f.date_due)>=46 then f.residual else 0 end) v_d46an

from account_invoice as f
	inner join res_partner p on(f.partner_id=p.id)
	left join trafitec_contrarecibo as cr on(cr.invoice_id=f.id)
where
f.residual>1 and f.state='open' and f.type='in_invoice'
and f.company_id={}
group by p.name
""".format(self.empresa_id())
		self.env.cr.execute(sql)
		facturas = self.env.cr.dictfetchall()
		
		#General.
		worksheet.write_datetime('B1', datetime.datetime.now(), ff)
		worksheet.merge_range('B2:H2', 'SOLUCIONES LOGISTICAS INTELIGENTES SA DE CV', ft)
		
		#Cabecera.
		worksheet.write(rowi+row, coli+0, "ASOCIADO", fc)
		worksheet.write(rowi+row, coli+1, "TOTAL", fc)
		worksheet.write(rowi+row, coli+2, "SALDO", fc)
		worksheet.write(rowi+row, coli+3, "D 1-15", fc)
		worksheet.write(rowi+row, coli+4, "D 16-30", fc)
		worksheet.write(rowi+row, coli+5, "D 31-45", fc)
		worksheet.write(rowi+row, coli+6, "D 45-N", fc)
		
		#Datos.
		for f in facturas:
			row += 1
			worksheet.write(rowi+row, coli+0, f['persona'])
			worksheet.write_number(rowi+row, coli+1, f['total'],fm)
			worksheet.write_number(rowi+row, coli+2, f['saldo'],fm)
			worksheet.write_number(rowi+row, coli+3, f['v_d1a15'],fm)
			worksheet.write_number(rowi+row, coli+4, f['v_d16a30'],fm)
			worksheet.write_number(rowi+row, coli+5, f['v_d31a45'],fm)
			worksheet.write_number(rowi+row, coli+6, f['v_d46an'],fm)
		
		workbook.close()
		with open(file_name, "rb") as file:
			file_base64 = base64.b64encode(file.read())
		# self.archivo_nombre = str(self.name) + '.xlsx'
		# self.write({'archivo_archivo': file_base64, })
		return file_base64
	
	def reporte_cuentasxcobrar(self):
		file_name = self.ruta_tmp()
		total_total = 0
		total_saldo = 0
		
		workbook = xlsxwriter.Workbook(file_name, {'in_memory': True})
		worksheet = workbook.add_worksheet("Cuentas por cobrar")
		fc = self.cfg_formato_cabecera(workbook)
		fm = self.cfg_formato_moneda(workbook)
		fm_b = self.cfg_formato_moneda_bold(workbook)
		ft = self.cfg_formato_titulo(workbook)
		ff = self.cfg_formato_fecha(workbook)
		
		# Ancho de columnas.
		worksheet.set_column(1, 1, 50)
		worksheet.set_column(2, 2, 20)
		worksheet.set_column(3, 3, 20)
		worksheet.set_column(4, 4, 20)
		worksheet.set_column(5, 5, 20)
		worksheet.set_column(6, 6, 60)
	
		
		rowi = 2
		coli = 1
		row = 0
		
		sql = """
select
f.id id,
f.number folio,
f.date_invoice fecha,
p.display_name persona,
f.amount_total total,
f.residual saldo,
f.contiene contiene
from account_invoice as f
	inner join res_partner as p on(f.partner_id=p.id)
where
f.state='open'
and f.type='out_invoice'
and f.company_id={}
order by f.residual desc
""".format(self.empresa_id())
		self.env.cr.execute(sql)
		facturas = self.env.cr.dictfetchall()
		
		# General.
		worksheet.write_datetime('B1', datetime.datetime.now(), ff)
		worksheet.merge_range('B2:H2', 'SOLUCIONES LOGISTICAS INTELIGENTES SA DE CV', ft)
		
		# Cabecera.
		worksheet.write(rowi + row, coli + 0, "CLIENTE", fc)
		worksheet.write(rowi + row, coli + 1, "FOLIO", fc)
		worksheet.write(rowi + row, coli + 2, "FECHA", fc)
		worksheet.write(rowi + row, coli + 3, "TOTAL", fc)
		worksheet.write(rowi + row, coli + 4, "SALDO", fc)
		worksheet.write(rowi + row, coli + 5, "CONTIENE", fc)
		
		# Datos.
		for f in facturas:
			row += 1
			worksheet.write(rowi + row, coli + 0, f['persona'])
			worksheet.write(rowi + row, coli + 1, f['folio'])
			worksheet.write(rowi + row, coli + 2, f['fecha'])
			worksheet.write_number(rowi + row, coli + 3, f['total'], fm)
			worksheet.write_number(rowi + row, coli + 4, f['saldo'], fm)
			worksheet.write(rowi + row, coli + 5, f['contiene'])
			
			total_total += f['total']
			total_saldo += f['saldo']
		row += 1
		worksheet.write(rowi + row, coli + 3, total_total,fm_b)
		worksheet.write(rowi + row, coli + 4, total_saldo,fm_b)
		
		workbook.close()
		with open(file_name, "rb") as file:
			file_base64 = base64.b64encode(file.read())
		# self.archivo_nombre = str(self.name) + '.xlsx'
		# self.write({'archivo_archivo': file_base64, })
		return file_base64
	
	def reporte_cuentasxpagar(self):
		file_name = self.ruta_tmp()
		total_total = 0
		total_saldo = 0
		
		workbook = xlsxwriter.Workbook(file_name, {'in_memory': True})
		worksheet = workbook.add_worksheet("Cuentas por pagar")
		fc = self.cfg_formato_cabecera(workbook)
		fm = self.cfg_formato_moneda(workbook)
		fm_b = self.cfg_formato_moneda_bold(workbook)
		ft = self.cfg_formato_titulo(workbook)
		ff = self.cfg_formato_fecha(workbook)
		
		# Ancho de columnas.
		worksheet.set_column(1, 1, 50)
		worksheet.set_column(2, 2, 20)
		worksheet.set_column(3, 3, 20)
		worksheet.set_column(4, 4, 20)
		worksheet.set_column(5, 5, 20)
		worksheet.set_column(6, 6, 60)

		
		rowi = 2
		coli = 1
		row = 0
		
		sql = """
select
f.id id,
f.reference folio,
f.date_invoice fecha,
p.display_name persona,
f.amount_total total,
f.residual saldo,
f.comment comentarios
from account_invoice as f
	inner join res_partner as p on(f.partner_id=p.id)
where
f.state='open'
and f.type='in_invoice'
and f.company_id={}
order by f.residual desc
""".format(self.empresa_id())
		self.env.cr.execute(sql)
		facturas = self.env.cr.dictfetchall()
		
		# General.
		worksheet.write_datetime('B1', datetime.datetime.now(), ff)
		worksheet.merge_range('B2:H2', 'SOLUCIONES LOGISTICAS INTELIGENTES SA DE CV', ft)
		
		# Cabecera.
		worksheet.write(rowi + row, coli + 0, "CLIENTE", fc)
		worksheet.write(rowi + row, coli + 1, "FOLIO", fc)
		worksheet.write(rowi + row, coli + 2, "FECHA", fc)
		worksheet.write(rowi + row, coli + 3, "TOTAL", fc)
		worksheet.write(rowi + row, coli + 4, "SALDO", fc)
		worksheet.write(rowi + row, coli + 5, "COENTARIOS", fc)
		
		# Datos.
		for f in facturas:
			row += 1
			worksheet.write(rowi + row, coli + 0, f['persona'])
			worksheet.write(rowi + row, coli + 1, f['folio'])
			worksheet.write(rowi + row, coli + 2, f['fecha'])
			worksheet.write_number(rowi + row, coli + 3, f['total'], fm)
			worksheet.write_number(rowi + row, coli + 4, f['saldo'], fm)
			worksheet.write(rowi + row, coli + 5, f['comentarios'])
			total_total += f['total']
			total_saldo += f['saldo']
	
		row += 1
		worksheet.write(rowi + row, coli + 3, total_total, fm_b)
		worksheet.write(rowi + row, coli + 4, total_saldo, fm_b)
		
		workbook.close()
		with open(file_name, "rb") as file:
			file_base64 = base64.b64encode(file.read())
		# self.archivo_nombre = str(self.name) + '.xlsx'
		# self.write({'archivo_archivo': file_base64, })
		return file_base64
	
	def reporte_cuentasxcobrar_flete(self):
		file_name = self.ruta_tmp()
		
		total_total = 0
		total_saldo = 0
		
		workbook = xlsxwriter.Workbook(file_name, {'in_memory': True})
		worksheet = workbook.add_worksheet("Cuentas por cobrar flete")
		fc = self.cfg_formato_cabecera(workbook)
		fm = self.cfg_formato_moneda(workbook)
		fm_b = self.cfg_formato_moneda_bold(workbook)
		ft = self.cfg_formato_titulo(workbook)
		ff = self.cfg_formato_fecha(workbook)
		
		# Ancho de columnas.
		worksheet.set_column(1, 1, 20)
		worksheet.set_column(2, 2, 20)
		worksheet.set_column(3, 3, 50)
		worksheet.set_column(4, 4, 20)
		worksheet.set_column(5, 5, 20)
		worksheet.set_column(6, 6, 20)
		worksheet.set_column(7, 7, 20)
		worksheet.set_column(8, 8, 50)
		
		rowi = 2
		coli = 1
		row = 0
		
		sql = """
select
f.id as id,
f.number as folio_interno,
f.number as folio,
f.date_invoice as fecha,
p.display_name as persona,
f.amount_total as total,
f.residual as saldo,
lne.name lineanegocio
from account_invoice as f
	inner join res_partner as p on(f.partner_id=p.id)
	left join trafitec_lineanegocio as lne on(f.lineanegocio=lne.id)
where
f.state='open'
and f.lineanegocio is not null
and f.type='out_invoice'
and f.residual>0
and f.company_id={}
""".format(self.empresa_id())
		self.env.cr.execute(sql)
		facturas = self.env.cr.dictfetchall()
		
		# General.
		worksheet.write_datetime('B1', datetime.datetime.now(), ff)
		worksheet.merge_range('B2:G2', 'SOLUCIONES LOGISTICAS INTELIGENTES SA DE CV', ft)
		
		# Cabecera.
		worksheet.write(rowi + row, coli + 0, "FOLIO", fc)
		worksheet.write(rowi + row, coli + 1, "FECHA", fc)
		worksheet.write(rowi + row, coli + 2, "PERSONA", fc)
		worksheet.write(rowi + row, coli + 3, "TOTAL", fc)
		worksheet.write(rowi + row, coli + 4, "SALDO", fc)
		worksheet.write(rowi + row, coli + 5, "LINEA DE NEGOCIO", fc)
		
		# Datos.
		for f in facturas:
			row += 1
			worksheet.write(rowi + row, coli + 0, f['folio'])
			worksheet.write(rowi + row, coli + 1, f['fecha'])
			worksheet.write(rowi + row, coli + 2, f['persona'])
			worksheet.write_number(rowi + row, coli + 3, f['total'], fm)
			worksheet.write_number(rowi + row, coli + 4, f['saldo'], fm)
			worksheet.write(rowi + row, coli + 5, f['lineanegocio'])
			
			total_total += f['total']
			total_saldo += f['saldo']
		
		row += 1
		worksheet.write(rowi + row, coli + 3, total_total,fm_b)
		worksheet.write(rowi + row, coli + 4, total_saldo,fm_b)
		
		workbook.close()
		with open(file_name, "rb") as file:
			file_base64 = base64.b64encode(file.read())
		return file_base64
	
	def reporte_cuentasxpagar_flete(self):
		file_name = self.ruta_tmp()
		
		total_total = 0
		total_saldo = 0
		
		workbook = xlsxwriter.Workbook(file_name, {'in_memory': True})
		worksheet = workbook.add_worksheet("Cuentas por pagar flete")
		fc = self.cfg_formato_cabecera(workbook)
		fm = self.cfg_formato_moneda(workbook)
		fm_b = self.cfg_formato_moneda_bold(workbook)
		ft = self.cfg_formato_titulo(workbook)
		ff = self.cfg_formato_fecha(workbook)
		
		# Ancho de columnas.
		worksheet.set_column(1, 1, 20)
		worksheet.set_column(2, 2, 20)
		worksheet.set_column(3, 3, 50)
		worksheet.set_column(4, 4, 20)
		worksheet.set_column(5, 5, 20)
		worksheet.set_column(6, 6, 20)
		worksheet.set_column(7, 7, 20)
		worksheet.set_column(8, 8, 50)
		
		rowi = 2
		coli = 1
		row = 0
		
		sql = """
select
f.id as id,
f.number as folio_interno,
f.reference as folio,
f.date_invoice as fecha,
p.display_name as persona,
case p.asociado when true then 'SI' else 'NO' end es_asociado,
f.amount_total as total,
f.residual as saldo,
cr.name as cr_folio,
cr.fecha as cr_fecha,
(select
string_agg(cli.display_name,', ')
from contrarecibo_viaje_relation x
	inner join trafitec_viajes as v on(x.viajes_id=v.id)
    inner join res_partner as cli on(v.cliente_id=cli.id)
where x.contrarecibo_id=cr.id
) cliente
from trafitec_contrarecibo as cr
	inner join account_invoice as f on(cr.invoice_id=f.id)
	inner join res_partner as p on(f.partner_id=p.id and p.asociado=True)
where
cr.state='Validada'
and f.state='open'
and f.type='in_invoice'
and f.residual>0
and f.company_id={}
""".format(self.empresa_id())
		self.env.cr.execute(sql)
		facturas = self.env.cr.dictfetchall()
		
		# General.
		worksheet.write_datetime('B1', datetime.datetime.now(), ff)
		worksheet.merge_range('B2:I2', 'SOLUCIONES LOGISTICAS INTELIGENTES SA DE CV', ft)
		
		# Cabecera.
		worksheet.write(rowi + row, coli + 0, "FOLIO", fc)
		worksheet.write(rowi + row, coli + 1, "FECHA", fc)
		worksheet.write(rowi + row, coli + 2, "PERSONA", fc)
		worksheet.write(rowi + row, coli + 3, "TOTAL", fc)
		worksheet.write(rowi + row, coli + 4, "SALDO", fc)
		worksheet.write(rowi + row, coli + 5, "FOLIO CR", fc)
		worksheet.write(rowi + row, coli + 6, "FECHA CR", fc)
		worksheet.write(rowi + row, coli + 7, "CLIENTE", fc)
		
		# Datos.
		for f in facturas:
			row += 1
			worksheet.write(rowi + row, coli + 0, f['folio'])
			worksheet.write(rowi + row, coli + 1, f['fecha'])
			worksheet.write(rowi + row, coli + 2, f['persona'])
			worksheet.write_number(rowi + row, coli + 3, f['total'], fm)
			worksheet.write_number(rowi + row, coli + 4, f['saldo'], fm)
			worksheet.write(rowi + row, coli + 5, f['cr_folio'])
			worksheet.write(rowi + row, coli + 6, f['cr_fecha'])
			worksheet.write(rowi + row, coli + 7, f['cliente'])
			
			total_total += f['total']
			total_saldo += f['saldo']
		
		row += 1
		worksheet.write(rowi + row, coli + 3, total_total,fm_b)
		worksheet.write(rowi + row, coli + 4, total_saldo,fm_b)
		
		workbook.close()
		with open(file_name, "rb") as file:
			file_base64 = base64.b64encode(file.read())
		return file_base64
	
	def reporte_operaciones_pedidos_estado(self):
		file_name = self.ruta_tmp()
		
		total_total = 0
		total_saldo = 0
		
		workbook = xlsxwriter.Workbook(file_name, {'in_memory': True})
		worksheet = workbook.add_worksheet("Estado de pedidos (Cotizaciones)")
		fc = self.cfg_formato_cabecera(workbook)
		fm = self.cfg_formato_moneda(workbook)
		fto = self.cfg_formato_tons(workbook)
		fp = self.cfg_formato_por(workbook)
		fm_b = self.cfg_formato_moneda_bold(workbook)
		ft = self.cfg_formato_titulo(workbook)
		ff = self.cfg_formato_fecha(workbook)
		
		# Ancho de columnas.
		worksheet.set_column(1, 1, 20)
		worksheet.set_column(2, 2, 20)
		worksheet.set_column(3, 3, 20)
		worksheet.set_column(4, 4, 20)
		worksheet.set_column(5, 5, 20)
		worksheet.set_column(6, 6, 20)
		worksheet.set_column(7, 7, 20)
		worksheet.set_column(8, 8, 20)
		worksheet.set_column(9, 9, 20)
		
		rowi = 2
		coli = 1
		row = 0
		
		sql = """
select
ct.name folio,
ct.fecha fecha,
cli.display_name cliente,
prot.name producto,
coalesce((
select
sum(ori.cantidad)
from trafitec_cotizaciones_linea_origen as ori
    inner join trafitec_cotizaciones_linea as lin on(ori.linea_id=lin.id)
where lin.cotizacion_id=ct.id
),0) as total_cotizacion,
coalesce((
select
sum(v1.peso_origen_total/1000)
from trafitec_viajes as v1
	inner join trafitec_cotizaciones_linea_origen as ori on(v1.subpedido_id=ori.id)
    inner join trafitec_cotizaciones_linea as lin on(ori.linea_id=lin.id)
where v1.state in('Nueva') and lin.cotizacion_id=ct.id
),0) as total_viajes,

ct.state estado
from trafitec_cotizacion as ct
	inner join res_partner as cli on(ct.cliente=cli.id)
	inner join product_product as pro on(ct.product=pro.id)
    inner join product_template as prot on(pro.product_tmpl_id=prot.id)
where ct.state in('Disponible')
""".format(self.empresa_id())
		self.env.cr.execute(sql)
		facturas = self.env.cr.dictfetchall()
		
		# General.
		worksheet.write_datetime('B1', datetime.datetime.now(), ff)
		worksheet.merge_range('B2:J2', 'SOLUCIONES LOGISTICAS INTELIGENTES SA DE CV', ft)
		
		# Cabecera.
		worksheet.write(rowi + row, coli + 0, "FOLIO", fc)
		worksheet.write(rowi + row, coli + 1, "FECHA", fc)
		worksheet.write(rowi + row, coli + 2, "CLIENTE", fc)
		worksheet.write(rowi + row, coli + 3, "PRODUCTO", fc)
		worksheet.write(rowi + row, coli + 4, "TOTAL (TONS)", fc)
		worksheet.write(rowi + row, coli + 5, "MOVIDO (TONS)", fc)
		worksheet.write(rowi + row, coli + 6, "SALDO (TONS)", fc)
		worksheet.write(rowi + row, coli + 7, "NO VIAJES RESTANTES", fc)
		worksheet.write(rowi + row, coli + 8, "PORCENTAJE AVANCE (%)", fc)
		
		# Datos.
		for f in facturas:
			total_cotizacion = f['total_cotizacion']
			total_viajes = f['total_viajes']
			total_saldo = total_cotizacion - total_viajes
			
			saldo_viajes = total_saldo / 70
			porcentaje_avance = total_viajes * 100.00 / total_cotizacion
			
			row += 1
			worksheet.write(rowi + row, coli + 0, f['folio'])
			worksheet.write(rowi + row, coli + 1, f['fecha'])
			worksheet.write(rowi + row, coli + 2, f['cliente'])
			worksheet.write(rowi + row, coli + 3, f['producto'])
			worksheet.write_number(rowi + row, coli + 4, total_cotizacion, fto)
			worksheet.write_number(rowi + row, coli + 5, total_viajes, fto)
			worksheet.write_number(rowi + row, coli + 6, total_saldo, fto)
			worksheet.write_number(rowi + row, coli + 7, saldo_viajes, fm)
			worksheet.write_number(rowi + row, coli + 8, porcentaje_avance, fp)
			
		
		row += 1
		
		workbook.close()
		with open(file_name, "rb") as file:
			file_base64 = base64.b64encode(file.read())
		return file_base64



