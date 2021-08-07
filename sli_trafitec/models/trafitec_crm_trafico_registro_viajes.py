

class TrafitecCrmTraficoRegistroViajes(models.Model):
	_name = 'trafitec.crm.trafico.registro.viajes'
	_description ='crm traficos registros viajes'
	registro_id = fields.Many2one(string='Registro', comodel_name='trafitec.crm.trafico.registro')
	viaje_id = fields.Many2one(string='Viaje', comodel_name='trafitec.viajes', required=True)

	@api.model
	def create(self, vals):
		nuevo = super(trafitec_crm_trafico_registro_viajes, self).create(vals)
		nuevo.viaje_id.crm_trafico_registro_id = nuevo.id
		return nuevo


	def unlink(self):
		self.viaje_id.crm_trafico_registro_id = False
		borrado = super(trafitec_crm_trafico_registro_viajes, self).unlink()
		# self.viaje_id.write({'crm_trafico_registro_id', False})
		return borrado
