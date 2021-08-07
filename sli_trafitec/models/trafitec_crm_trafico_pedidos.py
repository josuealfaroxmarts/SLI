
class TrafitecCrmTraficoPedidos(models.TransientModel):
	_name = 'trafitec.crm.trafico.pedidos'
	_description ='crm trafico pedidos'
	crm_trafico_id = fields.Many2one(string="CRM", comodel_name="trafitec.crm.trafico")
	cotizacion_id = fields.Many2one(string='Cotización', comodel_name='trafitec.cotizacion')
	cotizacion_linea_id = fields.Many2one(string='Cotizacion línea', comodel_name='trafitec.cotizaciones.linea')
	cotizacion_linea_xid = fields.Integer(string='Cotización línea', related='cotizacion_linea_id.id')
	folio = fields.Char(string='Folio')
	fecha = fields.Char(string='Fecha')
	origen = fields.Char(string='Origen')
	destino = fields.Char(string='Destino')
	producto = fields.Char(string='Producto')
	tarifa_a = fields.Float(string='Tarifa')
	cliente = fields.Char(string='Cliente')
	usuarios_asignados = fields.Char(string='Asignado a')
	peso = fields.Float(string='Peso')
	peso_viajes = fields.Float(string='Peso viajes')
	avance = fields.Float(string='Avance', default=0)
	detalles = fields.Char(string='Detalles', default='')
	semaforo_valor = fields.Char(string='Semáforo')
	lineanegocio = fields.Char(string='Línea de negocio')
	estado = fields.Char(string='Estado')


	def action_asociados_recomendar(self):
		obj_crm_asociados = self.env['trafitec.crm.asociados']
		return obj_crm_asociados.action_recomendar(self.cotizacion_id.id, self.cotizacion_linea_id.id)


	def action_asociados_recomendados(self):
		viajes_obj = self.env['trafitec.viajes']
		persona_obj = self.env['res.partner']
		obj_crm_asociados = self.env['trafitec.crm.asociados']
		# return obj.action_recomendar(self.cotizacion_linea_id.id)

		cotizacion_id = self.cotizacion_id.id
		cotizacion_municipio_origen_id = self.cotizacion_linea_id.municipio_origen_id.id
		cotizacion_municipio_destino_id = self.cotizacion_linea_id.municipio_destino_id.id

		cotizacion_estado_origen_id = self.cotizacion_linea_id.municipio_origen_id.state_sat_code.id
		cotizacion_estado_destino_id = self.cotizacion_linea_id.municipio_destino_id.state_sat_code.id

		# viajes_dat = viajes_obj.search([('origen.municipio.id', '=', cotizacion_municipio_origen_id), ('destino.municipio.id', '=', cotizacion_municipio_destino_id)])
		viajes_dat = viajes_obj.search([('origen.municipio.state_sat_code.id', '=', cotizacion_estado_origen_id),
		                                ('destino.municipio.state_sat_code.id', '=', cotizacion_estado_destino_id)])
		print("----VIAJES ENCONTRADOS--")
		print(viajes_dat)

		# Asociados recomendados de viajes.
		xids = []
		for v in viajes_dat:
			xids.append(v.asociado_id.id)

		# Asociados recomendados de usuario.
		porusuario = obj_crm_asociados.search([('linea_id', '=', self.cotizacion_linea_id.id)])
		for xu in porusuario:
			for ax in xu.asociado_id:
				xids.append(ax.id)

		# raise UserError(str(porusuario)+" Arreglo:"+str(xids))

		contexto = self._context
		filtro = []
		print("--CONTEXTO AL PRESIONAR BOTON--")
		# print(contexto)
		# print(self.ids)
		# filtro.append(('asociado', '=', True))
		filtro.append(('id', 'in', xids))

		# filtro.append(('asociado', '=', True))

		action_ctx = dict(self.env.context)
		view_id_kanban = self.env.ref('sli_trafitec.trafitec_crm_trafico_asociados_kanban').id
		view_id_form = self.env.ref('base.view_partner_form').id
		return {
			'name': 'Asociados recomendados (Folio: ' + str(self.cotizacion_id.name or '') + ' Tarifa:' + str(
				self.tarifa_a or '') + ' Origen:' + str(self.origen or '') + ' Destino:' + str(
				self.destino or '') + ')',
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'kanban,form',
			'res_model': 'res.partner',
			'views': [(view_id_kanban, 'kanban'), (view_id_form, 'form')],
			# 'form_view_ref': 'base.res_partner_kanban_view',
			# 'tree_view_ref': 'trafitec_crm_trafico_asociados_kanban',
			# 'kanban_view_ref': 'trafitec_crm_trafico_asociados_kanban',
			# 'tree_view_ref':'',
			# 'view_id': view_id,
			# 'view_ref': 'trafitec_crm_trafico_asociados_kanban',
			'target': 'current',
			# 'res_id': self.ids[0],
			# Parametros por contexto:
			'context': {
				'cotizacion_id': cotizacion_id,
				'municipio_origen_id': cotizacion_municipio_origen_id,
				'municipio_destino_id': cotizacion_municipio_destino_id
			},
			'domain': filtro
		}

