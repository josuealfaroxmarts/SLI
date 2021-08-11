# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from . import amount_to_text
import xlsxwriter
import base64


class TrafitecUbicacion(models.Model):
	_name = 'trafitec.ubicacion'
	_description ='ubicacion'

	# MODIFICACIONE RECIENTE ALTA DE UBICACIONES
	name = fields.Char(
		string='Nombre', 
		required=True
	)
	calle = fields.Char(
		string='Calle', 
		required=True
	)
	noexterior = fields.Char(
		string='No. Exterior', 
		required=True
	)
	nointerior = fields.Char(string='No. Interior')
	localidad = fields.Many2one(
		'l10n_mx_edi.res.locality', 
		string='Localidad'
	)
	colonia = fields.Char(
		string='Colonia', 
		required=True
	)
	estado = fields.Char(
		string='Estado', 
		required=True
	)
	codigo_postal = fields.Char(
		string='Codigo Postal', 
		required=True
	)
	ciudad = fields.Char(
		string='Ciudad', 
		required=True
	)
	cruce = fields.Char(string='Cruce')
	responsable = fields.Char(string='Responsable')
	coberturacelular = fields.Boolean(string='Cobertura de celular')
	latitud = fields.Float(string='Latitud')
	longitud = fields.Float(string='Longitud')
	cap_carga = fields.Float(string='Capacidad de carga')
	cap_descarga = fields.Float(string='Capacidad de descarga')
	bodega_prob = fields.Boolean(string='Es bodega problematica')
	tipo_ubicacion = fields.Selection(
		[
			('almacen', 'Almacén'), 
			('puerto', 'Puerto')
		], 
		string='Tipo de ubicacion'
	)
	tipo_carga = fields.Selection(
		[
			('carga', 'Carga'), 
			('descarga', 'Descarga'), 
			('carga/descarga', 'Carga/Descarga')
		],
		string='Tipo de carga'
	)
	comentarios = fields.Text(string='Comentarios')
	cliente_ubicacion = fields.Many2one(
		'res.partner', 
		string='Cliente'
	)
	responsable_id = fields.One2many(
		'trafitec.responsable', 
		'responsable', 
		string='id responsable'
	)

	#TODO HABLAR CON EL CONSULTOR LINEA 130
	#municipio = fields.Many2one(
	# string='Municipio', 
	# store=True, 
	# related='localidad.zip_sat_code.township_sat_code'
	#)
	# FIN MODIFICACION RECIENTE ALTA DE UBICACIONES

	active = fields.Boolean(
		string='Activo', 
		default=True
	)


	@api.constrains('name')
	def _check_constrains(self):
		if self.name:
			name_obj = self.env['trafitec.ubicacion'].search([('name', 'ilike', self.name)])
			if len(name_obj) > 1:
				raise UserError(_('Aviso !\nEl nombre de la ubicación no se puede repetir.'))
