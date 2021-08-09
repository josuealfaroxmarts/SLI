# -*- coding: utf-8 -*-

from odoo import api, fields, models


class trafitec_comisiones_abono(models.Model):
	_name = 'trafitec.comisiones.abono'
	_description='comisiones abono'

	name = fields.Float(
		string='Abono', 
		required=True
	)
	fecha = fields.Date(
		string='Fecha', 
		required=True, 
		default=fields.Datetime.now
	)
	observaciones = fields.Text(string='Observaciones')
	tipo = fields.Selection(
		[
			('manual','Manual'), 
			('contrarecibo','Contra recibo')
		], 
		string='Tipo', 
		default='manual'
	)
	abonos_id = fields.Many2one(
		'trafitec.cargos', 
		ondelete='cascade'
	)
	contrarecibo_id = fields.Many2one(
		'trafitec.contrarecibo', 
		ondelete='restrict'
	)
	permitir_borrar = fields.Boolean(
		string='Permitir borrar', 
		default=False
	)


	def unlink(self):

		# if self.tipo == 'contrarecibo':
		# if self.permitir_borrar != False:
		#     raise UserError(_(
		#         'Aviso !\nNo se puede eleminar un abono de un contra recibo.'))
		if self.tipo == 'manual':
			obj = self.env['trafitec.con.comision'].search(
				[('cargo_id', '=', self.abonos_id.id), ('line_id.state', '=', 'Nueva')])
			for con in obj:
				res = con.saldo + self.name
				abonado = con.comision - res
				con.write({'saldo': res, 'abonos': abonado})

		return super(trafitec_comisiones_abono, self).unlink()


	@api.constrains('name')
	def _check_abono(self):
		if self.name <= 0:
			raise UserError(
				('Aviso !\nEl monto del abono debe ser mayor a cero.')
			)


	@api.constrains('name')
	def _check_monto_mayor(self):
		obj_abono = self.env['trafitec.comisiones.abono'].search([('abonos_id', '=', self.abonos_id.id)])
		amount = 0
		for abono in obj_abono:
			amount += abono.name

		if amount > self.abonos_id.monto:
			raise UserError(
				('Aviso !\nEl monto de abonos ha sido superado al monto de la comision.')
			)


	@api.model
	def create(self, vals):
		id =  super(trafitec_comisiones_abono, self).create(vals)

		if 'tipo' in vals:
			tipo = vals['tipo']
		else:
			tipo = 'manual'

		valores = {
			'comision_abono_id' : id.id,
			'monto': vals['name'],
			'detalle': vals['observaciones'],
			'cobradoen' : 'Comision {}'.format(tipo)
		}
		self.env['trafitec.abonos'].create(valores)

		if tipo == 'manual':
			obj = self.env['trafitec.con.comision'].search([('cargo_id', '=', vals['abonos_id']), ('line_id.state','=','Nueva')])
			for con in obj:
				res = con.saldo - vals['name']
				abonado = con.comision - res
				con.write({'saldo':res, 'abonos': abonado})

		return id


	def write(self, vals):
		if 'name' in vals:
			monto = vals['name']
		else:
			monto = self.name

		if 'observaciones' in vals:
			detalle = vals['observaciones']
		else:
			detalle = self.observaciones

		valores = {
			'monto': monto,
			'detalle': detalle
		}
		obj = self.env['trafitec.abonos'].search([('comision_abono_id', '=', self.id)])
		obj.write(valores)

		if self.tipo == 'manual' and 'name' in vals:
			obj = self.env['trafitec.con.comision'].search([('cargo_id', '=', self.abonos_id.id), ('line_id.state', '=', 'Nueva')])
			for con in obj:

				if self.name > vals['name']:
					res = con.saldo + (self.name - vals['name'])
				else:
					res = con.saldo - (vals['name'] - self.name)

				abonado = con.comision - res
				con.write({'saldo': res, 'abonos': abonado})

		return super(trafitec_comisiones_abono, self).write(vals)
		