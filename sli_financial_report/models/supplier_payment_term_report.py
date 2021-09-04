import base64
import xlwt

from datetime import datetime
from io import StringIO

from odoo import _, api, exceptions, fields, models, tools


class SupplierPaymentTermReport(models.Model):
	_name = 'supplier.payment.term.report'
	_description = 'Supplier payment report'

	date_from = fields.Date(string='De')
	date_to = fields.Date(string='A')
	file_name = fields.Char(string='Nombre del archivo')
	type_file = fields.Char(string='Tipo de archivo')
	file = fields.Binary(string='Descargar archivo')
	partner_id = fields.Many2one(
		'res.partner', 
		string='Proveedor', 
		required=True,
		domain=[('supplier_rank', '>=', 1)]
	)

	def print_xls(self):
		file = StringIO()

		account_invoice_obj = self.env['account.move'].search([
			('partner_id', '=', self.partner_id.id),
			('date', '>=', self.date_from),
			('date', '<=', self.date_to),
			('state', '=', 'posted')
		])

		final_value = {}
		workbook = xlwt.Workbook()
		sheet = workbook.add_sheet('Cartera vencida proveedores')

		format0 = xlwt.easyxf(
			'font:height 500,bold True;pattern: pattern solid, '
			'fore_colour gray40;align: horiz center'
		)
		format1 = xlwt.easyxf(
			'font:bold True;pattern: pattern solid,'
			' fore_colour gray40;align: horiz left'
		)
		format2 = xlwt.easyxf('font:bold True;align: horiz left')
		format3 = xlwt.easyxf('align: horiz left')
		format4 = xlwt.easyxf('align: horiz right')
		format5 = xlwt.easyxf(
			'font:bold True;pattern: pattern solid, '
			'fore_colour gray25; align: horiz left'
		)
		format6 = xlwt.easyxf(
			'pattern: pattern solid, fore_colour red; align: horiz right')

		sheet.write_merge(
			0, 2, 0, 13, 'Facturas emitidas: '
			             + self.date_from + ' / '
			             + self.date_to, format0
		)

		row = 5

		sheet.write(row, 0, 'PROVEEDOR', format5)
		sheet.write(row, 1, 'FOLIO FACTURA', format5)
		sheet.write(row, 2, 'FECHA FACTURA', format5)
		sheet.write(row, 3, 'FECHA VENCIMIENTO', format5)
		sheet.write(row, 4, 'LIMITE DE CREDITO', format5)
		sheet.write(row, 5, 'DIAS DE CREDITO', format5)
		sheet.write(row, 6, 'ESTADO', format5)
		sheet.write(row, 7, 'TOTAL', format5)
		sheet.write(row, 8, 'SALDO PENDIENTE', format5)
		sheet.write(row, 9, '01 A 15 DIAS', format5)
		sheet.write(row, 10, '16 A 30 DIAS', format5)
		sheet.write(row, 11, '31 A 45 DIAS', format5)
		sheet.write(row, 12, '45 A + DIAS', format5)
		sheet.write(row, 13, 'DIAS DE VENCIMIENTO', format5)

		row += 1

		if account_invoice_obj:
			for invoice in account_invoice_obj:
				if invoice.type in ('in_invoice','in_refund'):

					if invoice.state == 'open':
						state = 'Abierta'

					partner_payment_term = invoice.partner_id.property_supplier_payment_term_id.name

					sheet.write(row, 0, invoice.partner_id.name, format3)
					sheet.write(row, 1, invoice.number, format3)
					sheet.write(row, 2, invoice.date_invoice, format4)
					sheet.write(row, 3, invoice.date_due, format4)
					sheet.write(row, 4, invoice.partner_id.limite_credito, format4)
					sheet.write(row, 5, partner_payment_term, format4)
					sheet.write(row, 6, state, format4)
					sheet.write(row, 7, invoice.amount_total, format4)
					sheet.write(row, 8, invoice.residual, format4)

					if invoice.date_due:
						datetime_invoice = datetime.strptime(invoice.date_due, '%Y-%m-%d')
						due_invoice = datetime_invoice.date()

						today_date = datetime.strptime(fields.Date.today(), '%Y-%m-%d')
						today = today_date.date()
						
						diff_days = today - due_invoice
						days = diff_days.days

						if days >= 1 and days <= 15:
							sheet.write(row, 9, invoice.residual, format6)

						if days >= 16 and days <= 30:
							sheet.write(row, 10, invoice.residual, format6)

						if days >= 31 and days <= 45:
							sheet.write(row, 11, invoice.residual, format6)

						if days >= 46:
							sheet.write(row, 12, invoice.residual, format6)

						sheet.write(row, 13, days, format4)
					
					row += 1

		else:
			raise exceptions.Warning(_('No se encontraron registros'))
		row += 2

		workbook.save('/tmp/Cartera_vencida_proveedores.xls')
		file = open('/tmp/Cartera_vencida_proveedores.xls', 'rb').read()
		out = base64.encodestring(file)
		self.write({
				'file_name': 'Cartera_vencida_proveedores.xls',
				'type_file': '.xls',
				'file': out,
				})
		return {
			'type': 'ir.actions.act_window',
			'res_id': self.id,
			'view_mode': 'form',
			'res_model': 'supplier.payment.term.report',
			'target': 'new',
			'name': 'Cartera vencida proveedores'
		}


