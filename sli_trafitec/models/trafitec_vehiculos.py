# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from . import amount_to_text
import xlsxwriter
import base64

	
class trafitec_vehiculos(models.Model):
	_inherit = 'fleet.vehicle'
	_order = 'id desc'

	color_vehicle = fields.Char(string='Color Vehiculo')
	ejes_tracktocamion = fields.Selection(
		[
			('C2', 'C2'), 
			('C3', 'C3'), 
			('T3', 'T3'), 
			('S2', 'S2'), 
			('S3', 'S3'), 
			('S2-R4', 'S2-R4') 
		], 
		string='Tipo de Eje'
	)
	tiposervicio = fields.Selection(
		[
			('Estatal', 'Estatal'), 
			('Federal', 'Federal')
		], 
		string='Tipo de servicio'
	)
	asociado_id = fields.Many2one(
		'res.partner', 
		domain=[
			('asociado', '=', True), 
			(['company','person'],'in','company_type')
		], 
		string="Asociado"
	)
	operador_id = fields.Many2one(
		'res.partner', 
		domain=[
			('operador','=',True)
		], 
		string="Operador"
	)
	es_flotilla = fields.Boolean(string='Es flotilla')
	no_economico = fields.Char(string='No. economico')
	es_utilitario = fields.Boolean(string='Es utilitario')
	remolque_1_id = fields.Many2one(
		string='Remolque 1', 
		comodel_name='trafitec.remolques', 
		help='Remolque 1 del vehículo.', 
		domain=[
			('tipo', '=', 'remolque')
		]
	)
	dolly_id = fields.Many2one(
		string='Dolly', 
		comodel_name='trafitec.remolques', 
		help='El dolly del vehículo.', 
		domain=[
			('tipo', '=', 'dolly')
		]
	)
	remolque_2_id = fields.Many2one(
		string='Remolque 2', 
		comodel_name='trafitec.remolques', 
		help='Remolque 2 del vehículo en caso de Doble (Full).', 
		domain=[
			('tipo', '=', 'remolque')
		]
	)

	# Cambios
	vehicle_model = fields.Char(string='Marca y modelo vehiculo')
	modelo = fields.Char(string='Marca y modelo')
	numero_economico = fields.Char(string='Número Economico')
	tipo_vehiculo = fields.Selection(
		[
			("tractocamion", "Tractocamion"), 
			("remolque", "Remolque"), 
			("dolly", "Dolly")
		],
		string='Tipo de vehículo'
	)
	nombre_circulacion = fields.Char(
		string='Nombre tarjeta de circulación', 
		compute='change_name_vehicle_documents'
	)
	ext_circulacion = fields.Char(string='Extension archivo ciculacion')
	circulacion = fields.Binary(string='Tarjeta de circulación')
	nombre_poliza_seguro = fields.Char(
		string='Nombre poliza del seguro', 
		compute='change_name_vehicle_documents'
	)
	ext_poliza_seguro = fields.Char(string='extension archivo Poliza del seguro')
	poliza_seguro = fields.Binary(string='Poliza del seguro')
	fecha_poliza = fields.Date(string='Fecha de poliza')
	fecha_poliza = fields.Date(string='Fecha de vigencia de poliza')
	nombre_fisio = fields.Char(
		string='Verificaciones fisiomecanicas', 
		compute='change_name_vehicle_documents'
	)
	fisio = fields.Binary(string='Verificaciones fisio-mecanicas')
	fisio_fecha = fields.Date(string='Fecha de vigencia de la poliza')
	nombre_ambientales = fields.Char(
		string='Nombre verificaciones ambientales', 
		compute='change_name_vehicle_documents'
	)
	ambientales = fields.Binary(string='Verificaciones ambientales')
	ambientales_fecha = fields.Char(
		string='Fecha de vigencia poliza', 
		compute='change_name_vehicle_documents'
	)
	model_id = fields.Many2one(required=False)


	def change_name_vehicle_documents(self):
		if self.license_plate :
			self.nombre_circulacion = "Comprobante domicilio de Tarjeta de circulación ({}).{}".format(self.license_plate, 
				self.ext_circulacion)
			self.nombre_poliza_seguro = "Poliza del seguro ({}).{}".format(self.license_plate, 
				self.ext_poliza_seguro)
			self.nombre_fisio = "Verificaciones fisiomecanicas.png"
			self.nombre_ambientales = "Verificaciones ambientales.png"


	@api.onchange('license_plate')
	def _onchange_license_plate(self):
		try:
			placas = ''
			placas = (self.license_plate or '')
			placas = placas.strip()
			placas = placas.replace(" ", "")
			placas = placas.replace("-", "")
			placas = placas.replace("_", "")
			placas = placas.replace(".", "")
			placas = placas.replace("/", "")

			vehiculos = self.env['fleet.vehicle'].search([('license_plate', '=ilike', placas), 
				('id', '!=', self._origin.id)], limit=1)

		# self.info_alertas = ''
		# if vehiculos:
		#	  self.info_alertas = 'Las placas {} ya existen.'.format(placas, self.id)
		except:
			_logger.error("**Error al validar las placas.")

	# info_alertas = fields.Char(string='Alerta', default='', help='Muestra mensaje de alertas.')
	@api.depends('name', 'asociado_id', 'operador_id', 'remolque_1_id', 'dolly_id', 'remolque_2_id')
	def name_get(self):
		result = []
		name = ""
		for rec in self:
			name = (rec.name or "") + '/' + (rec.asociado_id.name or "") + '/' + (rec.operador_id.name or "") + " (" + (
					rec.remolque_1_id.name or "") + " " + (rec.dolly_id.name or "") + " " + (
							rec.remolque_2_id.name or "") + ")"
			result.append((rec.id, name))

			"""
			if rec.name and rec.asociado_id and rec.operador_id:
				name = (rec.name or "") + '/' + (rec.asociado_id.name or "") + '/' + (rec.operador_id.name or "")+" ("+(rec.remolque_1_id.name or "")+" "+(rec.dolly_id.name or "")+" "+(rec.remolque_2_id.name or "")+")"
				result.append((rec.id, name))
			else:
				name = (rec.name or "")
				result.append((rec.id, name))
			"""

		return result


	# SLI SUCURSALES
	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=10):
		args = args or []
		domain = []
		if not (name == '' and operator == 'ilike'):
			args += ['|', '|', ('name', 'ilike', name), ('asociado_id.name', 'ilike', name),
					('operador_id.name', 'ilike', name)]

		result = self.search(domain + args, limit=limit)
		res = result.name_get()

		return res


	@api.onchange('es_flotilla')
	def _onchange_es_flotilla(self):
		if self.es_flotilla == True:
			if self.es_utilitario == True:
				self.es_flotilla = False
				res = {'warning': {'title': _('Advertencia'), 'message': _(
					'No puede seleccionar que el vehiculo es flotilla, si ya esta seleccionado como utilitario')}}

				return res


	@api.onchange('es_utilitario')
	def _onchange_es_utilitario(self):
		if self.es_utilitario == True:
			if self.es_flotilla == True:
				self.es_utilitario = False
				res = {'warning': {'title': _('Advertencia'), 'message': _(
					'No puede seleccionar que el vehiculo es utilitario, si ya esta seleccionado como flotilla')}}

				return res


	@api.model
	def create(self, vals):
		placas = ""
		placas = vals['license_plate']

		placas = placas.strip()
		placas = placas.replace(" ", "")
		placas = placas.replace("-", "")
		placas = placas.replace("_", "")
		placas = placas.replace(".", "")
		placas = placas.replace("/", "")

		obj_placs = self.env['fleet.vehicle'].search([('license_plate', '=ilike', placas)])

		if len(obj_placs) > 0:
			raise UserError(_('Aviso !\nEl número de placas no se puede repetir.'))

		if vals['es_flotilla'] == True:

			if vals['no_economico'] == False:
				raise UserError(_('Aviso !\nSi selecciono la opcion de flotilla, necesita capturar el no. economico.'))

			if vals['asociado_id'] == False:
				raise UserError(_('Aviso !\nSi selecciono la opcion de flotilla, necesita seleccionar un asociado.'))

			obj_vehicle = self.env['fleet.vehicle'].search([('no_economico', '=ilike', vals['no_economico'])])
			if len(obj_vehicle) > 0:
				raise UserError(_('Aviso !\nEl número de flotilla no se puede repetir.'))

		return super(trafitec_vehiculos, self).create(vals)


	@api.constrains('remolque_1_id', 'remolque_2_id', 'dolly_id')
	def validacion_general(self):
		context = self._context

		if context.get('validacion_general', True):

			if self.remolque_1_id and self.remolque_2_id:

				if self.remolque_1_id == self.remolque_2_id:
					raise UserWarning(_("Los remolques deben ser diferentes."))

				if not self.dolly_id:
					raise UserWarning(_("Debe especificar el dolly."))

			if self.remolque_1_id and self.dolly_id and not self.remolque_2_id:
				raise UserWarning(_("Debe especificar el remolque 2."))

			if self.dolly_id and (not self.remolque_1_id or not self.remolque_2_id):
				raise UserWarning(_("Debe especificar los remolques."))


	def write(self, vals):
		if 'es_flotilla' in vals:
			es_flotilla = vals['es_flotilla']
		else:
			es_flotilla = self.es_flotilla

		if 'no_economico' in vals:
			no_economico = vals['no_economico']
		else:
			no_economico = self.no_economico

		if 'asociado_id' in vals:
			asociado_id = vals['asociado_id']
		else:
			asociado_id = self.asociado_id.name

		if 'license_plate' in vals:
			placas = ""
			placas = vals['license_plate']
			placas = placas.strip()
			placas = placas.replace(" ", "")
			placas = placas.replace("-", "")
			placas = placas.replace("_", "")
			placas = placas.replace(".", "")
			placas = placas.replace("/", "")

			obj_placs = self.env['fleet.vehicle'].search([('license_plate', '=ilike', placas)])

			if len(obj_placs) > 0:
				raise UserError(_('Aviso !\nEl número de placas no se puede repetir.'))

		if es_flotilla == True:

			if no_economico == False:
				raise UserError(_('Aviso !\nSi selecciono la opcion de flotilla, necesita capturar el no. economico.'))

			if asociado_id == False:
				raise UserError(_('Aviso !\nSi selecciono la opcion de flotilla, necesita seleccionar un asociado.'))

			if 'no_economico' in vals:
				obj_vehicle = self.env['fleet.vehicle'].search([('no_economico', '=ilike', no_economico)])

				if len(obj_vehicle) > 0:
					raise UserError(_('Aviso !\nEl número de flotilla no se puede repetir.'))
					
		return super(trafitec_vehiculos, self).write(vals)

