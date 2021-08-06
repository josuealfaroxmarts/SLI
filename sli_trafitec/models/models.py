## -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError

import datetime

from . import amount_to_text

import xlsxwriter
import base64


class trafitec_municipios(models.Model):
	_name = 'trafitec.municipios'
	_description ='Municipios'

	name = fields.Char(string="Nombre completo")
	name_value = fields.Char(string="Nombre del municipio", required=True)
	estado = fields.Many2one("res.country.state", string='Estado', ondelete='restrict',
							domain="[('country_id','=',157)]", required=True)

	@api.onchange('pais')
	def _onchange_pais(self):
		if self.pais:
			return {'domain': {'estado': [('country_id', '=', self.pais.id)]}}

	@api.model
	def _devuelve_mexico(self):
		return self.env['res.country'].search([('code', '=', 'MX')])

	pais = fields.Many2one('res.country', string='Pais', ondelete='restrict', default=_devuelve_mexico, required=True)

	@api.model
	def create(self, vals):
		estado = self.env['res.country.state'].search([('id', '=', vals['estado'])])
		vals['name'] = str(vals['name_value']) + ', ' + str(estado.name)
		return super(trafitec_municipios, self).create(vals)

	def write(self, vals):
		if 'name_value' in vals:
			nom = vals['name_value']
		else:
			nom = self.name_value
		if 'estado' in vals:
			estado = self.env['res.country.state'].search([('id', '=', vals['estado'])])
			vals['name'] = str(nom) + ', ' + str(estado.name)
		else:
			vals['name'] = str(nom) + ', ' + str(self.estado.name)
		return super(trafitec_municipios, self).write(vals)


class trafitec_localidad(models.Model):
	_name = 'trafitec.localidad'
	_description ='Localidad'

	name = fields.Char(string="Nombre")
	name_value = fields.Char(string="Nombre de la Localidad", required=True)
	codigopostal = fields.Char(string="Codigo postal")
	municipio = fields.Many2one('trafitec.municipios', string='Municipio', required=True)
	comentarios = fields.Text(string="Comentarios")

	@api.model
	def create(self, vals):
		municipio_id = vals['municipio']
		municipio_obj = self.env['trafitec.municipios'].search([('id', '=', municipio_id)])
		vals['name'] = str(vals['name_value']) + ', ' + str(municipio_obj.name)
		return super(trafitec_localidad, self).create(vals)

	def write(self, vals):
		if 'name_value' in vals:
			nom = vals['name_value']
		else:
			nom = self.name_value
		if 'municipio' in vals:
			municipio_obj = self.env['trafitec.municipios'].search([('id', '=', vals['municipio'])])
			vals['name'] = nom + ', ' + str(municipio_obj.name)
		else:
			vals['name'] = nom + ', ' + self.municipio.name
		return super(trafitec_localidad, self).write(vals)


class trafitec_status_client(models.Model) :
	name = 'trafitec.status'
	status = fields.Char(string="Estatus", required=True)
	_description ='status'

class trafitec_ubicaciones(models.Model):
	_name = 'trafitec.ubicacion'
	_description ='ubicacion'
	# MODIFICACIONE RECIENTE ALTA DE UBICACIONES
	name = fields.Char(string="Nombre", required=True)
	calle = fields.Char(string="Calle", required=True)
	noexterior = fields.Char(string="No. Exterior", required=True)
	nointerior = fields.Char(string="No. Interior")
	localidad = fields.Many2one('l10n_mx_edi.res.locality', string='Localidad')
	colonia = fields.Char(string="Colonia", required=True)
	estado = fields.Char(string="Estado", required=True)
	codigo_postal = fields.Char(string="Codigo Postal", required=True)
	ciudad = fields.Char(string="Ciudad", required=True)
	cruce = fields.Char(string="Cruce")
	responsable = fields.Char(string="Responsable")
	coberturacelular = fields.Boolean(string="Cobertura de celular")
	latitud = fields.Float(string="Latitud")
	longitud = fields.Float(string="Longitud")
	cap_carga = fields.Float(string="Capacidad de carga")
	cap_descarga = fields.Float(string="Capacidad de descarga")
	bodega_prob = fields.Boolean(string="Es bodega problematica")
	tipo_ubicacion = fields.Selection([('almacen', 'Almacén'), ('puerto', 'Puerto')], string="Tipo de ubicacion")
	tipo_carga = fields.Selection([('carga', 'Carga'), ('descarga', 'Descarga'), ('carga/descarga', 'Carga/Descarga')],
									string="Tipo de carga")
	comentarios = fields.Text(string="Comentarios")
	cliente_ubicacion = fields.Many2one('res.partner', string="Cliente")
	responsable_id = fields.One2many('trafitec.responsable','responsable', string='id responsable' )
	#TODO HABLAR CON EL CONSULTOR LINEA 130
	#municipio = fields.Many2one(string='Municipio', store=True, related='localidad.zip_sat_code.township_sat_code')
	# FIN MODIFICACION RECIENTE ALTA DE UBICACIONES
	active = fields.Boolean(string="Activo", default=True)

	@api.constrains('name')
	def _check_constrains(self):
		if self.name:
			name_obj = self.env['trafitec.ubicacion'].search([('name', 'ilike', self.name)])
			if len(name_obj) > 1:
				raise UserError(_('Aviso !\nEl nombre de la ubicación no se puede repetir.'))


class trafitec_ubi_responsable(models.Model):
	_name = 'trafitec.responsable'
	_description ='Responsable'

	responsable = fields.Many2one('trafitec.ubicacion', string='Responsable')
	nombre_responsable = fields.Char(string="Nombre", required=True)
	email_responsable = fields.Char(string="Correo Electronico", required=True)
	telefono_responsable = fields.Char(string="Teléfono", required=True)



class trafitec_etiquetas(models.Model):
	_name = 'trafitec.etiquetas'
	_description ='etiquetas'
	name = fields.Char(string="Nombre", required=True)
	tipovalor = fields.Selection(
		[('Numerico', 'Numerico'), ('Texto', 'Texto'), ('Booleano', 'Booleano'), ('Entero', 'Entero')],
		string="Tipo de valor", required=True)


class trafitec_muelles(models.Model):
	_name = 'trafitec.muelles'
	_description ='muelles'
	name = fields.Char(string="Nombre", required=True)
	ubicacion = fields.Many2one('trafitec.ubicacion', string='Ubicación', required=True,
								domain="[('tipo_ubicacion','=','puerto')]")
	detalles = fields.Text(string="Detalles")


class trafitec_buques(models.Model):
	_name = 'trafitec.buques'
	_description ='buques'
	name = fields.Char(string="Nombre", required=True)
	detalles = fields.Text(string="Detalles")


class trafitec_tipodocumento(models.Model):
	_name = 'trafitec.tipodoc'
	_description ='tipo doc'
	name = fields.Char(string="Nombre", required=True)
	tipo = fields.Selection([('origen', 'Origen'), ('destino', 'Destino')], string="Tipo", required=True)
	evidencia = fields.Boolean(string="Para evidencia", default=False,
								help='Indica si el tipo de documento sera considerado como evidencia de viaje.')
	dmc = fields.Boolean(string="Para DMC", default=False,
							help='Indica si este tipo de documento es considerado como Documento Maestro del Cliente')
	detalles = fields.Text(string="Detalles", default="", help="")


class trafitec_tiposmovil(models.Model):
	_name = 'trafitec.moviles'
	_description ='tipo moviles'
	name = fields.Char(string="Nombre", required=True)
	tipomovil = fields.Selection([('vehiculo', 'Vehículo'), ('remolque', 'Remolque')], string="Tipo de móvil",
								required=True)
	tipo = fields.Selection([('full', 'Full'), ('sencillo', 'Sencillo')], string="Tipo", required=True)
	capacidad = fields.Float(string="Capacidad (Tons)", required=True, default=0)
	unidadmedida = fields.Many2one('uom.uom', string="Unidad de medida", readonly=True)
	lineanegocio = fields.Many2one(comodel_name='trafitec.lineanegocio', string='Linea de negocio')


class trafitec_lineanegocio(models.Model):
	_name = 'trafitec.lineanegocio'
	_description ='linea negocio'
	name = fields.Char(string="Nombre", required=True)
	porcentaje = fields.Float(string="Porcentaje de comisión", required=True)


class trafitec_tipopresentacion(models.Model):
	_name = 'trafitec.tipopresentacion'
	_description ='tipo presentacion'
	name = fields.Char(string="Nombre", required=True)


class trafitec_tipocargosadicionales(models.Model):
	_name = 'trafitec.tipocargosadicionales'
	_description ='tipo cargos adicionales'

	name = fields.Char(string="Nombre", required=True)
	product_id = fields.Many2one('product.product', string='Producto', required=True)
	validar_en_cr = fields.Boolean(string="Validar en CR",
									help='Validar este concepto en el contra recibo y carta porte (Obtiene los cargos adicionales del cada viaje del contrarecibo y verifica su existencia en los conceptos de la carta porte.).')

class trafitec_producttemplate(models.Model):
	_inherit = 'product.template'

	trafi_product_id = fields.One2many('trafitec.product', 'product_id')
	es_flete = fields.Boolean(string='Es flete', default=False,
							help='Indica si este producto sera considerado como flete para procesos del sistema.')


class trafitec_productetiqueta(models.Model):
	_name = 'trafitec.product'
	_description ='Etiqueta producto'

	product_id = fields.Many2one('product.template', string='Product')
	etiqueta_id = fields.Many2one('trafitec.tipopresentacion', string='Presentación')

	

class trafitec_asoc_rutas(models.Model):
	_name = 'trafitec.rutas'
	_description ='rutas'

	asociado = fields.Many2one('res.partner', string='Asociado')
	estado = fields.Many2one("res.country.state", string='Estado', domain="[('country_id','=',157)]", required=True)
	vigente = fields.Boolean(string='Vigente')


