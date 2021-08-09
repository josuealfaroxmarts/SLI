# -*- coding: utf-8 -*-

import base64
from odoo import models, fields, api, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from xml.dom import minidom


class trafitec_facturas_documentos(models.Model):
	_name = 'trafitec.facturas.documentos'
	_description ='facturas documentos'


	name = fields.Selection(string='Tipo',
							selection=[('cartaporte_pdf', 'Carta porte PDF'), ('cartaporte_xml', 'Carta porte XML')],
							required=True, default='cartaporte_pdf')
	documento_nombre = fields.Char('Nombre del archivo')
	documento_archivo = fields.Binary(string='Archivo', required=True)
	factura_id = fields.Many2one(comodel_name='account.move', string='Factura', ondelete='cascade')

	
	@api.constrains('documento_nombre')
	def _check_filename(self):
		if self.documento_archivo:
			if self.documento_nombre:
				raise UserError(_('Alerta..\n No hay archivo.'))
			else:
				# Check the file's extension
				tmp = self.documento_nombre.split('.')
				ext = tmp[len(tmp) - 1]
				if ext != 'pdf' and self.name == 'cartaporte_pdf':
					raise UserError(_('Alerta..\nSolo se permiten archivos pdf para.'))
				if ext != 'xml' and self.name == 'cartaporte_xml':
					raise UserError(_('Alerta..\nSolo se permiten archivos xml para el cfdi.'))