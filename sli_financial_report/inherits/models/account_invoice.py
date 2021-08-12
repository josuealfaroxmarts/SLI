# -*- coding: utf-8 -*-
# Viridiana Cruz Santos

from odoo import api, fields, models


class AccountInvoice(models.Model):
	_inherit = "account.move"

	file_pdf = fields.Binary(
		string="Archivo PDF",
		compute='_get_file',
		readonly=True
	)
	filename_pdf = fields.Char(string="Nombre del archivo PDF")
	file_xml = fields.Binary(
		string="Archivo XML",
		compute='_get_file',
		readonly=True
	)
	filename_xml = fields.Char(string="Nombre del archivo XML")

	def _get_file(self):
		for invoice in self:
			attachment_obj = self.env['ir.attachment'].search([('res_id', '=', invoice.id),
															('res_model', '=', 'account.move')
														])

			for attachment in attachment_obj:
				if attachment.mimetype == 'application/pdf':
					invoice.file_pdf = attachment.datas
					invoice.filename_pdf = attachment.datas_fname

				if attachment.mimetype == 'application/xml':
					invoice.file_xml = attachment.datas
					invoice.filename_xml = attachment.datas_fname