class trafitec_unidades(models.Model):
	_name = 'trafitec.unidades'
	_description ='unidades'
	asociado = fields.Many2one('res.partner', string='Asociado')
	movil = fields.Many2one('trafitec.moviles', string='Móvil', required=True)
	cantidad = fields.Integer(string='Cantidad', required=True)


class trafitec_unidadmedida(models.Model):
	_inherit = 'uom.uom'
	trafitec = fields.Boolean(string='Es unidad de medida para Trafitec')


class trafitec_vehiculos(models.Model):
	_inherit = 'fleet.vehicle'
	_order = 'id desc'

	color_vehicle = fields.Char(string='Color Vehiculo')
	ejes_tracktocamion = fields.Selection([('C2', 'C2'), ('C3', 'C3'), ('T3', 'T3'), ('S2', 'S2'), ('S3', 'S3') ,('S2-R4', 'S2-R4') ], string='Tipo de Eje')
	tiposervicio = fields.Selection([('Estatal', 'Estatal'), ('Federal', 'Federal')], string='Tipo de servicio')
	asociado_id = fields.Many2one('res.partner',
								domain="[('asociado','=',True),(['company','person'],'in','company_type')]",
								string="Asociado")
	operador_id = fields.Many2one('res.partner', domain="[('operador','=',True)]", string="Operador")
	es_flotilla = fields.Boolean(string='Es flotilla')
	no_economico = fields.Char(string='No. economico')
	es_utilitario = fields.Boolean(string='Es utilitario')

	remolque_1_id = fields.Many2one(string='Remolque 1', comodel_name='trafitec.remolques',
									help='Remolque 1 del vehículo.', domain=[('tipo', '=', 'remolque')])
	dolly_id = fields.Many2one(string='Dolly', comodel_name='trafitec.remolques', help='El dolly del vehículo.',
								domain=[('tipo', '=', 'dolly')])
	remolque_2_id = fields.Many2one(string='Remolque 2', comodel_name='trafitec.remolques',
									help='Remolque 2 del vehículo en caso de Doble (Full).',
									domain=[('tipo', '=', 'remolque')])

	#Cambios
	vehicle_model = fields.Char(string='Marca y modelo vehiculo')
	modelo = fields.Char(string='Marca y modelo')
	numero_economico = fields.Char(string='Número Economico')
	tipo_vehiculo = fields.Selection([("tractocamion", "Tractocamion"), ("remolque", "Remolque"), ("dolly", "Dolly")],string='Tipo de vehículo')
	nombre_circulacion = fields.Char(string='Nombre tarjeta de circulación', compute='change_name_vehicle_documents')
	ext_circulacion = fields.Char(string='Extension archivo ciculacion')
	circulacion = fields.Binary(string='Tarjeta de circulación')
	nombre_poliza_seguro = fields.Char(string='Nombre poliza del seguro', compute='change_name_vehicle_documents')
	ext_poliza_seguro = fields.Char(string='extension archivo Poliza del seguro')
	poliza_seguro = fields.Binary(string='Poliza del seguro')
	fecha_poliza = fields.Date(string='Fecha de poliza')
	fecha_poliza = fields.Date(string='Fecha de vigencia de poliza')
	nombre_fisio = fields.Char(string='Verificaciones fisiomecanicas', compute='change_name_vehicle_documents')
	fisio = fields.Binary(string='Verificaciones fisio-mecanicas')
	fisio_fecha = fields.Date(string='Fecha de vigencia de la poliza')
	nombre_ambientales = fields.Char(string='Nombre verificaciones ambientales', compute='change_name_vehicle_documents')
	ambientales = fields.Binary(string='Verificaciones ambientales')
	ambientales_fecha = fields.Char(string='Fecha de vigencia poliza', compute='change_name_vehicle_documents')
	model_id = fields.Many2one(required=False)

	def change_name_vehicle_documents(self):
		if self.license_plate :
			self.nombre_circulacion = "Comprobante domicilio de Tarjeta de circulación ({}).{}".format(self.license_plate, self.ext_circulacion)
			self.nombre_poliza_seguro = "Poliza del seguro ({}).{}".format(self.license_plate, self.ext_poliza_seguro)
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

			vehiculos = self.env['fleet.vehicle'].search([('license_plate', '=ilike', placas), ('id', '!=', self._origin.id)], limit=1)
		#self.info_alertas = ''
		#if vehiculos:
		#	self.info_alertas = 'Las placas {} ya existen.'.format(placas, self.id)
		except:
			_logger.error("**Error al validar las placas.")

	#info_alertas = fields.Char(string='Alerta', default='', help='Muestra mensaje de alertas.')
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


class trafitec_res_bank(models.Model):
	_inherit = 'res.bank'

	no_institucion = fields.Char(string='No. de institución', required=True)
	clave_institucion = fields.Char(string='Clave de la institución', required=True)
	exportar = fields.Boolean(string="Exportar")


class trafitec_plazas_banxico(models.Model):
	_name = 'trafitec.plazas.banxico'
	_description ='plazas banxico'
	name = fields.Char(string='Nombre', required=True)
	numero_plaza = fields.Char(string='Número de plaza', required=True)

	
	def _compute_display_name(self):
		self.display_name = '{} - {}'.format(self.name, self.numero_plaza)

	display_name = fields.Char(string='Nombres', compute='_compute_display_name')


class trafitec_concepto_anti(models.Model):
	_name = 'trafitec.concepto.anticipo'
	_description ='concepto anticipo'
	name = fields.Char(string='Concepto', required=True)
	requiere_orden = fields.Boolean(string='Requiere orden de carga')


class trafitec_cliente_documentos(models.Model):
	_name = 'trafitec.clientes.documentos'
	_description ='Documentos clientes'
	name = fields.Many2one('trafitec.tipodoc', string='Documento requerido', required=True)
	tipo_tipo = fields.Selection(string='Tipo', related='name.tipo')
	tipo_evidencia = fields.Boolean(string='Evidencia', related='name.evidencia')
	tipo_dmc = fields.Boolean(string='DMC', related='name.dmc')
	partner_id = fields.Many2one('res.partner')


class trafitec_parametros(models.Model):
	_name = 'trafitec.parametros'
	_description ='parametros'
	name = fields.Char(string='Nombre', default='', required=True)
	company_id = fields.Many2one('res.company', 'Compañia',
								default=lambda self: self.env['res.company']._company_default_get(
									'trafitec.parametros'), required=True)
	product = fields.Many2one('product.template', string='Producto', required=True)
	payment_term_id = fields.Many2one('account.payment.term', string='Forma de pago', required=True)

	iva = fields.Many2one('account.tax', string='Porcentaje de IVA', required=True)
	retencion = fields.Many2one('account.tax', string='Porcentaje de retencion', required=True)
	pronto_pago = fields.Float(string='Porcentaje pronto pago', required=True)
	journal_id_invoice = fields.Many2one('account.journal', string='Diario', required=True)
	account_id_invoice = fields.Many2one('account.account', string='Planes contable', required=True)
	product_invoice = fields.Many2one('product.product', string='Productos', required=True)

	# diario = vals.env['account.journal'].search([('name', '=', 'Proveedores Transportistas')])  # Diario.
	# plancontable = vals.env['account.account'].search([('name', '=', 'Proveedores Transportistas')])  # Plan contable.
	# configuracion_trafitec = vals.env['trafitec.parametros'].search(
	#	[('company_id', '=', vals.company_id.id)])  # Plan contable.
	cr_diario_id = fields.Many2one(comodel_name='account.journal', string='Diario contable', required=True)
	cr_plancontable_id = fields.Many2one(comodel_name='account.account', string='Plan contable', required=True)
	cr_moneda_id = fields.Many2one(comodel_name='res.currency', string='Moneda predeterminada',
								required=True)  # Moneda predeterminada para nuevo contra recibos.
	cr_lineanegocio_id = fields.Many2one(comodel_name='trafitec.lineanegocio', string='Línea negocio predeterminada',
										)  # Linea de negocio para nuevo contra recibos.

	# Notas de cargo.
	# nca_diario_pagos_id=fields.Many2one(string='Diario para pago automatico:',comodel_name='account.journal',required=True,domain="[('type','=','purchase')]")
	# nca_diario_cobros_id=fields.Many2one(string='Diario para cobro automatico:',comodel_name='account.journal',required=True,domain="[('type','=','sale')]")
	nca_diario_pagos_id = fields.Many2one(string='Diario para pago automatico:', comodel_name='account.journal',
											required=True)
	nca_diario_cobros_id = fields.Many2one(string='Diario para cobro automatico:', comodel_name='account.journal',
											required=True)
	metodo_pago_id = fields.Many2one('l10n_mx_edi.payment.method', 'Metodo de Pago', help='Metodo de Pago Requerido por el SAT',
									required=True)

	cot_producto_id = fields.Many2one(string="id Producto", comodel_name="product.product",
										help="Producto que se utilizara para crear las ordenes de venta a partir de la cotización de trafitec.")

	cot_envio_avance_pruebas_st = fields.Boolean(string='Pruebas', default=True,
												help='Indica el estado de pruebas para envio de avance de cotización.')
	cot_envio_avance_pruebas_correo = fields.Char(string='Correo', default='',
												help='Correo al que se enviara el avance de cotización de pruebas.')

	# ----------------------------------------------------
	# Producto para seguro de carga.
	# ----------------------------------------------------
	seguro_cargo_adicional_id = fields.Many2one(string="Tipo de cargo adicional",
												comodel_name="trafitec.tipocargosadicionales",
												help="El tipo de cargo adicional que se utilizara para el seguro de carga.")

	# ----------------------------------------------------
	# Descuentos.
	# ----------------------------------------------------
	descuento_combustible_externo_id = fields.Many2one(string='Combustible externo', comodel_name='product.product', help='Proveedor externo: Producto donde se obtendra el costo del combustible para los calculos.')
	descuento_combustible_interno_id = fields.Many2one(string='Combustible interno', comodel_name='product.product', help='Autoconsumo: Producto donde se obtendra el costo del combustible para los calculos.')
	descuento_combustible_proveedor_id = fields.Many2one(string='Proveedor', comodel_name="res.partner", help='Proveedor predeterminado para vales de combustible.')
	descuento_concepto_id = fields.Many2one(string='Concepto', comodel_name='trafitec.concepto.anticipo', help='Concepto predeterminado al generar descuento en el viaje.')
	descuento_combustible_pfactor = fields.Float(string='Porcentaje factor (%)', default=40, help='Porcentaje del flete para calculo de vale de combustible.')
	descuento_combustible_pcomision = fields.Float(string='Porcentaje de comisión (%)', default=1, help='Porcentaje de comisión.')

	@api.constrains('descuento_combustible_pfactor', 'descuento_combustible_pcomision')
	def validacion(self):
		if not (self.descuento_combustible_pfactor in range(0, 100)):
			raise UserError('El factor debe estar entre 0 100 %.')

		if not (self.descuento_combustible_pcomision in range(0, 100)):
			raise UserError('El porcentaje de comisión debe estar entre 0 100 %.')

	@api.model
	def create(self, vals):
		parametros_obj = self.env['trafitec.parametros'].search([('company_id', '=', vals['company_id'])])
		if (len(parametros_obj) > 0):
			raise UserError(_('Aviso !\nNo puede crear 2 parametros para la misma compañia'))
		return super(trafitec_parametros, self).create(vals)

	def write(self, vals):
		if 'company_id' in vals:
			raise UserError(_('Aviso !\nNo puede cambiar la compañia'))
		return super(trafitec_parametros, self).write(vals)


