# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class trafitec_cliente_documentos(models.Model):
	_name = 'trafitec.clientes.documentos'
	_description = 'Documentos clientes'
	
	name = fields.Many2one(
		'trafitec.tipodoc',
		string='Documento requerido',
		required=True
	)
	tipo_tipo = fields.Selection(string='Tipo', related='name.tipo')
	tipo_evidencia = fields.Boolean(
		string='Evidencia',
		related='name.evidencia'
	)
	tipo_dmc = fields.Boolean(string='DMC', related='name.dmc')
	partner_id = fields.Many2one('res.partner')