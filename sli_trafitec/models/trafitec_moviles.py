# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from . import amount_to_text
import xlsxwriter
import base64


class trafitec_tiposmovil(models.Model):
	_name = 'trafitec.moviles'
	_description ='tipo moviles'

	name = fields.Char(
		string='Nombre', 
		required=True
	)
	tipomovil = fields.Selection(
		[
			('vehiculo', 'Vehículo'), 
			('remolque', 'Remolque')
		], 
		string='Tipo de móvil',
		required=True
	)
	tipo = fields.Selection(
		[
			('full', 'Full'), 
			('sencillo', 'Sencillo')
		], 
		string='Tipo', 
		required=True
	)
	capacidad = fields.Float(
		string='Capacidad (Tons)', 
		required=True, 
		default=0
	)
	unidadmedida = fields.Many2one(
		'uom.uom', 
		string='Unidad de medida', 
		readonly=True
	)
	lineanegocio = fields.Many2one(
		comodel_name='trafitec.lineanegocio', 
		string='Linea de negocio'
	)