class trafitec_sucursal(models.Model):
	_name = 'trafitec.sucursal'
	_description ='sucursal'
	name = fields.Char(string='Nombre', required=True)
	active = fields.Boolean(string="Activo", default=True)

	_sql_constraints = [('name_uniq', 'unique(name)', 'El nombre no se puede repetir.')]


class trafitec_seguridad_perfil(models.Model):
	_name = 'trafitec.seguridad.perfiles'
	_description ='Perfiles seguridad'
	name = fields.Char(string='Nombre', default='', required=True)
	detalles = fields.Char(string='Detalles', default='')
	derechos = fields.One2many(string='Derechos', comodel_name='trafitec.seguridad.derechos.perfil',
								inverse_name='perfil')
	usuarios = fields.Many2many(string='Usuarios', comodel_name='res.users')
	state = fields.Boolean(string='Activo', default=True)


class trafitec_seguridad_derechos(models.Model):
	_name = 'trafitec.seguridad.derechos'
	_description ='Seguridad derechos'
	name = fields.Char(string='Nombre', required=True)
	detalles = fields.Char(string='Detalles', required=True)


class trafitec_seguridad_derechos_perfil(models.Model):
	_name = 'trafitec.seguridad.derechos.perfil'
	_description ='Seguridad derechos perfil'
	perfil = fields.Many2one(string='Perfil', comodel_name='trafitec.seguridad.perfiles')
	derecho = fields.Many2one(string='Derecho', comodel_name='trafitec.seguridad.derechos', required=True)
	permitir = fields.Boolean(string='Permitir', default=True)


