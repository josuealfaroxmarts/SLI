# -*- coding: utf-8 -*-

import xlsxwriter
import base64

from odoo import models, fields, api, _, tools


class TrafitecParametros(models.TransientModel):
	_name = 'trafitec.reportes.parametros'
	_description = 'Parametros'
	
	fecha_inicial = fields.Date(string="Fecha incial")
	fecha_final = fields.Date(string="Fecha final")
	archivo_nombre = fields.Char(string="Nombre del archivo")
	archivo_archivo = fields.Binary(string="Archivo")

	@api.model
	def render_html2(self, docids, data=None):
		docargs = {}
		return self.env['report'].render(
			'SLI_TrafitecReportesX.report_viaje_general',
			docargs
		)

	@api.model
	def render_html3(self, docids, data=None):
		report_obj = self.env['report']
		report = report_obj._get_report_from_name('report_viaje_general')
		docids == [150, 151, 148]
		docargs = {'doc_ids': docids, 'doc_model': report.model, 'docs': self}
		return report_obj.render(
			'SLI_TrafitecReportesX.report_viaje_general',
			docargs
		)

	@api.model
	def render_html4(self, docids, data=None):
		report_obj = self.env['report']
		report = report_obj._get_report_from_name(
			'SLI_TrafitecReportesX.report_viaje_general'
		)
		docs = self.env['trafitec.viajes'].browse([151, 150])
		docargs = {
			'doc_ids': [151, 150],
			'doc_model': report.model,
			'docs': docs
		}
		return self.env['report'].render(
			'SLI_TrafitecReportesX.report_viaje_general',
			docargs
		)

	def render_html(self):
		context = None
		ids = [1, 2, 3]
		if ids:
			if not isinstance(ids, list):
				ids = [ids]
			context = dict(
				context or {},
				active_ids=ids,
				active_model=self._name,
				data={
					'fecha_inicial': self.fecha_inicial,
					'fecha_final': self.fecha_final
				}
			)
		return {
			'type': 'ir.actions.report.xml',
			'report_name': 'SLI_TrafitecReportesX.report_viaje_general',
			'context': context
		}

	def export_xls(self):
		for rec in self:
			file_name = 'temp'
			workbook = xlsxwriter.Workbook(file_name, {'in_memory': True})
			worksheet = workbook.add_worksheet()
			row = 0
			col = 0
			header = []

			for e in header:
				worksheet.write(row, col, e)
				col += 1
			row += 1
			for vals in rec.carrier_line_ids:
				worksheet.write(row, 0, vals.ref)
			workbook.close()
			with open(file_name, "rb") as file:
				file_base64 = base64.b64encode(file.read())
			rec.archivo_nombre = rec.name + '.xlsx'
			rec.write({'archivo_archivo': file_base64, })