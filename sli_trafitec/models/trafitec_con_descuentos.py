# -*- coding: utf-8 -*-

from odoo import api, fields, models


class TrafitecConDescuentos(models.Model):
	_name = 'trafitec.con.descuentos'
	_description ='Descuentos'

	name = fields.Char(
		string='Concepto', 
		readonly=True
	)
	fecha = fields.Date(
		string='Fecha', 
		readonly=True
	)
	anticipo = fields.Float(
		string='Anticipo', 
		readonly=True
	)
	abonos = fields.Float(
		string='Abonos', 
		readonly=True
	)
	saldo = fields.Float(
		string='Saldo', 
		readonly=True
	)
	abono = fields.Float(
		string='Abono', 
		required=True
	)
	folio_viaje = fields.Char(
		string='Folio de viaje', 
		readonly=True
	)
	operador = fields.Char(
		string='Operador', 
		readonly=True
	)
	comentarios = fields.Text(
		string='Comentarios', 
		readonly=True
	)
	descuento_fk = fields.Many2one(
		'trafitec.descuentos', 
		string='Id del descuento', 
		required=True
	)
	linea_id = fields.Many2one(
		comodel_name='trafitec.contrarecibo', 
		string='Contrarecibo id', 
		ondelete='cascade'
	)
	viaje_id = fields.Many2one(
		'trafitec.viajes', 
		string='Viaje ID'
	)


	def _compute_cobrado(self):
		if self.linea_id.state != 'Nueva' :

			if self.linea_id.cobrar_descuentos == 'No cobrar':
				self.cobrado = False

			if self.linea_id.cobrar_descuentos == 'Todos':
				self.cobrado = True

			if self.linea_id.cobrar_descuentos == 'Viajes del contrarecibo':

				for viaje in self.linea_id.viaje_id:

					if self.viaje_id.id == viaje.id:
						self.cobrado = True
						break
					else:
						self.cobrado = False
		else:
			self.cobrado = False


	cobrado = fields.Boolean(
		string='Cobrado', 
		default=False, 
		compute='_compute_cobrado'
	)


	@api.onchange('abono')
	def _onchange_abono(self):
		if self.abono > self.saldo:
			self.abono = self.saldo
			res = {'warning': {
				'title': ('Advertencia'),
				'message': ('No puede poner un monto mayor de abono al saldo faltante.')
			}}

			return res


	@api.constrains('abono')
	def _check_abono(self):
		if self.abono <= 0:
			raise UserError(
				('Aviso !\nEl monto del abono debe ser mayor a cero.')
			)