# -------------------------------------------------------------------------------------------------------------------------------------------
# CANCELACION DE CUENTAS
# -------------------------------------------------------------------------------------------------------------------------------------------
class cancelacion_cuentas(models.Model):
	_name = 'trafitec.cancelacioncuentas'
	_description ='Cancelacion cuentas'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_order = 'id desc'

	@api.depends('facturas_proveedor_id.abono')
	def _total(self):
		total = 0
		for f in self.facturas_id:
			total += f.abono
		self.abonos = total

	name = fields.Char(string='Folio', default='')
	persona_id = fields.Many2one(string='Persona', comodel_name='res.partner', required=True,
									tracking=True, domain="[('supplier','=',True),('customer','=',True)]")

	referencia = fields.Text(string='Referencia', default='', required=True, tracking=True)
	detalles = fields.Text(string='Detalles', default='', required=True, tracking=True)
	fecha = fields.Date(string='Fecha', required=True, default=datetime.datetime.today(), tracking=True)
	moneda_id = fields.Many2one(string='Moneda', comodel_name='res.currency', required=True,
								tracking=True)
	total = fields.Monetary(string='Suma', currency_field='moneda_id', required=True, default=0,
							tracking=True)
	total_txt = fields.Char(string='Total en texto', default='')
	total_txt_ver = fields.Char(string='Cantidad con letra', related='total_txt')
	abonos = fields.Monetary(string='Total', currency_field='moneda_id', default=0, store=True, compute='_total')

	facturas_cliente_id = fields.One2many(string='Facturas cliente',
											comodel_name='trafitec.cancelacioncuentas.facturas.cliente',
											inverse_name='cancelacion_cuentas_id')
	facturas_proveedor_id = fields.One2many(string='Facturas proveedor',
											comodel_name='trafitec.cancelacioncuentas.facturas.proveedor',
											inverse_name='cancelacion_cuentas_id')
	facturas_relacion_id = fields.One2many(string='Relación', comodel_name='trafitec.cancelacioncuentas.relacion',
											inverse_name='cancelacion_cuentas_id')

	diario_pago_cliente = fields.Many2one(string='Diario de pago a cliente', comodel_name='account.journal',
											required=True, tracking=True)
	diario_pago_proveedor = fields.Many2one(string='Diario de pago a proveedor', comodel_name='account.journal',
											required=True, tracking=True)

	persona_cobranza = fields.Char(string='Persona de cobranza', required=True, tracking=True)

	estado = fields.Boolean(string='Activa', default=True, tracking=True)
	state = fields.Selection(string='Estado',
								selection=[('nuevo', 'Nuevo'), ('validado', 'Validado'), ('cancelado', 'Cancelado')],
								default='nuevo', tracking=True)

	@api.onchange('total', 'moneda_id')
	def _onchange_total(self):

		if self.total >= 0:
			if self.moneda_id:
				if self.moneda_id.name.upper() in ['MXN', 'MXP', 'PESOS', 'PESOS MEXICANOS']:
					self.total_txt = amount_to_text().amount_to_text_cheque(self.total).upper()
				else:
					self.total_txt = amount_to_text().amount_to_text(self.total).upper()
			else:
				self.total_txt = ''
		else:
			self.total_txt = ''

	# self.total_txt=amount_to_text().amount_to_text(self.total,False)

	@api.onchange('persona_id', 'moneda_id')
	def _onchange_persona_id(self):
		lista_clientes = []
		lista_proveedores = []
		self.facturas_cliente_id = []
		self.facturas_proveedor_id = []
		self.facturas_relacion_id = []

		if not self.persona_id or not self.moneda_id:
			return

		facturas_cliente = self.env['account.move'].search(
			[('partner_id', '=', self.persona_id.id), ('move_type', '=', 'out_invoice'), ('amount_residual', '>', 0),
				('state', '=', 'open'), ('currency_id', '=', self.moneda_id.id)], order='date asc')
		# facturas.sorted(key=lamnda r: r.)
		# facturas=self.env['account.move'].search([])
		print("***Facturas:" + str(facturas_cliente))
		for f in facturas_cliente:
			nuevo = {'factura_cliente_id': f.id, 'factura_cliente_total': f.amount_total,
						'factura_cliente_saldo': f.amount_residual, 'abono': f.amount_residual}
			lista_clientes.append(nuevo)
		self.facturas_cliente_id = lista_clientes

		facturas_proveedores = self.env['account.move'].search(
			[('partner_id', '=', self.persona_id.id), ('move_type', '=', 'in_invoice'), ('amount_residual', '>', 0),
				('state', '=', 'open'), ('currency_id', '=', self.moneda_id.id)], order='date asc')
		# facturas=self.env['account.move'].search([])
		print("***Facturas:" + str(facturas_proveedores))
		for f in facturas_proveedores:
			nuevo = {'factura_proveedor_id': f.id, 'factura_proveedor_total': f.amount_total,
						'factura_proveedor_saldo': f.amount_residual, 'abono': 0}
			lista_proveedores.append(nuevo)
		self.facturas_proveedor_id = lista_proveedores

	@api.model
	def create(self, vals):
		if 'company_id' in vals:
			vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
				'Trafitec.CancelacionCuentas') or _('Nuevo')
		else:
			vals['name'] = self.env['ir.sequence'].next_by_code('Trafitec.CancelacionCuentas') or _('Nuevo')

		if 'facturas_cliente_id' in vals:
			for f in vals['facturas_cliente_id']:
				total = f[2]['factura_cliente_total']
				saldo = f[2]['factura_cliente_saldo']

				print(">>> F: " + str(f[2]['factura_cliente_saldo']))

		nuevo = super(cancelacion_cuentas, self).create(vals)
		return nuevo

	def action_saldar(self):
		for m in self.facturas_proveedor_id:
			m.abono = m.factura_proveedor_saldo

	def action_ceros(self):
		self.facturas_relacion_id = None
		print(".....Relacion: " + str(self.facturas_relacion_id))

		for m in self.facturas_proveedor_id:
			m.abono = 0

	def action_distribuir(self):
		fc_saldo = 0
		fp_saldo = 0
		relacion = []
		error = False
		errores = ""

		print("***Facturas de clientes:" + str(self.facturas_cliente_id))
		print("***Facturas de proveedores:" + str(self.facturas_proveedor_id))

		if not self.facturas_proveedor_id:
			error = True
			errores += "No hay facturas de proveedor.\n"

		if not self.facturas_cliente_id:
			error = True
			errores += "No hay facturas de cliente.\n"

		if error:
			raise ValidationError(_(errores))

		# Relaciones.
		self.facturas_relacion_id = None

		# Quitar abonos.
		for fp in self.facturas_proveedor_id:
			fp.abono = 0

		# Distribuir.
		for fc in self.facturas_cliente_id:  # Facturas de cliente.
			fc_saldo = fc.factura_cliente_saldo
			print("---FC SALDO: " + str(fc_saldo))
			for fp in self.facturas_proveedor_id:  # Facturas de proveedor.
				fp_saldo = fp.factura_proveedor_id.amount_residual - fp.abono

				if fc_saldo <= 0:
					break
				if fp_saldo <= 0:
					continue

				if fc_saldo >= fp_saldo:
					fp.abono += fp_saldo
					fc_saldo -= fp_saldo
					rnueva = {'factura_cliente_id': fc.factura_cliente_id.id,
								'factura_proveedor_id': fp.factura_proveedor_id.id, 'abono': fp_saldo}
					relacion.append(rnueva)
				else:
					fp.abono += fc_saldo
					rnueva = {'factura_cliente_id': fc.factura_cliente_id.id,
								'factura_proveedor_id': fp.factura_proveedor_id.id, 'abono': fc_saldo}
					relacion.append(rnueva)
					fc_saldo = 0

		self.facturas_relacion_id = relacion

	@api.constrains('total')
	def validar(self):
		error = False
		errores = ""

		if self.total <= 0:
			error = True
			errores += "El total debe ser mayor a cero.\n"

		for f in self.facturas_cliente_id:
			if f.abono < 0:
				error = True
				errores += "El abono de las facturas cliente debe ser mayor o igual a cero ({}).\n".format(
					f.factura_cliente_id.name)
			if f.abono > f.factura_cliente_saldo:
				error = True
				errores += "El abono de las facturas cliente debe ser menor o igual al saldo de la factuta ({}).\n".format(
					f.factura_cliente_id.name)

		for f in self.facturas_proveedor_id:
			if f.abono < 0:
				error = True
				errores += "El abono de las facturas proveedor debe ser mayor o igual a cero ({}).\n".format(
					f.factura_proveedor_id.name)
			if f.abono > f.factura_proveedor_saldo:
				error = True
				errores += "El abono de las facturas proveedor debe ser menor o igual al saldo de la factuta ({}).\n".format(
					f.factura_proveedor_id.name)

		# if not self.facturas_relacion_id:
		#	error=True
		#	errores+="Debe haber relacion de pagos.\n"

		if error:
			raise ValidationError(_(errores))

	def _aplicapago(self, diario_id, factura_id, abono, moneda_id, persona_id, tipo='supplier', subtipo='inbound'):
		metodo = 2
		if subtipo == 'inbound':
			metodo = 1

		valores = {'journal_id': diario_id,  # Ok.
					'payment_method_id': metodo,  # account_payment_method 1=Manual inbound, 2=Manual outbound.
					'payment_date': datetime.datetime.now().date(),  # Ok.
					'communication': 'Pago por cancelación de cuentas {}.'.format(str(self.name)),  # Ok.
					'move_ids': [(4, factura_id, None)],  # [(4, inv.id, None) for inv in self._get_invoices()],
					'payment_type': subtipo,  # inbound,outbound
					'amount': abono,  # Ok.
					'currency_id': moneda_id,  # Ok.           s
					'partner_id': persona_id,  # Ok.
					'partner_type': tipo,  # Ok. customer,supplier
					}

		print("***Pago auto: " + str(valores))
		pago = self.env['account.payment'].create(valores)
		pago.post()
		return pago

	def action_validar(self):
		error = False
		errores = ""

		if not self.facturas_relacion_id:
			error = True
			errores += "Debe especificar la relacion de facturas y abonos.\n"

		totalabonos = 0
		for f in self.facturas_relacion_id:
			totalabonos += f.abono

		if totalabonos != self.total:
			error = True
			errores += "El total de los abonos debe ser igual al total del documento.\n"

		# default_credit_account_id   #Haber
		if not self.diario_pago_cliente.default_debit_account_id or not self.diario_pago_cliente.default_credit_account_id:  # Debe
			error = True
			errores += "El diario de pago a cliente no tiene cuentas contables configuradas.\n"

		if not self.diario_pago_proveedor.default_debit_account_id or not self.diario_pago_proveedor.default_credit_account_id:  # Debe
			error = True
			errores += "El diario de pago a proveedor no tiene cuentas contables configuradas.\n"

		for r in self.facturas_relacion_id:
			fc = r.factura_cliente_id
			fp = r.factura_proveedor_id
			abono = r.abono

			if not fc or not fp:
				continue

			if abono <= 0:
				continue

			fc_o = self.env['account.move'].search([('id', '=', fc.id)])
			fp_o = self.env['account.move'].search([('id', '=', fp.id)])

			if abono > fc_o.amount_residual:
				error = True
				errores += "El abono {} es mayor al saldo de la factura cliente {}/{}.\n".format(abono, fc.name,
																								fc.amount_residual)

			if abono > fp_o.amount_residual:
				error = True
				errores += "El abono {} es mayor al saldo de la factura proveedor {}/{}.\n".format(abono, fp.name,
																								fp.amount_residual)

		if error:
			raise ValidationError(_(errores))

		if self.state == 'nuevo':
			print("------Facturas relacion: " + str(self.facturas_relacion_id))
			for r in self.facturas_relacion_id:
				abono = r.abono
				print("---Abono:" + str(abono))
				if abono <= 0:
					continue

				print("---Factura cliente:" + str(r.factura_cliente_id))
				print("---Factura proveedor:" + str(r.factura_proveedor_id))

				# Aplicar pago para factura cliente.
				pago1 = None
				pago2 = None
				pago1 = self._aplicapago(self.diario_pago_cliente.id, r.factura_cliente_id.id, abono, self.moneda_id.id,
										self.persona_id.id, 'customer', 'inbound')

				# Aplicar pago para factura proveedor.
				pago2 = self._aplicapago(self.diario_pago_proveedor.id, r.factura_proveedor_id.id, abono,
										self.moneda_id.id, self.persona_id.id, 'supplier', 'outbound')
				print("Pago 1:" + str(pago1) + " Pago 2:" + str(pago2))
			self.state = 'validado'

	def action_cancelar(self):
		print("---selft.state" + str(self.state))
		if self.state == 'nuevo' or self.state == 'validado':
			self.state = 'cancelado'

	def unlink(self):
		if self.state == 'validado':
			raise ValidationError(_("El documento ya esta validado."))


class cancelacion_cuentas_facturas_proveedor(models.Model):
	_name = 'trafitec.cancelacioncuentas.facturas.proveedor'
	_description ='Cancelacion cuentas en facturas proveedor'
	cancelacion_cuentas_id = fields.Many2one(string='Cancelación de cuentas',
											comodel_name='trafitec.cancelacioncuentas')
	moneda_id = fields.Many2one(string='Moneda', comodel_name='res.currency')

	factura_proveedor_id = fields.Many2one(string='Factura proveedor', comodel_name='account.move')
	factura_proveedor_fecha = fields.Date(string='Fecha', related='factura_proveedor_id.date')
	factura_proveedor_total = fields.Monetary(string='Total', related='factura_proveedor_id.amount_total',
												currency_field='moneda_id')
	factura_proveedor_saldo = fields.Monetary(string='Saldo', related='factura_proveedor_id.amount_residual',
												currency_field='moneda_id')

	abono = fields.Monetary(string='Abono', default=0, currency_field='moneda_id')


class cancelacion_cuentas_facturas_cliente(models.Model):
	_name = 'trafitec.cancelacioncuentas.facturas.cliente'
	_description ='Cancelacion cuentas en facturas cliente'
	cancelacion_cuentas_id = fields.Many2one(string='Cancelación de cuentas',
											comodel_name='trafitec.cancelacioncuentas')
	moneda_id = fields.Many2one(string='Moneda', comodel_name='res.currency')

	factura_cliente_id = fields.Many2one(string='Factura cliente', comodel_name='account.move')
	factura_cliente_fecha = fields.Date(string='Fecha', related='factura_cliente_id.date')
	factura_cliente_total = fields.Monetary(string='Total', related='factura_cliente_id.amount_total',
											currency_field='moneda_id')
	factura_cliente_saldo = fields.Monetary(string='Saldo', related='factura_cliente_id.amount_residual',
											currency_field='moneda_id')

	abono = fields.Monetary(string='Abono', default=0, currency_field='moneda_id')


class cancelacion_cuentas_relacion(models.Model):
	_name = 'trafitec.cancelacioncuentas.relacion'
	_description ='Cancelacion cuentas relacion'
	cancelacion_cuentas_id = fields.Many2one(string='Cancelación de cuentas',
											comodel_name='trafitec.cancelacioncuentas')
	factura_cliente_id = fields.Many2one(string='Factura cliente', comodel_name='account.move')
	factura_proveedor_id = fields.Many2one(string='Factura proveedor', comodel_name='account.move')
	moneda_id = fields.Many2one(string='Moneda', comodel_name='res.currency')
	abono = fields.Monetary(string='Abono', currency_field='moneda_id')


