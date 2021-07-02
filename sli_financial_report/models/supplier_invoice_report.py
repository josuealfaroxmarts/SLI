# -*- coding: utf-8 -*-
# Viridiana Cruz Santos

import xlwt
import base64
from io import StringIO
from odoo import _, api, exceptions, fields, models, tools
from odoo.tools import float_is_zero

class SupplierInvoiceReport(models.Model):
	_name = "supplier.invoice.report"


	partner_id = fields.Many2one('res.partner', string='Proveedor', required=True, domain=[('supplier', '=', True)])
	date_from = fields.Date(string='De')
	date_to = fields.Date(string='A')


	
	def print_xls(self):
		csv_id = self.action_invoice_report()
		return {
			'type': 'ir.actions.act_url',
			'url': '/web/content/reportdownload/%s/file/%s?download=true' %(csv_id.id, csv_id.file_name),
			'target': 'self',
			'context': '{"partner_id":"%s", "date_from":"%s", "date_to":"%s"}' % (self.partner_id.id, self.date_from, self.date_to),
			}


	
	def action_invoice_report(self):
		file = StringIO()
		account_invoice_obj = self.env['account.move'].search([
																('partner_id', '=', self.partner_id.id),
																('date', '>=', self.date_from),
																('date', '<=', self.date_to),
																('state', '=', 'paid')
																])

		final_value = {}
		workbook = xlwt.Workbook()
		sheet = workbook.add_sheet('Facturas de Proveedor')

		format0 = xlwt.easyxf('font:height 500,bold True;pattern: pattern solid, fore_colour gray40;align: horiz center')
		format1 = xlwt.easyxf('font:bold True;pattern: pattern solid, fore_colour gray40;align: horiz left')
		format2 = xlwt.easyxf('font:bold True;align: horiz left')
		format3 = xlwt.easyxf('align: horiz left')
		format4 = xlwt.easyxf('align: horiz right')
		format5 = xlwt.easyxf('font:bold True;pattern: pattern solid, fore_colour gray25; align: horiz left')

		sheet.write_merge(0, 2, 0, 7, 'Facturas emitidas: ' + self.date_from + ' / ' + self.date_to , format0)
		
		sheet.write(5, 0, 'Proveedor', format1)
		sheet.write_merge(5, 5, 1, 7, self.partner_id.name, format2)

		invoice_lines = []
		if account_invoice_obj:
			for data in account_invoice_obj:
				invoice = {
					'invoice_id': data.id,
					'invoice_number' : data.number,
					'invoice_date' : data.date_invoice,
					'amount_total' : data.amount_total,
					'residual': data.residual
				}

				invoice_lines.append(invoice)
			
			row = 7
			for rec in invoice_lines:
				sheet.write(row, 0, '', format3)
				sheet.write(row, 1, '', format3)
				sheet.write(row, 2, '', format3)
				sheet.write(row, 3, '', format3)

				row += 1

				sheet.write(row, 0, 'FOLIO FACTURA', format1)
				sheet.write(row, 1, 'FECHA FACTURA', format1)
				sheet.write(row, 2, 'TOTAL', format1)
				sheet.write(row, 3, 'SALDO PENDIENTE', format1)
				
				row +=1

				sheet.write(row, 0, rec.get('invoice_number'), format3)
				sheet.write(row, 1, rec.get('invoice_date'), format3)
				sheet.write(row, 2, rec.get('amount_total'), format4)
				sheet.write(row, 3, rec.get('residual'), format4)
				
				row += 1

				invoice = self.env['account.move'].search([('id', '=', rec.get('invoice_id'))])

				if invoice.payment_move_line_ids:
					sheet.write(row, 0, 'FOLIO PAGO', format5)
					sheet.write(row, 1, 'FECHA PAGO', format5)
					sheet.write(row, 2, 'MONTO APLICADO EN FACTURA', format5)
					sheet.write(row, 3, 'MONTO TOTAL DEL PAGO', format5)

					row += 1
					for payment in invoice.payment_move_line_ids:
						payment_currency_id = False

						if invoice.type in ('out_invoice', 'in_refund'):
							amount = sum([p.amount for p in payment.matched_debit_ids if p.debit_move_id in invoice.move_id.line_ids])
							amount_currency = sum([p.amount_currency for p in payment.matched_debit_ids if p.debit_move_id in invoice.move_id.line_ids])
							if payment.matched_debit_ids:
								payment_currency_id = all([p.currency_id == payment.matched_debit_ids[0].currency_id for p in payment.matched_debit_ids]) and payment.matched_debit_ids[0].currency_id or False

						if invoice.type in ('in_invoice', 'out_refund'):
							amount = sum([p.amount for p in payment.matched_credit_ids if p.credit_move_id in invoice.move_id.line_ids])
							amount_currency = sum([p.amount_currency for p in payment.matched_credit_ids if p.credit_move_id in invoice.move_id.line_ids])
							if payment.matched_credit_ids:
								payment_currency_id = all([p.currency_id == payment.matched_credit_ids[0].currency_id for p in payment.matched_credit_ids]) and payment.matched_credit_ids[0].currency_id or False
						if payment_currency_id and payment_currency_id == invoice.currency_id:
							amount_to_show = amount_currency
						else:
							amount_to_show = payment.company_id.currency_id.with_context(date=payment.date).compute(amount, invoice.currency_id)
							if float_is_zero(amount_to_show, precision_rounding=invoice.currency_id.rounding):
								continue
						
						sheet.write(row, 0, payment.payment_id.name, format3)
						sheet.write(row, 1, payment.payment_id.payment_date, format3)
						sheet.write(row, 2, amount_to_show, format3)
						sheet.write(row, 3, payment.payment_id.amount, format3)

						row += 1

		else:
			raise exceptions.Warning(_("No se encontraron registros"))
		row += 2
		

		workbook.save('/tmp/Facturas_proveedor.xls')
		file = open('/tmp/Facturas_proveedor.xls', 'rb').read()
		out = base64.encodestring(file)

		return self.env['reportdownload'].create(
												vals={
												'file_name': 'Facturas_proveedor.xls',
												'type_file': '.xls',
												'file': out,
												})
