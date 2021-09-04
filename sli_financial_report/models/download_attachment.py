from odoo import _, api, exceptions, fields, models


class DownloadAttachment(models.Model):
	_name = 'download.attachment'
	_description = 'Download attachment'

	file = fields.Binary(
		string='Archivo',
		readonly=True
	)
	filename = fields.Char(string='Nombre del archivo')
	active_model = fields.Char(string='Modelo')
	active_id = fields.Char(string='ID Activo')
	attachment_ids = fields.Many2many(
		'ir.attachment', 
		string='Adjuntos'
	)