# -------------------------------------------------------------------------------------------------------------------------------------------
# Pagos masivos.
# -------------------------------------------------------------------------------------------------------------------------------------------
class trafitec_pagosmasivos(models.Model):
	_name = 'trafitec.pagosmasivos'
	_description ='Pagos masivos'
	_order = 'id desc'
	_inherit = ['mail.thread', 'mail.activity.mixin']

	name = fields.Char(string='Folio', default='')
	persona_id = fields.Many2one(string='Persona', comodel_name='res.partner', required=True,
								domain="[(['company','person'],'in','company_type'),'|',('supplier','=',True),('customer','=',True)]",
								tracking=True)
	fecha = fields.Date(string='Fecha', default=datetime.datetime.now().today(), required=True,
						tracking=True)

	moneda_id = fields.Many2one(string='Moneda', comodel_name='res.currency', required=True,
								tracking=True)

	total = fields.Monetary(string='Total', default=0, currency_field='moneda_id', required=True,
							tracking=True)
	total_txt = fields.Char(string='Total texto cantidad', default='')
	total_txt_ver = fields.Char(string='Total texto', related='total_txt', default='')

	facturas_id = fields.One2many(string='Facturas', comodel_name='trafitec.pagosmasivos.facturas',
								inverse_name='pagomasivo_id')
	referencia = fields.Char(string='Referenccia', default='', required=True, tracking=True)
	detalles = fields.Char(string='Detalles', default='', tracking=True)
	diario_id = fields.Many2one(string='Diario', comodel_name='account.journal', required=True)
	tipo = fields.Selection(string='Tipo',
							selection=[('noespecificado', '(No especificado)'), ('proveedor', 'Proveedor'),
										('cliente', 'Cliente')], default='noespecificado', required=True,
							tracking=True)
	state = fields.Selection(string='Estado',
								selection=[('nuevo', 'Nuevo'), ('validado', 'Validado'), ('aplicado', 'Aplicado'),
										('cancelado', 'Cancelado')], default='nuevo', required=True,
							tracking=True)

	busqueda_fecha_inicial = fields.Date(string='Búsqueda: Fecha inicial', default=datetime.datetime.now().today(),
										required=True)
	busqueda_fecha_final = fields.Date(string='Búsqueda: Fecha final', default=datetime.datetime.now().today(),
										required=True)

	# context="{'form_view_ref': 'account.view_account_payment_from_invoices', 'move_ids' : facturas_id}"
	def LlamarABatch(self):
		losids = []
		lasfids = []
		print("****LAS FACTURAS*****")
		for f in self.facturas_id:
			if f.factura_id.amount_residual > 0:
				losids.append(f.factura_id.id)
				lasfids.append({'id': f.factura_id.id, 'receiving_amt': 1.1})

		# print("Id: "+str(f.factura_id.id)+" Folio: "+str(f.factura_id.name)+" amount_residual: "+str(f.factura_id.amount_residual))

		return {'name': 'Pagos masivos X', 'type': 'ir.actions.act_window', 'type': 'ir.actions.act_window',
				'res_model': 'account.register.payments',  # 'res_model': 'trafitec.programacionpagos',
				'view_type': 'form', 'view_mode': 'form', 'form_view_ref': 'action_invoice_invoice_batch_process',
				# 'form_view_ref': 'account.view_account_payment_from_invoices',
				'target': 'new', 'multi': True,
				'context': {'move_ids': lasfids, 'active_ids': losids, 'active_model': 'account.move', 'batch': True,
							'programacionpagosx': True}}

	def EjecutaAbonar(self):
		facturas = self.env['account.move'].search([('id', '=', 329)])
		print("----------------Facturas------------------")
		print(facturas)
		print("----------------Pagos---------------------")
		print(facturas[0].payment_move_line_ids)

		self.Abonar(self.total)

	def Abonar(self, total):
		return
		print("-----Abono:" + str(total))

		# --------------------------------------------------
		# Generar pago.
		# --------------------------------------------------
		pago_id = self.env['account.payment'].create(
			{'partner_id': self.persona_id.id, 'amount': total, 'payment_method_id': 1, 'journal_id': self.diario_id.id,
				'payment_type': 'inbound', 'partner_type': 'customer'})
		print("*****Despues del pago..")

		# --------------------------------------------------
		# Crear asientos contables del pago y factura.
		# --------------------------------------------------
		lista = []

		linea = {'account_id': 3, 'name': 'Pago cliente.', 'date': datetime.datetime.today(),
				'partner_id': self.persona_id.id, 'credit': float(total), 'debit': 0.0}

		linea2 = {'account_id': 3, 'name': 'Pago factura.', 'date': datetime.datetime.today(),
				'partner_id': self.persona_id.id, 'credit': 0.00, 'debit': float(total)}

		lista.append(linea)
		lista.append(linea2)

		line_list = [(0, 0, x) for x in lista]
		move_id = self.env['account.move'].create(
			{'partner_id': self.persona_id.id, 'date': datetime.datetime.today(), 'journal_id': self.diario_id.id,
			'line_ids': line_list})

		print("*****Despues del movimiento")
		# --------------------------------------------------
		# Crear lineas de movimientos.
		# --------------------------------------------------
		for f in self.facturas_id:
			cantidad = f.abono
			# Pago de cliente.
			valor = {'move_id': move_id.id, 'account_id': f.factura_id.account_id.id, 'partner_id': self.persona_id.id,
					'journal_id': self.diario_id.id, 'user_type_id': 2, 'move_id': f.factura_id.id,
					'ref': '' + str(f.factura_id.name), 'name': '' + str(f.factura_id.name), 'credit': total,
					'debit': 0, 'payment_id': pago_id.id}
			print("*****Valor1:")
			print(valor)
			credit_line = self.env['account.move.line'].with_context(check_move_validity=False).create(valor)

			# Factura.
			valor = {'move_id': move_id.id, 'account_id': self.diario_id.default_debit_account_id.id,
					'partner_id': self.persona_id.id, 'journal_id': self.diario_id.id, 'user_type_id': 3,
					'move_id': f.factura_id.id, 'ref': '' + str(f.factura_id.name),
					'name': '' + str(f.factura_id.name), 'credit': 0, 'debit': total, 'payment_id': pago_id.id}
			print("*****Valor2:")
			print(valor)
			debit_line = self.env['account.move.line'].with_context(check_move_validity=False).create(valor)

			# Registra el abono.
			# TODO ABONO PAGO MASIVO
			abono_credito = {'credit_move_id': credit_line.id, 'full_reconcile_id': False, 'amount': cantidad,
							'debit_move_id': debit_line.id, 'amount_currency': 0}
			conciliacion = self.env['account.partial.reconcile'].create(abono_credito)

		move_id.post()
		# pago_id.post()
		print("-----Final:" + str(total))

	@api.model
	def create(self, vals):
		# self.Abonar(500)

		if 'company_id' in vals:
			vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
				'Trafitec.PagosMasivos') or _('Nuevo')
		else:
			vals['name'] = self.env['ir.sequence'].next_by_code('Trafitec.PagosMasivos') or _('Nuevo')
		return super(trafitec_pagosmasivos, self).create(vals)

	def _aplicapago(self, diario_id, factura_id, abono, moneda_id, persona_id, tipo='supplier', subtipo='inbound'):
		# factura = self.env['account.move'].search([('id', '=', self.id)])
		if abono <= 0:
			return

		metodo = 2
		if subtipo == 'inbound':
			metodo = 1

		valores = {'journal_id': diario_id,  # Ok.
					'payment_method_id': metodo,  # account_payment_method 1=Manual inbound, 2=Manual outbound.
					'payment_date': datetime.datetime.now().date(),  # Ok.
					'communication': 'Pago desde codigo por:{} de tipo:{} desde Pago masivo {}.'.format(str(abono), tipo,
																										self.name),
					# Ok.
					'move_ids': [(4, factura_id, None)],  # [(4, inv.id, None) for inv in self._get_invoices()],
					'payment_type': subtipo,  # inbound,outbound
					'amount': abono,  # Ok.
					'currency_id': moneda_id,  # Ok.           s
					'partner_id': persona_id,  # Ok.
					'partner_type': tipo,  # Ok. customer,supplier
					}

		# print("***Pago auto: "+str(valores))
		pago = self.env['account.payment'].create(valores)
		pago.post()

	def _aplicapago2(self, diario_id, abono, moneda_id, persona_id, tipo='supplier', subtipo='inbound'):
		# factura = self.env['account.move'].search([('id', '=', self.id)])
		if abono <= 0:
			return

		metodo = 2
		if subtipo == 'inbound':
			metodo = 1

		valores = {'journal_id': diario_id,  # Ok.
					'payment_method_id': metodo,  # account_payment_method 1=Manual inbound, 2=Manual outbound.
					'payment_date': datetime.datetime.now().date(),  # Ok.
					'communication': '',
					# 'Pago desde codigo por:{} de tipo:{} desde Pago masivo {}.'.format(str(abono),self.name), # Ok.
					'move_ids': [], 'payment_type': subtipo,  # inbound,outbound
					'amount': abono,  # Ok.
					'currency_id': moneda_id,  # Ok.           s
					'partner_id': persona_id,  # Ok.
					'partner_type': tipo,  # Ok. customer,supplier
					}

		# print("***Pago auto: "+str(valores))
		pago = self.env['account.payment'].create(valores)
		return pago.post()

	def action_validar(self):
		self.write({'state': 'validado'})
		return
		error = False
		errores = ""
		total_abonos = 0

		# VALIDACIONES
		if self.total <= 0:
			error = True
			errores += "El total debe ser mayor a cero.\n"

		if self.referencia.strip() == "":
			error = True
			errores += "Debe especificar la referencia.\n"

		for f in self.facturas_id:
			if f.abono == 0:
				continue

			if f.abono < 0:
				error = True
				errores += "El abono de la factura {} debe ser mayor o igual a cero.\n".format(f.factura_id.name)

			if f.abono > f.factura_saldo:
				error = True
				errores += "Los abonos deben ser menores o iguales al saldo de la factura {}.".format(
					f.factura_id.name)

			total_abonos = total_abonos + f.abono

		if total_abonos <= 0:
			error = True
			errores += "El total de abonos debe ser mayor a cero.\n"

		if total_abonos != self.total:
			error = True
			errores += "El total de abonos debe ser igual al total general.\n"

		if error:
			raise UserError(_("Alerta..\n" + errores))

		# REALIZAR TAREA
		tipo = ""
		tipo_persona = ""

		if self.tipo == 'noespecificado':
			return

		if self.tipo == 'proveedor':
			tipo = "in_invoice"
			tipo_persona = "supplier"

		if self.tipo == 'cliente':
			tipo = "out_invoice"
			tipo_persona = "customer"

		# for f in self.facturas_id:
		#	self._aplicapago2(self.diario_id.id, self.total, self.moneda_id.id, self.persona_id.id, tipo_persona)
		self._aplicapago2(self.diario_id.id, self.total, self.moneda_id.id, self.persona_id.id, tipo_persona)

		self.write({'state': 'validado'})

	def action_cancelar(self):
		self.write({'state': 'cancelado'})

	def action_distribuir(self):
		disponible = self.total
		for f in self.facturas_id:
			f.abono = 0

		for f in self.facturas_id:
			if disponible > 0:
				if disponible >= f.factura_saldo:
					f.abono = f.factura_saldo
					disponible = disponible - f.abono
				else:
					f.abono = disponible
					disponible = 0
					break

	def action_cero(self):
		for f in self.facturas_id:
			f.abono = 0

	def action_saldar(self):
		for f in self.facturas_id:
			f.abono = f.factura_saldo

	@api.onchange('persona_id', 'moneda_id', 'tipo', 'busqueda_fecha_inicial', 'busqueda_fecha_final')
	def _onchange_persona_id(self):
		self.CargaFacturas()

	def CargaFacturas(self):
		lista_clientes = []
		self.facturas_id = []
		tipo = ""

		if not self.persona_id or not self.moneda_id:
			return

		if self.tipo == 'noespecificado':
			return

		if self.tipo == 'proveedor':
			tipo = "in_invoice"

		if self.tipo == 'cliente':
			tipo = "out_invoice"

		print("----------------------TIPO: " + tipo)

		facturas_cliente = self.env['account.move'].search(
			[('partner_id', '=', self.persona_id.id), ('move_type', '=', tipo), ('amount_residual', '>', 0), ('state', '=', 'open'),
			('currency_id', '=', self.moneda_id.id), ('date', '>=', self.busqueda_fecha_inicial),
			('date', '<=', self.busqueda_fecha_final)], order='date asc')
		print("**Facturas cliente:" + str(facturas_cliente))
		for f in facturas_cliente:
			nuevo = {'pagomasivo_id': False, 'moneda_id': f.currency_id.id, 'factura_id': f.id,
					'factura_fecha': f.date, 'factura_total': f.amount_total, 'factura_saldo': f.amount_residual,
					'abono': 0}
			print("**Nuevo:" + str(nuevo))
			lista_clientes.append(nuevo)
		print("**Lista de documentos:" + str(lista_clientes))
		self.facturas_id = lista_clientes


