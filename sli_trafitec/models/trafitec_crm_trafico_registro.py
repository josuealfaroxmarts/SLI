
class TrafitecCrmTraficoRegistro(models.Model):
	_name = 'trafitec.crm.trafico.registro'
	_description ='trafico registro'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_order = 'id desc'
	_rec_name = 'id'

	asociado_id = fields.Many2one(string='Asociado', comodel_name='res.partner', tracking=True)
	asociado_id_txt = fields.Char(string='Asociado texto', related='asociado_id.name', readonly=True)

	detalles = fields.Char(string='Detalles', default='', required=True, tracking=True)
	tipo = fields.Selection(string='Tipo',
	                        selection=[('llamada_telefonica', 'Llamada telefónica'), ('email', 'Correo electrónico'),
	                                   ('mensajero_instataneo', 'Mensajero instantaneo')], default='llamada_telefonica',
	                        required=True, tracking=True)
	generar_evento_st = fields.Boolean(string='Registrar evento en calendario', default=False)
	generar_evento_dias = fields.Integer(string='Dias para nuevo evento', default=3)
	generar_evento_fechahora = fields.Datetime(string='Fecha para nuevo evento')


	@api.depends('viajes_id')
	def _compute_numero_viajes(self):
		self.viajes_n = len(self.viajes_id)

	seg_modificar = fields.Boolean(string='Permitir modificar', default=True, tracking=True)
	cotizacion_id = fields.Many2one(string='Cotización', comodel_name='trafitec.cotizacion',
	                                tracking=True)
	cotizacion_id_txt = fields.Char(string='Cotización ', related='cotizacion_id.name', readonly=True)
	viajes_id = fields.One2many(string='Viajes', comodel_name='trafitec.crm.trafico.registro.viajes',
	                            inverse_name='registro_id')
	viajes_n = fields.Integer(string='Número de viajes', compute=_compute_numero_viajes, default=0, store=True)
	motivo_rechazo_id = fields.Many2one(string='Motivo de rechazo', comodel_name='trafitec.clasificacionesg',
	                                    tracking=True)
	tarifa = fields.Float(string='Tarifa', default=0)
	state = fields.Selection(string='Estado cotizacion',
	                         selection=[('nuevo', 'Nuevo'), ('aceptado', 'Aceptado'), ('rechazado', 'Rechazado')],
	                         default='nuevo', tracking=True, required=True)

	@api.model
	def default_get(self, fields):
		res = super(trafitec_crm_trafico_registro, self).default_get(fields)

		if 'cotizacion_id' in self._context and 'active_id' in self._context:
			cotizacion_id = self._context.get('cotizacion_id', None)
			asociado_id = self._context.get('active_id', None)
			cotizacion_dat = self.env['trafitec.cotizacion'].browse([cotizacion_id])
			persona_dat = self.env['res.partner'].browse([asociado_id])
			res.update(
				{
					'cotizacion_id': cotizacion_dat.id,
					'cotizacion_id_txt': cotizacion_dat.name,
					'asociado_id': persona_dat.id,
					'asociado_id_txt': persona_dat.name
				}
			)
		return res

	@api.onchange('state')
	def _onchange_state(self):
		if self.state != 'rechazado':
			self.motivo_rechazo_id = False

	def action_aceptado(self):
		self.state = 'aceptado'

	def action_rechazado(self):
		self.state = 'rechazado'

	def valida(self, vals=None, tipo=1):  # 1=Crear, 2=Modificar, 3=Borrar.
		if vals:
			if 'generar_evento_fechahora' in vals and 'generar_evento_st' in vals:

				if vals['generar_evento_st']:
					fechahora = vals['generar_evento_fechahora']
					if not fechahora:
						raise UserError(_('Debe especificar la fecha y hora para el nuevo evento.'))

		"""
			if 'state' in vals:
				if vals['state'] == 'aceptado':
					if not 'viajes_id' in vals or len(vals.get('viajes_id', [])) <= 0:
						raise UserError(_('Debe especificar los viajes.'))
		"""

		state = ''
		viajes_id = []
		motivo_rechazo_id = None
		tarifa = 0.00
		if tipo == 1:  # Crear.
			state = vals['state']
			# viajes_id = vals['viajes_id']
			motivo_rechazo_id = vals['motivo_rechazo_id']
			tarifa = vals['tarifa']
		elif tipo == 2:  # Modificar.
			# registro_dat = self.env['trafitec.crm.trafico.registro'].browse([self.id])
			if 'state' in vals:
				state = vals['state']
			else:
				state = self.state

			"""
			if 'viajes_id' in vals:
				viajes_id = vals['viajes_id']
			else:
				viajes_id = self.viajes_id
			"""

			if 'motivo_rechazo_id' in vals:
				motivo_rechazo_id = vals['motivo_rechazo_id']
			else:
				motivo_rechazo_id = self.motivo_rechazo_id

			if 'tarifa' in vals:
				tarifa = vals['tarifa']
			else:
				tarifa = self.tarifa

		if state == 'aceptado':
			"""
			if len(viajes_id) <= 0:
				raise UserError(_('Debe especificar al menos un viaje.'))
			"""

			if tarifa <= 0:
				raise UserError(_('Debe especificar la tarifa'))

		if state == 'rechazado':
			if not motivo_rechazo_id:
				raise UserError(_('Debe especificar el motivo de rechazo'))

			"""
			if len(viajes_id) > 0:
				raise UserError(_('Debe quitar los viajes relacionados.'))
			"""

	@api.model
	def create(self, vals):
		self.valida(vals, 1)

		persona_obj = self.env['res.partner']
		persona_dat = None

		if 'active_id' in self._context:
			vals['asociado_id'] = self._context['active_id']

		if 'cotizacion_id' in self._context:
			vals['cotizacion_id'] = self._context['cotizacion_id']

		# Lo marca como generado.
		vals.update({'seg_modificar': False})

		nuevo = super(trafitec_crm_trafico_registro, self).create(vals)
		if 'active_id' in self._context:
			persona_dat = persona_obj.search([('id', '=', self._context['active_id'])])
			persona_dat.write({
				'crm_trafico_ultimocontacto_fechahora': datetime.datetime.today(),
				'crm_trafico_ultimocontacto_usuario_id': self._uid
			})
		# self.asociado_id.crm_trafico_ultimocontacto_fechahora = datetime.datetime.today()  # +timedelta(days=-3)
		# self.asociado_id.crm_trafico_ultimocontacto_usuario_id = self._uid

		if nuevo.generar_evento_st:
			tipo_txt = 'Contactar a: '

			if persona_dat:
				tipo_txt += (persona_dat.name or persona_dat.display_name or '')

			calendario_obj = self.env['calendar.event']
			nuevoevento = {
				'name': tipo_txt,
				'user_id': self.env.user.id,
				'description': nuevo.detalles,
				'start': str(nuevo.generar_evento_fechahora),
				'stop': str(nuevo.generar_evento_fechahora)  # nuevo.generar_evento_fechahora + timedelta(hours=1)
			}
			calendario_obj.create(nuevoevento)

		self._proceso_rechazo(vals, nuevo)

		return nuevo

	def write(self, vals):
		self.valida(vals, 2)

		# vals.update({'seg_modificar':False})
		modificado = super(trafitec_crm_trafico_registro, self).write(vals)

		self._proceso_rechazo(vals, modificado)
		return modificado

	def _proceso_rechazo(self, vals, obj=None):
		state = ''
		asociado_id = None

		if 'state' in vals:
			state = vals.get('state', '')

			if 'asociado_id' in vals:
				asociado_id = vals.get('asociado_id', None)
			else:
				asociado_id = self.asociado_id.id

			if state == 'rechazado' and asociado_id and obj:
				persona_dat = self.env['res.partner'].browse([asociado_id])
				persona_dat.write({'crm_trafico_ultimo_rechazo_id': obj.id})
		return
