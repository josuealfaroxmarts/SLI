from odoo import models, fields, api

class TrafitecCrmTraficoRegistroViajes(models.Model):
	_name = 'trafitec.crm.trafico.registro.viajes'
	_description ='crm traficos registros viajes'

	registro_id = fields.Many2one(
		string='Registro', 
		comodel_name='trafitec.crm.trafico.registro'
	)
	viaje_id = fields.Many2one(
		string='Viaje', 
		comodel_name='trafitec.viajes', 
		required=True
	)

	@api.model
	def create(self, vals):
		nuevo = super(TrafitecCrmTraficoRegistroViajes, self).create(vals)
		nuevo.viaje_id.crm_trafico_registro_id = nuevo.id
		return nuevo


	def unlink(self):
		self.viaje_id.crm_trafico_registro_id = False
		borrado = super(TrafitecCrmTraficoRegistroViajes, self).unlink()
		return borrado