class trafitec_pagosmasivos_facturas(models.Model):
	_name = 'trafitec.pagosmasivos.facturas'
	_description ='Facturas pagos masivos'
	pagomasivo_id = fields.Many2one(string='Pago masivo', comodel_name='trafitec.pagosmasivos')
	moneda_id = fields.Many2one(string='Moneda', comodel_name='res.currency', required=True)
	factura_id = fields.Many2one(string='Factura', comodel_name='account.move', required=True)
	factura_fecha = fields.Date(string='Fecha', related='factura_id.date', store=True)
	factura_total = fields.Monetary(string='Total', related='factura_id.amount_total', default=0, store=True,
									currency_field='moneda_id')
	factura_saldo = fields.Monetary(string='Saldo', related='factura_id.amount_residual', default=0, store=True,
									currency_field='moneda_id')
	abono = fields.Monetary(string='Abono', required=True, default=0, currency_field='moneda_id')


# -------------------------------------------------------------------------------------------------------------------------------------------
# Evidencias de viaje.
# -------------------------------------------------------------------------------------------------------------------------------------------
class trafitec_viajes_scan(models.Model):
	_name = 'trafitec.viajes.scan'
	_description ='viajes scan'
	viaje_id = fields.Many2one(string='Viaje', comodel_name='trafitec.viajes', required=True)
	st = fields.Selection([('not_started', 'No iniciado'), ('started', 'Iniciado')],string='Estado')


# -------------------------------------------------------------------------------------------------------------------------------------------
# Clasificaciones
# -------------------------------------------------------------------------------------------------------------------------------------------
class trafitec_clasificacionesg(models.Model):
	_name = 'trafitec.clasificacionesg'
	_description ='clasicaciones sg'
	name = fields.Char(string='Nombre', default='', required=True)
	aplica_viajes = fields.Boolean(string='Aplica a calificar viaje', default=False)
	aplica_crm_trafico_rechazo = fields.Boolean(string='Aplica a CRM Tráfico en rechazo', default=False)
	aplica_clasificacion_bloqueo_cliente = fields.Boolean(string='Aplica clasificación de bloqueo de cliente', default=False)
	considerar = fields.Selection(string="Considerar",
								selection=[('noespecificado', 'No especificado'), ('malo', 'Malo'),
											('bueno', 'Bueno')], default='malo', required=True)
	state = fields.Selection(string='Estado', selection=[('inactivo', 'Inactivo'), ('activo', 'Activo')], required=True,
							default='activo')


# -------------------------------------------------------------------------------------------------------------------------------------------
# Clasificaciones x viaje
# -------------------------------------------------------------------------------------------------------------------------------------------
class trafitec_clasificacionesgxviaje(models.Model):
	_name = 'trafitec.clasificacionesgxviaje'
	_description ='clasificaciones sgxviaje'
	viaje_id = fields.Many2one(string='Viaje', comodel_name='trafitec.viajes')
	clasificacion_id = fields.Many2one(string='Calificación', comodel_name='trafitec.clasificacionesg', required=True)
	operador_nombre = fields.Char(string='Operador', related='viaje_id.operador_id.display_name', store=True)
	asociado_nombre = fields.Char(string='Asociado', related='viaje_id.asociado_id.display_name', store=True)
	considerar = fields.Selection(string='Considerado como', related='clasificacion_id.considerar', store=True)

	_sql_constraints = [('viaje_clasificacion_uniq', 'unique(viaje_id, clasificacion_id)',
						'La calificación debe ser unica en el viaje.')]


# -------------------------------------------------------------------------------------------------------------------------------------------
# Presupuestos
# -------------------------------------------------------------------------------------------------------------------------------------------
class trafitec_presupuestos(models.Model):
	_name = 'trafitec.presupuestos'
	_description ='presupuestos'
	ano = fields.Integer(string='Año', default=2018)
	# mes = fields.Selection(string='Mes', selection=[(1, 'Enero'), (2,'Febrero'), (3,'Marzo'), (4, 'Abril'),(5, 'Mayo'), (6, 'Junio'), (7, 'Julio'),(8,'Agosto'),(9,'Septiembre'),(10,'Octubre'),(11,'Noviembre'),(12,'Diciembre')])
	monto_mes1 = fields.Float(string='Enero', default=0)
	monto_mes2 = fields.Float(string='Febrero', default=0)
	monto_mes3 = fields.Float(string='Marzo', default=0)
	monto_mes4 = fields.Float(string='Abril', default=0)
	monto_mes5 = fields.Float(string='Mayo', default=0)
	monto_mes6 = fields.Float(string='Junio', default=0)
	monto_mes7 = fields.Float(string='Julio', default=0)
	monto_mes8 = fields.Float(string='Agosto', default=0)
	monto_mes9 = fields.Float(string='Septiembre', default=0)
	monto_mes10 = fields.Float(string='Octubre', default=0)
	monto_mes11 = fields.Float(string='Noviembre', default=0)
	monto_mes12 = fields.Float(string='Diciembre', default=0)
	st = fields.Selection([('inactive', 'Inactivo'), ('active', 'Activo')],string='Estado', default='active')


class CustomPopMessage(models.TransientModel):
	_name = 'custom.pop.message'
	_description ='Custom pop message'
	name = fields.Char('Mensaje', readonly=True)


class TrafitecParametros(models.TransientModel):
	_name = 'trafitec.reportes.parametros'
	_description ='Parametros'
	fecha_inicial = fields.Date(string="Fecha incial")
	fecha_final = fields.Date(string="Fecha final")
	archivo_nombre = fields.Char(string="Nombre del archivo")
	archivo_archivo = fields.Binary(string="Archivo")

	@api.model
	def render_html2(self, docids, data=None):
		print("-------------------RENDER HTML--------------------")
		# docargs = {'doc_ids': self.ids, 'doc_model': self.model, 'data': data, }
		docargs = {}
		return self.env['report'].render('SLI_TrafitecReportesX.report_viaje_general', docargs)

	@api.model
	def render_html3(self, docids, data=None):
		report_obj = self.env['report']
		report = report_obj._get_report_from_name('report_viaje_general')
		docids == [150, 151, 148]
		print("----------REPORT----------")
		print(report)
		docargs = {'doc_ids': docids, 'doc_model': report.model, 'docs': self, }
		return report_obj.render('SLI_TrafitecReportesX.report_viaje_general', docargs)

	@api.model
	def render_html4(self, docids, data=None):
		report_obj = self.env['report']
		report = report_obj._get_report_from_name('SLI_TrafitecReportesX.report_viaje_general')

		docs = self.env['trafitec.viajes'].browse([151, 150])
		docargs = {'doc_ids': [151, 150], 'doc_model': report.model, 'docs': docs}
		return self.env['report'].render('SLI_TrafitecReportesX.report_viaje_general', docargs)

	def render_html(self):
		context = None
		ids = [1, 2, 3]
		if ids:
			if not isinstance(ids, list):
				ids = [ids]
			context = dict(context or {}, active_ids=ids, active_model=self._name,
							data={'fecha_inicial': self.fecha_inicial, 'fecha_final': self.fecha_final})
		return {'type': 'ir.actions.report.xml', 'report_name': 'SLI_TrafitecReportesX.report_viaje_general',
				'context': context, }

	def export_xls(self):
		file_name = 'temp'
		workbook = xlsxwriter.Workbook(file_name, {'in_memory': True})
		worksheet = workbook.add_worksheet()
		row = 0
		col = 0
		header = []

		for e in header:
			worksheet.write(row, col, e)
			col += 1
		row += 1
		for vals in self.carrier_line_ids:
			worksheet.write(row, 0, vals.ref)
		workbook.close()
		with open(file_name, "rb") as file:
			file_base64 = base64.b64encode(file.read())
		self.archivo_nombre = self.name + '.xlsx'
		self.write({'archivo_archivo': file_base64, })


