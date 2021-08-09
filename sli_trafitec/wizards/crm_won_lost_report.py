# -*- coding: utf-8 -*-

import xlsxwriter
import base64

from odoo import models, fields, api, _, tools


class CrmReport(models.TransientModel):
	_name = 'crm.won.lost.report'
	_description = 'crm won lost report'
	
	sales_person = fields.Many2one('res.users', string="Sales Person")
	start_date = fields.Date('Start Date')
	end_date = fields.Date('End Date', default=fields.Date.today)

	def print_xls_report(self):
		workbook = xlsxwriter.Workbook('hello_world.xlsx')
		worksheet = workbook.add_worksheet()
		worksheet.write('A1', 'Hello world')
		workbook.close()

	def export(self):
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
			for vals in self.carrier_line_ids:
				worksheet.write(row, 0, vals.ref)
			workbook.close()
			with open(file_name, "rb") as file:
				file_base64 = base64.b64encode(file.read())
			rec.carrier_xlsx_document_name = rec.name + '.xlsx'
			rec.write({'carrier_xlsx_document': file_base64, })