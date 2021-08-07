

class TrafitecCrmTraficoTablero(models.Model):
	_name = "trafitec.crm.trafico.tablero"
	_description ='crm trafico tablero'

	# def init(self):
	# print("---SELF INIT---")
	# print(self)

	# print("---CONTEXT INIT---")
	# print(self._context)

	# try:
	# tablero_obj = self.env['trafitec.crm.trafico.tablero']
	# tablero_dat = self.env['trafitec.crm.trafico.tablero'].search([])
	# if len(tablero_dat) <= 0:
	#	tablero_obj.create({'name': 'CRM TRAFICO 3', 'color': 1})
	# except:
	#	print("**Error al inicializar el registro de CRM Tráfico.")


	def _compute_cotizaciones_disponibles_n(self):
		n = self.env['trafitec.cotizacion'].search([('state', '=', 'Disponible')])
		self.cotizaciones_disponibles_n = len(n)


	def _compute_misviajeshoy_n(self):
		n = self.env['trafitec.viajes'].search_count([('state', '=', 'Nueva'), ('create_uid', '=', self.env.user.id),
		                                              ('create_date', '>=', str(datetime.datetime.today().date()))])
		self.misviajeshoy_n = n


	def _compute_misviajes_n(self):
		n = self.env['trafitec.viajes'].search_count([('state', '=', 'Nueva'), ('create_uid', '=', self.env.user.id), (
			'create_date', '>=', (datetime.date.today() + timedelta(days=-7)).strftime("%Y-%m-%d"))])
		self.misviajes_n = n


	def _compute_misviajesc_n(self):
		n = self.env['trafitec.viajes'].search_count([('state', '!=', 'Nueva'), ('create_uid', '=', self.env.user.id)])
		self.misviajesc_n = n

	name = fields.Char(string="Nombre")
	color = fields.Integer(string='Color')
	cotizaciones_disponibles_n = fields.Integer(string="Cotizaciones disponibles",
	                                            compute=_compute_cotizaciones_disponibles_n, store=False)
	misviajes_n = fields.Integer(string="Mis viajes recientes", compute=_compute_misviajes_n, store=False)
	misviajeshoy_n = fields.Integer(string="Mis viajes hoy", compute=_compute_misviajeshoy_n, store=False)
	misviajesc_n = fields.Integer(string="Mis viajes cancelados", compute=_compute_misviajesc_n, store=False)

	def action_abrir_crm_cotizaciones(self):
		# view_id = self.env.ref('sli_trafitec.trafitec_crm_trafico_form').id
		return {
			'name': 'CRM Tráfico',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'tree,form',
			'res_model': 'trafitec.crm.trafico',
			# 'views': [(view_id, 'tree')],
			# 'form_view_ref': 'base.res_partner_kanban_view',
			# 'tree_view_ref': 'trafitec_crm_trafico_asociados_kanban',
			# 'kanban_view_ref': 'trafitec_crm_trafico_asociados_kanban',
			# 'tree_view_ref':'',
			# 'view_id': view_id,
			# 'view_ref': 'trafitec_crm_trafico_asociados_kanban',
			'target': 'current',
			'multi': True,
			# 'res_id': self.ids[0],
			'context': self._context,
			# 'domain': []
		}

	def action_abrir_crm_viajes(self):
		return {}

	def action_abrir_cotizaciones(self):
		# view_id = self.env.ref('sli_trafitec.view_cotizacion_tree').id
		return {
			'name': 'Mis cotizaciones (' + (self.env.user.name or '') + ')',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'tree,form',
			'res_model': 'trafitec.cotizacion',
			# 'views': [(view_id, 'tree')],
			# 'form_view_ref': 'base.res_partner_kanban_view',
			# 'tree_view_ref': 'trafitec_crm_trafico_asociados_kanban',
			# 'kanban_view_ref': 'trafitec_crm_trafico_asociados_kanban',
			# 'tree_view_ref':'',
			# 'view_id': view_id,
			# 'view_ref': 'trafitec_crm_trafico_asociados_kanban',
			# 'target': 'new',
			# 'res_id': self.ids[0],
			'context': {},
			'domain': [('create_uid', '=', self.env.user.id)]
		}

	def action_abrir_viajes(self):
		# view_id = self.env.ref('sli_trafitec.view_viajes_tree').id
		return {
			'name': 'Mis viajes (' + (self.env.user.name or '') + ')',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'tree,form',
			'res_model': 'trafitec.viajes',
			# 'views': [(view_id, 'tree')],
			# 'form_view_ref': 'base.res_partner_kanban_view',
			# 'tree_view_ref': 'trafitec_crm_trafico_asociados_kanban',
			# 'kanban_view_ref': 'trafitec_crm_trafico_asociados_kanban',
			# 'tree_view_ref':'',
			# 'view_id': view_id,
			# 'view_ref': 'trafitec_crm_trafico_asociados_kanban',
			# 'target': 'new',
			# 'res_id': self.ids[0],
			'context': {},
			'domain': [('create_uid', '=', self.env.user.id)]
		}