class SalespersonWizard(models.TransientModel):
	_name = "salesperson.wizard"
	_description = "Salesperson Wizard"

	def check_report(self):
		data = {}
		data['form'] = self.read(['salesperson_id', 'date_from', 'date_to'])[0]
		return self._print_report(data)

	def _print_report(self, data):
		data['form'].update(self.read(['salesperson_id', 'date_from', 'date_to'])[0])
		return self.env['report'].get_action(self, 'sales_report.report_salesperson', data=data)

	@api.model
	def render_html(self, docids, data=None):
		self.model = self.env.context.get('active_model')

		docs = self.env[self.model].browse(self.env.context.get('active_id'))
		sales_records = []
		orders = self.env['sale.order'].search([('user_id', '=', docs.salesperson_id.id)])
		if docs.date_from and docs.date_to:
			for order in orders:
				if int(docs.date_from) <= int(order.date_order) and int(docs.date_to) >= int(order.date_order):
					sales_records.append(order)
				else:
					raise UserError("Please enter duration")

		docargs = {'doc_ids': self.ids, 'doc_model': self.model, 'docs': docs, 'time': time, 'orders': sales_records}
		return self.env['report'].render('sales_report.report_salesperson', docargs)


class CrmReport(models.TransientModel):
	_name = 'crm.won.lost.report'
	_description ='crm won lost report'
	sales_person = fields.Many2one('res.users', string="Sales Person")
	start_date = fields.Date('Start Date')
	end_date = fields.Date('End Date', default=fields.Date.today)

	def print_xls_report(self):
		workbook = xlsxwriter.Workbook('hello_world.xlsx')
		worksheet = workbook.add_worksheet()
		worksheet.write('A1', 'Hello world')
		workbook.close()

	def export(self):
		file_name = 'temp'
		workbook = xlsxwriter.Workbook(file_name, {'in_memory': True})
		worksheet = workbook.add_worksheet()
		row = 0
		col = 0
		header = []
		for e in header:
			worksheet.write(row, col, e)
			col += 1
		row += 1
		for vals in self.carrier_line_ids:
			worksheet.write(row, 0, vals.ref)
		workbook.close()
		with open(file_name, "rb") as file:
			file_base64 = base64.b64encode(file.read())
		self.carrier_xlsx_document_name = self.name + '.xlsx'
		self.write({'carrier_xlsx_document': file_base64, })

