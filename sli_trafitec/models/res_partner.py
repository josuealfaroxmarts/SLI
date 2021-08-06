from odoo import api, fields, models, _


class ResPartner(models.Model):
	_inherit = "res.partner"

	status = fields.Char(string="status ")
	nueva_clasificacion = fields.Many2one(string="Nueva clasificación")
	aseguradora = fields.Boolean(string="Es aseguradorados")
	excedente_merma = fields.Selection(
		[
			("No cobrar", "No cobrar"), ("Porcentaje: Cobrar diferencia", "Porcentaje: Cobrar diferencia"),
			("Porcentaje: Cobrar todo", "Porcentaje: Cobrar todo"), ("Kg: Cobrar diferencia", "Kg: Cobrar diferencia"),
			("Kg: Cobrar todo", "Kg: Cobrar todo"), ("Cobrar todo", "Cobrar todo")
		],
		string="Si la merma excede lo permitido",
		default="Porcentaje: Cobrar diferencia"
	)
	facturar_con = fields.Selection(
		[
			("Peso convenido", "Peso convenido"),
			("Peso origen", "Peso origen"),
			("Peso destino", "Peso destino")
		],
		string="Facturar con",
		default="Peso origen"
	)
	clasificacion = fields.Selection(
		[
			("(No clasificado)", "(No clasificado)"),
			("Flete", "Flete"),
			("No flete", "No flete"),
			("Flete y no flete", "Flete y no flete")],
		string="Clasificación",
		default="(No clasificado)"
	)
	merma_permitida_por = fields.Float(string="Merma permitida (%)")
	merma_permitida_kg = fields.Float(string="Merma permitida (KG)")
	permitir_diferente = fields.Boolean(string="Permitir diferente pedido al facturar")
	facturar_ordenes = fields.Boolean(string="Facturar ordenes de carga sin documentos")
	prorroga = fields.Boolean(string="Prorroga")
	fecha_prorroga = fields.Date(string="Fecha prorroga")

	# Proveedores
	plazas_ban_id = fields.Many2one(
		"trafitec.plazas.banxico",
		string="Plaza"
	)
	no_sucursal = fields.Char(string="No. de sucursal")

	documentos_id = fields.One2many(
		"trafitec.clientes.documentos",
		"partner_id"
	)
	permitir_ta_mayor_tc = fields.Boolean(
		string="Permitir TA mayor a TC.",
		default=False,
		required=True
	)
	equipoventa_id = fields.Many2one(
		string="Equipo de venta",
		comodel_name="crm.team"
	)
	moroso_prorroga_st = fields.Boolean(
		string="Moroso prorroga",
		default=False,
		help="Indica si se aplicara la prorroga de morosos."
	)
	moroso_prorroga_fecha = fields.Date(
		string="Moroso Fecha de prorroga",
		help="Indica la fecha de la prorroga para los morosos."
	)
	bloqueado_cliente_bloqueado = fields.Boolean(
		string="Cliente bloqueado",
		default=False,
		help="Cliente bloqueado, no se permitira hacer: cotizaciones, viajes y facturas."
	)
	bloqueado_cliente_clasificacion_id = fields.Many2one(
		string="Motivo de bloqueo",
		comodel_name="trafitec.clasificacionesg",
		default=False,
		help="Clasificación del bloqueo."
	)
	license_approved = fields.Boolean(string="licencia aprobada")
	nss_approved = fields.Boolean(string="Numero de seguro social aprobado")
	name_healthcare_number = fields.Char()
	adj_healthcare_number = fields.Binary(string="Adjunto numero de seguro social")
	ext_healthcare_number = fields.Char()
	healthcare_number = fields.Char(string="Numero de seguro social")
	name_license_driver = fields.Char(
		string="Nombre Licencia",
		compute="change_name"
	)
	ext_license_driver = fields.Char()
	license_driver = fields.Binary(string="Licencia")
	healthcare_number = fields.Char(string="Número de seguro social")
	adj_healthcare_number = fields.Binary(string="Adjunto Número de seguro social")
	name_healthcare_number = fields.Char(compute="change_name")
	ext_healthcare_number = fields.Char()

	crm_trafico_ultimocontacto_fechahora = fields.Datetime(string="Último contacto fecha y hora")
	crm_trafico_ultimocontacto_usuario_id = fields.Many2one(string="Último contacto usuario", comodel_name="res.users")
	crm_trafico_ultimocontacto_dias_transcurridos = fields.Integer(string="Último contacto dias transcurridos",
	                                                               compute=_compute_ultimocontacto_dias_trascurridos,
	                                                               store=False, default=0)
	crm_trafico_numerounidades = fields.Integer(string="Número de unidades", compute=_compute_numerounidades,
	                                            store=False, default=0)
	crm_trafico_saldo = fields.Float(string="Saldo total", compute=_compute_saldo, default=0)
	crm_trafico_saldo_flete = fields.Float(string="Saldo flete", compute=_compute_saldo_flete, default=0)

	crm_trafico_tarifa_minima = fields.Float(string="Tarifa minima", compute=_compute_viaje_tarifa_minima, default=0)
	crm_trafico_info = fields.Text(string="Info", compute=_compute_crm_trafico_info, default="--")
	crm_trafico_ultimo_rechazo_id = fields.Many2one(string="Último rechazo",
	                                                comodel_name="trafitec.crm.trafico.registro")
	crm_trafico_ultimos_registros_info1 = fields.Text(string="Últimos registros",
	                                                  compute=_compute_crm_ultimosregistros_info1)
	crm_trafico_ultimos_registros_info2 = fields.Text(string="Último registros",
	                                                  compute=_compute_crm_ultimosregistros_info2)


	asociado = fields.Boolean(string='Es asociado')
	tipoasociado = fields.Selection([('externo', 'Externo'), ('interno', 'Interno')], string="Tipo de asociado")
	notificar_contrarecido = fields.Boolean(string='Notificar generación de contrarecibo')
	notificar_pago = fields.Boolean(string='Notificar Pago')
	porcentaje_comision = fields.Float(string='Porcentaje de comisión')
	usar_porcentaje = fields.Boolean(string='Usar porcentaje de línea de negocio')
	creditocomision = fields.Boolean(string='Crédito de comisión')
	calificacion = fields.Selection(
		[('A-Administración total', 'A-Administración total'), ('B-Alianza estrategica', 'B-Alianza estrategica'),
		 ('C-Asociado normal', 'C-Asociado normal'), ('D-No son asociados', 'D-No son asociados')],
		string='Calificación')
	info_completa = fields.Boolean(string='Información completa')
	doc_completa = fields.Boolean(string='Documentación completa')
	validado = fields.Boolean(string='Validado')
	trafitec_rutas_id = fields.One2many('trafitec.rutas', 'asociado')
	trafitec_unidades_id = fields.One2many('trafitec.unidades', 'asociado')

	operador = fields.Boolean(string='Es operador')
	status_document = fields.Boolean()
	asociado_operador = fields.Many2one('res.partner',
	                                    domain="[('asociado','=',True),(['company','person'],'in','company_type')]",
	                                    string="Asociado",
	                                    store=True)
	imei = fields.Char(string='IMEI')
	noviajes = fields.Integer(string='No. Viajes', readonly=True)
	radio = fields.Char(string='Radio')
	celular = fields.Char(string='Celular')
	celular_enlazado = fields.Selection([('No aplica', 'No aplica'), ('No', 'No'), ('Si', 'Si')],
	                                    string='Celular Enlazado')
	activo_slitrack = fields.Boolean(string='Activo para SLITrack')
	combustible_convenio_st = fields.Boolean(string='Convenio de combustible', default=False, help='Indica si el asociado tiene convenio para carga de combustible a crédito.')


	@api.constrains('vat')
	def check_vat(self):
		return self.check_vat_mx(self.vat)

	def check_vat(self, vat):
		if (14 >= len(self.vat) <= 15) :
			return True
		else :
			raise UserError(_('Aviso !\nEl RFC debe contener entre 14 a 15 caracteres incluyendo el codigo del país (MX).'))


	@api.constrains('vat')
	def _construct_constraint_msg(self):
		return True

	@api.constrains('vat', 'company_type')
	def _check_constrains(self):
		if self.company_type != 'person':
			if self.vat:
				if len(self.vat) >= 12 and len(self.vat) <= 13 :
					vat_obj = self.env['res.partner'].search(
						[('vat', 'ilike', self.vat), ('company_id', '=', self.company_id.id)])
					if len(vat_obj) > 1:
						raise UserError(_('Aviso !\nEl RFC no se puede repetir.'))
			"""
			elif not self.vat:
				raise UserError(_(
					'Aviso !\nEl RFC no puede estar vacio.'))
			"""

	@api.constrains('customer', 'excedente_merma')
	def _check_excedente_merma(self):
		if self.customer == True:
			obj_groups = self.env['res.users'].search([('partner_id', '=', self.id)])
			if len(obj_groups) == 0:
				if self.excedente_merma == False:
					raise UserError(_('Aviso !\nEl cliente tiene que tener definido algun excedente de merma.'))

	@api.constrains('customer', 'facturar_con')
	def _check_facturar_con(self):
		if self.customer == True:
			obj_groups = self.env['res.users'].search([('partner_id', '=', self.id)])
			if len(obj_groups) == 0:
				if self.facturar_con == False:
					raise UserError(
						_('Aviso !\nEl cliente tiene que tener definido algun valor en el campo facturar con.'))

	@api.model
	def create(self, vals):

		id = super(trafitec_asociados, self).create(vals)
		if 'asociado' in vals:
			if vals['asociado'] == True:
				obj_estados = self.env['res.country.state'].search([('country_id', '=', 157)])
				for estados in obj_estados:
					valores = {'asociado': id.id, 'estado': estados.id, 'vigente': True}
					self.env['trafitec.rutas'].create(valores)
		return id

	def write(self, vals):
		if 'asociado' in vals:
			asociado = vals['asociado']
		else:
			asociado = self.asociado

		if asociado == True:
			obj_rutas = self.env['trafitec.rutas'].search([('asociado', '=', self.id)])
			if len(obj_rutas) == 0:
				obj_estados = self.env['res.country.state'].search([('country_id', '=', 157)])
				for estados in obj_estados:
					valores = {'asociado': self.id, 'estado': estados.id, 'vigente': True}
					self.env['trafitec.rutas'].create(valores)
		return super(trafitec_asociados, self).write(vals)




