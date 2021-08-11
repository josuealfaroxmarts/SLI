# -*- coding: utf-8 -*-
# Viridiana Cruz Santos

from odoo import _, api, exceptions, fields, models


class ReportDownload(models.Model):
	_name = "reportdownload"
	_description = "Download"

	file_name = fields.Char(string="Nombre del archivo")
	type_file = fields.Char(string="Tipo de archivo")
	file = fields.Binary(string="Archivo")