class TrafitecReportesGeneralesPedidosAvance(models.Model):
	_name = 'trafitec.reportes.generales.pedidos.avance.buscar'
	_description ='Reportes generales pedidos avance buscar'
	name = fields.Char(string='Nombre', required=True, help='Nombre')
	buscar_tipo = fields.Selection(string='Tipo de busqueda', selection=[('general','General'),('detalles','Detalles')])
	buscar_cliente = fields.Char(string='Cliente', default='', help='Cliente de cotizacion.')
	buscar_folio = fields.Char(string='Folio', default='', help='Folio de cotizacion.')
	buscar_usuario = fields.Char(string='Usuario', default='', help='Usuario.')
	buscar_origen = fields.Char(string='Origen', default='')
	buscar_destino = fields.Char(string='Destino', default='')
	buscar_fecha_inicial = fields.Date(string='Fecha inicial', default=datetime.datetime.today(), required=True, help='Fecha inicial de los viajes.')
	buscar_fecha_final = fields.Date(string='Fecha final', default=datetime.datetime.today(), required=True, help='Fecha final de los viajes.')

	porcentaje_general = fields.Float(string='Porcentaje general', default=0)
	porcentaje_detalles = fields.Float(string='Porcentaje detalles', default=0)

	resultados_id = fields.One2many(string='Resultado', comodel_name='trafitec.reportes.generales.pedidos.avance.resultado', inverse_name='buscar_id')
	detalles_id = fields.One2many(string='Detalles', comodel_name='trafitec.reportes.generales.pedidos.avance.detalles', inverse_name='buscar_id')
	detalles_xmes_id = fields.One2many(string='Por mes', comodel_name='trafitec.reportes.generales.pedidos.avance.xmes', inverse_name='buscar_id')
	detalles_xdia_id = fields.One2many(string='Por dia', comodel_name='trafitec.reportes.generales.pedidos.avance.xdia', inverse_name='buscar_id')

	def general(self):
		general = []
		condicion = ""
		condicion_viaje = ""

		#condicion += " and ct.fecha>='"+self.buscar_fecha_inicial+"' and ct.fecha<='"+self.buscar_fecha_final+"' "
		if self.buscar_folio:
			condicion += " and ct.name ilike '%{}%' ".format(self.buscar_folio or '')

		if self.buscar_cliente:
			condicion += " and cli.name ilike '%{}%' ".format(self.buscar_cliente or '')

		if self.buscar_usuario:
			condicion_viaje += " and usu.login ilike '%{}%' ".format(self.buscar_usuario or '')

		sql = """
select
ct.id as id,
ct.name as folio,
ct.fecha as fecha,
cli.name as cliente,
coalesce((
select sum(v.peso_origen_total/1000)
from trafitec_viajes as v
inner join trafitec_cotizaciones_linea_origen as lo on(v.subpedido_id =lo.id)
inner join trafitec_cotizaciones_linea l on(lo.linea_id =l.id )
inner join res_users as usu on(v.create_uid =usu.id)
where v.state = 'Nueva' and l.cotizacion_id = ct.id and v.create_date >= '{0}' and v.create_date <= '{1}' {3}
),0) 
as actual,
coalesce((
select count(v.peso_origen_total)
from trafitec_viajes as v
inner join trafitec_cotizaciones_linea_origen as lo on(v.subpedido_id =lo.id)
inner join trafitec_cotizaciones_linea l on(lo.linea_id =l.id )
inner join res_users as usu on(v.create_uid =usu.id)
where v.state = 'Nueva' and l.cotizacion_id = ct.id and v.create_date >= '{0}' and v.create_date <= '{1}' {3}
),0) 
as viajes,
coalesce((
select sum(l.cantidad)
from trafitec_cotizaciones_linea_origen as lo 
inner join trafitec_cotizaciones_linea l on(lo.linea_id =l.id )
where l.cotizacion_id = ct.id
),0) 
as total,
0 as porcentaje,
ct.state as estado
from trafitec_cotizacion as ct
inner join res_partner as cli on(ct.cliente=cli.id)
where ct.state in('Disponible','EnEspera') {2}
""".format(self.buscar_fecha_inicial, self.buscar_fecha_final, condicion, condicion_viaje)
		self.env.cr.execute(sql)
		general = self.env.cr.dictfetchall()
		return general

	def detalles(self):
		detalles = []
		condicion = ""
		condicion_viaje = ""

		if self.buscar_folio:
			condicion += " and c.name ilike '%{}%' ".format(self.buscar_folio or '')
		if self.buscar_cliente:
			condicion += " and cli.name ilike '%{}%' ".format(self.buscar_cliente or '')
		if self.buscar_usuario:
			condicion_viaje += " and usu.login ilike '%{}%' ".format(self.buscar_usuario or '')


		sql = """
select
c.name cotizacion_folio,
l.id subpedido,
max(cli.name) cliente,
max(muno.name||', '||esto.name) origen,
max(mund.name||', '||estd.name) destino, 
coalesce(
sum(
(
select
count(v.peso_origen_total)
from trafitec_viajes as v
	inner join trafitec_cotizaciones_linea_origen as vlo on(v.subpedido_id =vlo.id)
	inner join res_users as usu on(v.create_uid =usu.id)
where v.state = 'Nueva' and vlo.linea_id = l.id and v.create_date >= '{0}' and v.create_date <= '{1}' {3}
)
),0) viajes,

coalesce(
sum(
(
select
sum(v.peso_origen_total/1000)
from trafitec_viajes as v
	inner join trafitec_cotizaciones_linea_origen as vlo on(v.subpedido_id =vlo.id)
	inner join res_users as usu on(v.create_uid =usu.id)
where v.state = 'Nueva' and vlo.linea_id = l.id and v.create_date >= '{0}' and v.create_date <= '{1}' {3}
)
),0) actual,
coalesce(sum(l.cantidad),0) total,
0 porcentaje
from trafitec_cotizaciones_linea as l
inner join trafitec_cotizacion c on(l.cotizacion_id =c.id and c.state in('Disponible','EnEspera'))
inner join res_partner as cli on(c.cliente=cli.id)
inner join res_country_township_sat_code as muno on(l.municipio_origen_id=muno.id)
inner join res_country_state_sat_code as esto on(muno.state_sat_code =esto.id)
inner join res_country_township_sat_code as mund on(l.municipio_destino_id=mund.id)
inner join res_country_state_sat_code as estd on(mund.state_sat_code =estd.id)
where c.state in('Disponible','EnEspera') {2}
group by c.name,l.id
order by c.name,l.id		
""".format(self.buscar_fecha_inicial, self.buscar_fecha_final, condicion, condicion_viaje)
		self.env.cr.execute(sql)
		detalles = self.env.cr.dictfetchall()
		return detalles

	def detalles_xmes(self):
		detalles = []
		condicion = ""

		if self.buscar_folio:
			condicion += " and ct.name ilike '%{}%' ".format(self.buscar_folio or '')
		if self.buscar_cliente:
			condicion += " and cli.name ilike '%{}%' ".format(self.buscar_cliente or '')
		if self.buscar_usuario:
			condicion += " and usu.login ilike '%{}%' ".format(self.buscar_usuario or '')

		sql = """
select 
--suc.name sucursal,
ct.name cotizacion,
max(cli.name) cliente,
extract(year from v.create_date) ano,
extract(month from v.create_date) mes,
count(*) viajes,
sum(v.peso_origen_total/1000) peso
from trafitec_viajes as v
	--inner join trafitec_sucursal as suc on(v.sucursal_id=suc.id)
	inner join trafitec_cotizaciones_linea_origen as lo on(v.subpedido_id =lo.id)
    inner join trafitec_cotizaciones_linea as l on(lo.linea_id =l.id)
    inner join trafitec_cotizacion  as ct on(l.cotizacion_id =ct.id )
    inner join res_partner as cli on(ct.cliente =cli.id)
	inner join res_users as usu on(v.create_uid =usu.id)
where v.state ='Nueva' and v.create_date>='{0}' and v.create_date<='{1}' {2} 
group by ct.name,extract(year from v.create_date),extract(month from v.create_date)
order by ct.name,extract(year from v.create_date),extract(month from v.create_date)
""".format(self.buscar_fecha_inicial, self.buscar_fecha_final, condicion)
		self.env.cr.execute(sql)
		detalles = self.env.cr.dictfetchall()
		return detalles

	def detalles_xdia(self):
		detalles = []
		condicion = ""

		if self.buscar_folio:
			condicion += " and ct.name ilike '%{}%' ".format(self.buscar_folio or '')
		if self.buscar_cliente:
			condicion += " and cli.name ilike '%{}%' ".format(self.buscar_cliente or '')
		if self.buscar_usuario:
			condicion += " and usu.login ilike '%{}%' ".format(self.buscar_usuario or '')

		sql = """
select 
--suc.name sucursal,
ct.name cotizacion,
max(cli.name) cliente,
extract(year from v.create_date) ano,
extract(month from v.create_date) mes,
extract(day from v.create_date) dia,
count(*) viajes,
sum(v.peso_origen_total/1000) peso
from trafitec_viajes as v
	--inner join trafitec_sucursal as suc on(v.sucursal_id=suc.id)
	inner join trafitec_cotizaciones_linea_origen as lo on(v.subpedido_id =lo.id)
    inner join trafitec_cotizaciones_linea as l on(lo.linea_id =l.id)
    inner join trafitec_cotizacion  as ct on(l.cotizacion_id =ct.id )
    inner join res_partner as cli on(ct.cliente =cli.id)
	inner join res_users as usu on(v.create_uid =usu.id)
where v.state ='Nueva' and v.create_date>='{0}' and v.create_date<='{1}' {2} 
group by ct.name,extract(year from v.create_date),extract(month from v.create_date),extract(day from v.create_date)
order by ct.name,extract(year from v.create_date),extract(month from v.create_date),extract(day from v.create_date)
""".format(self.buscar_fecha_inicial, self.buscar_fecha_final, condicion)
		self.env.cr.execute(sql)
		detalles = self.env.cr.dictfetchall()
		return detalles

	def action_buscar(self):
		self.resultados_id = [(5, _, _)] #Vaciar los datos existentes.
		self.detalles_id = [(5, _, _)] #Vaciar los datos existentes.
		self.detalles_xmes_id = [(5, _, _)] #Vaciar los datos existentes.
		self.detalles_xdia_id = [(5, _, _)] #Vaciar los datos existentes.
		self.porcentaje_general = 0
		self.porcentaje_detalles = 0

		lista = []
		detalles = []
		filtro = []
		filtro_viajes = []

		suma_general = 0
		suma_detalles = 0
		conteo_general = 0
		conteo_detalles = 0

		general = []
		general = self.general()
		for c in general:
			actual = 0
			total = 0
			porcentaje = 0
			actual = c.get('actual', 0)
			total = c.get('total', 0)

			if total > 0:
				porcentaje = actual * 100 / total
			suma_general += porcentaje
			conteo_general += 1
			
			#Genera los datos.
			nuevo = {
				'cotizacion_folio': c.get('folio', ''),
				'cotizacion_cliente': c.get('cliente', ''),
				'cotizacion_numeroviajes': c.get('viajes', 0),
				'cotizacion_peso_actual': actual,
				'cotizacion_peso_total': total,
				'cotizacion_porcentaje': porcentaje
			}
			lista.append(nuevo)

		conjunto = self.detalles()
		for i in conjunto:
			actual = 0
			total = 0
			porcentaje = 0
			actual = i.get('actual', 0)
			total = i.get('total', 0)

			if total > 0:
				porcentaje = actual * 100 / total

			suma_detalles += porcentaje
			conteo_detalles += 1

			nuevo = {
				'cotizacion_folio': i.get('cotizacion_folio', ''),
				'cotizacion_linea': i.get('subpedido', ''),
				'cotizacion_cliente': i.get('cliente', ''),
				'cotizacion_origen': i.get('origen', ''),
				'cotizacion_destino': i.get('destino', ''),
				'cotizacion_numeroviajes': i.get('viajes', 0),
				'cotizacion_peso_actual': actual,
				'cotizacion_peso_total': total,
				'cotizacion_porcentaje': porcentaje
			}
			detalles.append(nuevo)

		self.detalles_xmes_id = self.detalles_xmes()
		self.detalles_xdia_id = self.detalles_xdia()

		if conteo_general > 0:
			self.porcentaje_general = suma_general / conteo_general

		if conteo_detalles > 0:
			self.porcentaje_detalles = suma_detalles / conteo_detalles

		self.resultados_id = lista
		self.detalles_id = detalles

class TrafitecReportesGeneralesPedidosAvanceResultado(models.Model):
	_name = 'trafitec.reportes.generales.pedidos.avance.resultado'
	_description ='Reportes generales pedidos avance resultado'
	buscar_id = fields.Many2one(string='Buscar', comodel_name='trafitec.reportes.generales.pedidos.avance.buscar')
	cotizacion_folio = fields.Char(string='Cotizacion', default='')
	cotizacion_cliente = fields.Char(string='Cliente', default='')
	cotizacion_numeroviajes = fields.Float(string='No. de viajes', default=0, help='Numero de viajes.')
	cotizacion_peso_actual = fields.Float(string='Peso actual')
	cotizacion_peso_total = fields.Float(string='Peso total')
	cotizacion_porcentaje = fields.Float(string='% Porcentaje de avance', default=0, help='Porcentaje de avance del la cotización.')

class TrafitecReportesGeneralesPedidosAvanceResultadoDetalles(models.Model):
	_name = 'trafitec.reportes.generales.pedidos.avance.detalles'
	_description ='Reportes generales pedidos avance detalles'
	buscar_id = fields.Many2one(string='Buscar', comodel_name='trafitec.reportes.generales.pedidos.avance.buscar')
	cotizacion_folio = fields.Char(string='Cotizacion', default='')
	cotizacion_linea = fields.Char(string='Linea', default='')
	cotizacion_cliente = fields.Char(string='Cliente', default='')
	cotizacion_origen = fields.Char(string='Origen', default='')
	cotizacion_destino = fields.Char(string='Destino', default='')
	cotizacion_numeroviajes = fields.Float(string='No. de viajes', default=0, help='Numero de viajes.')
	cotizacion_peso_actual = fields.Float(string='Peso actual')
	cotizacion_peso_total = fields.Float(string='Peso total')
	cotizacion_porcentaje = fields.Float(string='% Porcentaje de avance', default=0, help='Porcentaje de avance del la cotización.')

class TrafitecReportesGeneralesPedidosAvanceResultadoXMes(models.Model):
	_name = 'trafitec.reportes.generales.pedidos.avance.xmes'
	_description ='Reportes generales pedidos avance xmes'
	buscar_id = fields.Many2one(string='Buscar', comodel_name='trafitec.reportes.generales.pedidos.avance.buscar')
	cotizacion = fields.Char(string='Cotizacion', default='')
	cliente = fields.Char(string='Cliente', default='')
	ano = fields.Integer(string='Año', default=0)
	mes = fields.Integer(string='Mes', default='')
	viajes = fields.Integer(string='Viajes', default='')
	peso = fields.Float(string='Peso', default=0)

class TrafitecReportesGeneralesPedidosAvanceResultadoXDia(models.Model):
	_name = 'trafitec.reportes.generales.pedidos.avance.xdia'
	_description ='Reportes generales pedidos avance xdia'
	buscar_id = fields.Many2one(string='Buscar', comodel_name='trafitec.reportes.generales.pedidos.avance.buscar')
	cotizacion = fields.Char(string='Cotizacion', default='')
	cliente = fields.Char(string='Cliente', default='')
	ano = fields.Integer(string='Año', default=0)
	mes = fields.Integer(string='Mes', default=0)
	dia = fields.Integer(string='Dia', default=0)
	viajes = fields.Integer(string='Viajes', default=0)
	peso = fields.Float(string='Peso', default=0)