@api.constrains("moroso_prorroga_st", "moroso_prorroga_fecha")
	def _check_moroso(self):
		if self.moroso_prorroga_st and not self.moroso_prorroga_fecha:
			raise UserWarning(_("Alerta.."), _("Debe especificar la fecha de prorroga de moroso."))

	def _computex(self):
		return 0

	def _compute_ultimocontacto_dias_trascurridos(self):
		# self.ensure_one()
		if self.crm_trafico_ultimocontacto_fechahora:
			self.crm_trafico_ultimocontacto_dias_transcurridos = (
					datetime.datetime.today() - fields.Datetime.from_string(
				self.crm_trafico_ultimocontacto_fechahora)).days

	def _compute_numerounidades(self):
		unidades_obj = self.env["trafitec.unidades"]
		unidades_dat = unidades_obj.search([("asociado", "=", self.id)])
		total = 0
		for u in unidades_dat:
			total += u.cantidad
		self.crm_trafico_numerounidades = total

	def _compute_saldo(self):
		facturas_obj = self.env["account.move"]
		facturas_dat = facturas_obj.search(
			[("partner_id", "=", self.id), ("state", "=", "open"), ("move_type", "=", "in_invoice")])
		total = 0
		for f in facturas_dat:
			total += f.amount_residual
		self.crm_trafico_saldo = total


	def _compute_saldo_flete(self):
		facturas_obj = self.env["account.move"]
		facturas_dat = facturas_obj.search(
			[("partner_id", "=", self.id), ("state", "=", "open"), ("contrarecibo_id", "!=", False)])
		total = 0
		for f in facturas_dat:
			total += f.amount_residual
		self.crm_trafico_saldo = total

	def saldo_vencido(self, persona_id=None):
		resultado = None
		saldo = 0.0
		sql = ""

		sql = """
		select
sum(f.amount_residual) saldo
from account_move as f
where f.state = "open"
and f.move_type="out_invoice"
and f.invoice_date_due<current_date
and f.partner_id={}
		""".format(persona_id)
		self.env.cr.execute(sql)
		resultado = self.env.cr.dictfetchall()

		if len(resultado) > 0:
			saldo = resultado[0].get("saldo", 0)

		return saldo

	"""
	Indica si el cliente especificado es un cliente
	que debe facturas vencidas.
	"""

	def es_moroso(self, persona_id=None):
		# ---------------------------------
		# OBJETOS Y VARIABLES
		# ---------------------------------

		saldo = 0.00
		fecha_prorroga = None

		persona_obj = self.env["res.partner"]
		persona_dat = persona_obj.search([("id", "=", persona_id)])
		saldo = self.saldo_vencido(persona_id)

		if persona_dat.moroso_prorroga_fecha:
			fecha_prorroga = datetime.datetime.strptime(persona_dat.moroso_prorroga_fecha, "%Y-%m-%d").date()

		if saldo and saldo > 0:
			pasar = False
			if persona_dat.moroso_prorroga_st and persona_dat.moroso_prorroga_fecha and datetime.datetime.today().date() <= fecha_prorroga:
				pasar = True

			if not pasar:
				return True

		return False


	def _compute_viaje_tarifa_minima(self):
		contexto = self._context
		trafitec_obj = self.env["trafitec.glo"]

		print("---CONTEXTO EN _compute_viaje_tarifa_minima---")
		print(contexto)

		municipio_origen_id = -1
		municipio_destino_id = -1
		if "municipio_origen_id" in contexto and "municipio_destino_id" in contexto:
			viajes = []

			municipio_origen_id = contexto.get("municipio_origen_id", -1)
			municipio_destino_id = contexto.get("municipio_destino_id", -1)
			viajes = trafitec_obj.ViajesAsociadoPorMunicipios(self.id, municipio_origen_id, municipio_destino_id)
			print("----VIAJES ENCONTRADOS CON ViajesAsociadoPorMunicipios----")
			print(viajes)
			if len(viajes) > 0:
				self.crm_trafico_tarifa_minima = viajes[0]["tarifa"]  # El primero
			else:
				self.crm_trafico_tarifa_minima = 0


	def _compute_crm_trafico_info(self):
		contexto = self._context
		trafitec_obj = self.env["trafitec.glo"]

		info = "--"

		print("---CONTEXTO EN _compute_viaje_tarifa_minima---")
		print(contexto)

		municipio_origen_id = -1
		municipio_destino_id = -1
		if "municipio_origen_id" in contexto and "municipio_destino_id" in contexto:
			viajes = []

			municipio_origen_id = contexto.get("municipio_origen_id", -1)
			municipio_destino_id = contexto.get("municipio_destino_id", -1)
			viajes = trafitec_obj.ViajesAsociadoPorMunicipios(self.id, municipio_origen_id, municipio_destino_id)
			# print("----VIAJES ENCONTRADOS CON ViajesAsociadoPorMunicipios----")
			# print(viajes)
			if len(viajes) > 0:
				info = "Viajes: " + str(len(viajes)) + " "
				info += "Tarifa mínima: " + str(viajes[0]["tarifa"]) + " "
				# info += "Tarifa máxima: "+str(viajes[-1]["tarifa"])+" "
				# info += "Tarifa maxima:"+viajes[-1:]["tarifa"]+" "
				self.crm_trafico_info = info
			else:
				self.crm_trafico_info = info


	def _compute_crm_ultimosregistros_info1(self):
		info = ""
		c = 0
		registros = self.env["trafitec.crm.trafico.registro"].search([("asociado_id", "=", self.id)], limit=2,
		                                                             order="id desc")
		if len(registros) >= 1:
			info = "(1) " + str(registros[0].detalles or "")
		self.crm_trafico_ultimos_registros_info1 = info


	def _compute_crm_ultimosregistros_info2(self):
		info = ""
		c = 0
		registros = self.env["trafitec.crm.trafico.registro"].search([("asociado_id", "=", self.id)], limit=2,
		                                                             order="id desc")
		if len(registros) >= 2:
			info = "(2) " + str(registros[1].detalles or "")
		self.crm_trafico_ultimos_registros_info2 = info




	def _compute_unidades_txt(self):
		unidades_obj = self.env["trafitec.unidades"]
		unidades_dat = unidades_obj.search([("asociado", "=", self.id)])
		total = ""
		for u in unidades_dat:
			total += str(u.movil.name or "")+" (" +str(u.cantidad or 0)+") "
		self.crmt_unidades_txt = total

	fecha_nacimiento = fields.Date(string="Fecha de nacimiento")
	status_user = fields.Boolean(default=False)
	crmt_logistico_correo = fields.Char(string="Correo de contacto logistico", default="", help="Correo del concato logistico")

	crmt_unidades_txt = fields.Char(string="Unidades", compute=_compute_unidades_txt, default="")
	nuevo_telefono = fields.Char(string="Teléfono")


	@api.constrains("email","asociado","aseguradora","customer","supplier")
	def _check_email(self):
		if self.asociado or self.aseguradora or self.customer or self.supplier:
			if not self.email: #and not self.parent_id:
				raise UserError(_("Alerta..\nEl correo electrónico (EMail) no puede estar vacío."))

	def action_marcar_contactado(self):
		view_id = self.env.ref("sli_trafitec.trafitec_crm_trafico_registro_form").id

		print("---CONTEXTO AL MOSTRAR NUEVO REGISTRO---")
		print(self._context)
		return {"name": "Nuevo registro de contacto", "type": "ir.actions.act_window", "view_type": "form",
		        "view_mode": "form", "res_model": "trafitec.crm.trafico.registro",  # "views": [(view_id, "tree")],
		        # "form_view_ref": "base.res_partner_kanban_view",
		        # "tree_view_ref": "trafitec_crm_trafico_asociados_kanban",
		        # "kanban_view_ref": "trafitec_crm_trafico_asociados_kanban",
		        # "tree_view_ref":"",
		        "view_id": view_id,  # "view_ref": "trafitec_crm_trafico_asociados_kanban",
		        "target": "new",  # "res_id": self.ids[0],
		        "context": {}}


	def action_vercalendario(self):
		view_id = self.env.ref("calendar.view_calendar_event_calendar").id
		return {"name": "Calendario", "type": "ir.actions.act_window", "view_type": "form",
		        "view_mode": "calendar,tree", "res_model": "calendar.event",  # "views": [(view_id, "tree")],
		        # "form_view_ref": "calendar.view_calendar_event_calendar",
		        # "tree_view_ref": "trafitec_crm_trafico_asociados_kanban",
		        # "kanban_view_ref": "trafitec_crm_trafico_asociados_kanban",
		        # "tree_view_ref":"",
		        # "view_id": view_id,
		        # "view_ref": "calendar.view_calendar_event_calendar",
		        # "target": "new",
		        # "res_id": self.ids[0],
		        "context": {}}

	def action_abrir_viajes_asociado(self):
		self.ensure_one()
		# view_id = self.env.ref("sli_trafitec.view_viajes_tree").id

		# if self._context.get("active_model", "") != "res.partner":
		#	raise UserError(_("El modelo del contexto debe ser res.partner."))

		return {"name": "Viajes de asociado (" + (self.name or "") + ")", "type": "ir.actions.act_window",
		        "view_type": "form", "view_mode": "tree,form", "res_model": "trafitec.viajes",
		        # "views": [(view_id, "tree")],
		        # "form_view_ref": "base.res_partner_kanban_view",
		        # "tree_view_ref": "trafitec_crm_trafico_asociados_kanban",
		        # "kanban_view_ref": "trafitec_crm_trafico_asociados_kanban",
		        # "tree_view_ref":"",
		        # "view_id": view_id,
		        # "view_ref": "trafitec_crm_trafico_asociados_kanban",
		        # "target": "new",
		        # "res_id": self.ids[0],
		        "context": {}, "domain": [("state", "=", "Nueva"), ("asociado_id", "=", self.id)]}

	def action_abrir_facturas_asociado(self):
		self.ensure_one()
		# view_id = self.env.ref("sli_trafitec.view_viajes_tree").id

		# if self._context.get("active_model", "") != "res.partner":
		#	raise UserError(_("El modelo del contexto debe ser res.partner."))

		return {"name": "Facturas de asociado (" + (self.name or "") + ")", "type": "ir.actions.act_window",
		        "view_type": "form", "view_mode": "tree", "res_model": "account.move", # "views": [(view_id, "tree")],
		        # "form_view_ref": "base.res_partner_kanban_view",
		        # "tree_view_ref": "trafitec_crm_trafico_asociados_kanban",
		        # "kanban_view_ref": "trafitec_crm_trafico_asociados_kanban",
		        # "tree_view_ref":"",
		        # "view_id": view_id,
		        # "view_ref": "trafitec_crm_trafico_asociados_kanban",
		        # "target": "new",
		        # "res_id": self.ids[0],
		        "context": {},
		        "domain": [("partner_id", "=", self.id), ("state", "=", "open"), ("type", "=", "in_invoice")]}

	def action_abrir_contactos(self):
		self.ensure_one()
		# view_id = self.env.ref("sli_trafitec.view_viajes_tree").id

		# if self._context.get("active_model", "") != "res.partner":
		#	raise UserError(_("El modelo del contexto debe ser res.partner."))

		return {"name": "Contactos (" + (self.name or "") + ")", "type": "ir.actions.act_window", "view_type": "form",
		        "view_mode": "tree,form", "res_model": "res.partner", # "views": [(view_id, "tree")],
		        # "form_view_ref": "base.res_partner_kanban_view",
		        # "tree_view_ref": "trafitec_crm_trafico_asociados_kanban",
		        # "kanban_view_ref": "trafitec_crm_trafico_asociados_kanban",
		        # "tree_view_ref":"",
		        # "view_id": view_id,
		        # "view_ref": "trafitec_crm_trafico_asociados_kanban",
		        # "target": "new",
		        # "res_id": self.ids[0],
		        "context": {}, "domain": [("parent_id", "=", self.id), ("type", "=", "contact")]}

	def action_abrir_contacto(self):
		self.ensure_one()
		# view_id = self.env.ref("sli_trafitec.view_viajes_tree").id

		# if self._context.get("active_model", "") != "res.partner":
		#	raise UserError(_("El modelo del contexto debe ser res.partner."))

		return {"name": "Contacto (" + (self.name or "") + ")", "type": "ir.actions.act_window", "view_type": "form",
		        "view_mode": "form", "res_model": "res.partner", # "views": [(view_id, "tree")],
		        # "form_view_ref": "base.res_partner_kanban_view",
		        # "tree_view_ref": "trafitec_crm_trafico_asociados_kanban",
		        # "kanban_view_ref": "trafitec_crm_trafico_asociados_kanban",
		        # "tree_view_ref":"",
		        # "view_id": view_id,
		        # "view_ref": "trafitec_crm_trafico_asociados_kanban",
		        # "target": "new",
		        "res_id": self.id, "context": {}, "domain": []}

	@api.onchange("aseguradora", "asociado", "operador", "company_type")
	def _onchange_asegurador(self):
		if self.aseguradora == True:
			if self.asociado == True or self.operador == True:
				self.asociado = False
				self.operador = False
				res = {"warning": {"title": _("Advertencia"),
				                   "message": _("No puede seleccionar que un contacto sea aseguradora, operador o asociado.")}}
				return res
			if self.company_type != "company":
				self.aseguradora = False
				res = {"warning": {"title": _("Advertencia"),
				                   "message": _("Para que un contacto sea aseguradora, tiene que ser una compañia")}}
				return res

	"""
	----------------------------------------------------------------------------------------------------------------------------------------------------
	FUNCIONES GENERALES DE UTILERIA
	----------------------------------------------------------------------------------------------------------------------------------------------------
	"""

	"""
	Regresa el saldo total del cliente de viajes no facturados.
	"""

	def cliente_saldo_viajes(self, persona_id, excluir_viaje_id=None):
		sql_viajes = ""
		total = 0
		total_viajes = 0

		empresa_id = self.env.user.company_id.id

		sql_viajes = """
	select
	sum(
	case
	when v.flete_cliente <= 0 then v.peso_autorizado * v.tarifa_cliente
	else v.flete_cliente
	end
	) total
	from trafitec_viajes as v
		inner join trafitec_moviles as mov on(v.tipo_remolque=mov.id)
	where v.state="Nueva"
	and v.en_factura=false
	and v.cliente_id={}
	and v.company_id={}
	""".format(persona_id, empresa_id)

		if excluir_viaje_id != None:
			sql_viajes += " and v.id !={}".format(excluir_viaje_id)

		self.env.cr.execute(sql_viajes)
		viajes = self.env.cr.dictfetchall()
		if len(viajes) > 0 and viajes[0]["total"]:
			total_viajes = viajes[0]["total"]

		total = total_viajes
		return total

	def cliente_saldo_facturas(self, persona_id):
		sql_facturas = ""
		total = 0

		empresa_id = self.env.user.company_id.id

		total_facturas = 0
		sql_facturas = """
	select
	sum(f.amount_residual) total
	from account_move as f
	where
	f.state="open"
	and f.partner_id={} and company_id={}
			""".format(persona_id, empresa_id)
		self.env.cr.execute(sql_facturas)
		facturas = self.env.cr.dictfetchall()
		if len(facturas) > 0 and facturas[0]["total"]:
			total_facturas = facturas[0]["total"]
		total = total_facturas
		return total

	def cliente_saldo_total(self, persona_id, excluir_viaje_id=None):
		return self.cliente_saldo_viajes(persona_id, excluir_viaje_id) + self.cliente_saldo_facturas(persona_id)

	def cliente_saldo_excedido(self, persona_id, monto_adicional, excluir_viaje_id=None):
		if not self._context.get("validar_credito_cliente", True):
			return False

		persona_obj = self.env["res.partner"]
		persona_datos = persona_obj.search([("id", "=", persona_id)])

		cliente_saldo = 0
		cliente_limite_credito = 0

		prorroga_hay = False
		prorroga_fecha = None

		# try:
		cliente_saldo = persona_obj.cliente_saldo_total(persona_id, excluir_viaje_id) + monto_adicional
		cliente_limite_credito = persona_datos.limite_credito

		prorroga_hay = persona_datos.prorroga
		if persona_datos.fecha_prorroga:
			prorroga_fecha = datetime.datetime.strptime(persona_datos.fecha_prorroga, "%Y-%m-%d").date()

		if cliente_saldo > cliente_limite_credito:
			if prorroga_hay:
				if prorroga_fecha and datetime.date.today() > prorroga_fecha:
					return True
			else:
				return True
		return False

