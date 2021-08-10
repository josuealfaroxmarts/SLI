import datetime
from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError


class TrafitecPagosMasivos(models.Model):
	_name = 'trafitec.pagosmasivos'
	_description = 'Pagos masivos'
	_order = 'id desc'
	_inherit = ['mail.thread', 'mail.activity.mixin']

	name = fields.Char(
		string='Folio', 
		default=''
	)
	persona_id = fields.Many2one(
		string='Persona',
		comodel_name='res.partner',
		required=True,
		domain=(
			[(['company','person'],'in','company_type'),'|',
			+ ('supplier','=',True),('customer','=',True)]
		),
		tracking=True
	)
	fecha = fields.Date(
		string='Fecha',
		default=datetime.datetime.now().today(),
		required=True,
		tracking=True
	)
	moneda_id = fields.Many2one(
		string='Moneda',
		comodel_name='res.currency',
		required=True,
		tracking=True
	)
	total = fields.Monetary(
		string='Total',
		default=0,
		currency_field='moneda_id',
		required=True,
		tracking=True
	)
	total_txt = fields.Char(
		string='Total texto cantidad', 
		default=''
	)
	total_txt_ver = fields.Char(
		string='Total texto',
		related='total_txt',
		default=''
	)
	facturas_id = fields.One2many(
		string='Facturas',
		comodel_name='trafitec.pagosmasivos.facturas',
		inverse_name='pagomasivo_id'
	)
	referencia = fields.Char(
		string='Referenccia',
		default='',
		required=True,
		tracking=True
	)
	detalles = fields.Char(
		string='Detalles', 
		default='', 
		tracking=True
	)
	diario_id = fields.Many2one(
		string='Diario',
		comodel_name='account.journal',
		required=True
	)
	tipo = fields.Selection([
			('noespecificado', '(No especificado)'),
			('proveedor', 'Proveedor'),
			('cliente', 'Cliente')
		],
		string='Tipo',
		default='noespecificado',
		required=True,
		tracking=True
	)
	state = fields.Selection([
			('nuevo', 'Nuevo'),
			('validado', 'Validado'),
			('aplicado', 'Aplicado'),
			('cancelado', 'Cancelado')
		],
		string='Estado',
		default='nuevo',
		required=True,
		tracking=True
	)
	busqueda_fecha_inicial = fields.Date(
		string='Búsqueda: Fecha inicial',
		default=datetime.datetime.now().today(),
		required=True
	)
	busqueda_fecha_final = fields.Date(
		string='Búsqueda: Fecha final',
		default=datetime.datetime.now().today(),
		required=True
	)

	def LlamarABatch(self):
		for rec in self:
			losids = []
			lasfids = []
			for invoice in rec.facturas_id:
				if invoice.factura_id.amount_residual > 0:
					losids.append(invoice.factura_id.id)
					lasfids.append({
						'id': invoice.factura_id.id,
						'receiving_amt': 1.1
					})
		return {
			'name': 'Pagos masivos X',
			'type': 'ir.actions.act_window',
			'type': 'ir.actions.act_window',
			'res_model': 'account.register.payments',
			'view_type': 'form', 'view_mode': 'form',
			'form_view_ref': 'action_invoice_invoice_batch_process',
			'target': 'new', 'multi': True,
			'context': {
				'move_ids': lasfids,
				'active_ids': losids,
				'active_model': 'account.move',
				'batch': True,
				'programacionpagosx': True
			}
		}

	@api.model
	def create(self, vals):
		if 'company_id' in vals:
			vals['name'] = self.env['ir.sequence'].with_context(
				force_company=vals['company_id']
			).next_by_code('Trafitec.PagosMasivos') or _('Nuevo')
		else:
			vals['name'] = self.env['ir.sequence'].next_by_code(
				'Trafitec.PagosMasivos'
			) or _('Nuevo')
		return super(TrafitecPagosMasivos, self).create(vals)

	def _aplicapago(
		self,
		diario_id,
		factura_id,
		abono,
		moneda_id,
		persona_id,
		tipo='supplier',
		subtipo='inbound'
	):
		for rec in self:
			if abono <= 0:
				return
			metodo = 2
			if subtipo == 'inbound':
				metodo = 1
			valores = {
				'journal_id': diario_id,
				'payment_method_id': metodo,
				'payment_date': datetime.datetime.now().date(),
				'communication': (
					'Pago desde codigo por:{} de tipo:{} desde '
					+ 'Pago masivo {}.'.format(str(abono), tipo, rec.name),
				),
				'move_ids': [(4, factura_id, None)],
				'payment_type': subtipo,
				'amount': abono,
				'currency_id': moneda_id,
				'partner_id': persona_id,
				'partner_type': tipo,
			}
			pago = self.env['account.payment'].create(valores)
			pago.post()

	def _aplicapago2(
		self,
		diario_id,
		abono,
		moneda_id,
		persona_id,
		tipo='supplier',
		subtipo='inbound'
	):
		for rec in self:
			if abono <= 0:
				return
			metodo = 2
			if subtipo == 'inbound':
				metodo = 1
			valores = {
				'journal_id': diario_id,
				'payment_method_id': metodo,
				'payment_date': datetime.datetime.now().date(),
				'communication': '',
				'move_ids': [],
				'payment_type': subtipo,
				'amount': abono,
				'currency_id': moneda_id,
				'partner_id': persona_id,
				'partner_type': tipo,
			}
			pago = self.env['account.payment'].create(valores)
			return pago.post()

	def action_validar(self):
		for rec in self:
			rec.write({'state': 'validado'})
			return
			error = False
			errores = ""
			total_abonos = 0
			# VALIDACIONES
			if rec.total <= 0:
				error = True
				errores += "El total debe ser mayor a cero.\n"
			if rec.referencia.strip() == "":
				error = True
				errores += "Debe especificar la referencia.\n"
			for f in rec.facturas_id:
				if f.abono == 0:
					continue
				if f.abono < 0:
					error = True
					errores += (
						"El abono de la factura {} debe ser mayor o "
						+ "igual a cero.\n".format(f.factura_id.name)
					)
				if f.abono > f.factura_saldo:
					error = True
					errores += (
						"Los abonos deben ser menores o iguales al "
						+ "saldo de la factura {}.".format(f.factura_id.name)
					)
				total_abonos = total_abonos + f.abono
			if total_abonos <= 0:
				error = True
				errores += "El total de abonos debe ser mayor a cero.\n"
			if total_abonos != rec.total:
				error = True
				errores += (
					"El total de abonos debe ser igual al total general.\n"
				)
			if error:
				raise UserError(_("Alerta..\n" + errores))
			tipo = ""
			tipo_persona = ""
			if rec.tipo == 'noespecificado':
				return
			if rec.tipo == 'proveedor':
				tipo = "in_invoice"
				tipo_persona = "supplier"
			if rec.tipo == 'cliente':
				tipo = "out_invoice"
				tipo_persona = "customer"
			rec._aplicapago2(
				rec.diario_id.id,
				rec.total,
				rec.moneda_id.id,
				rec.persona_id.id,
				tipo_persona
			)
			rec.write({'state': 'validado'})

	def action_cancelar(self):
		for rec in self:
			rec.write({'state': 'cancelado'})

	def action_distribuir(self):
		for rec in self:
			disponible = rec.total
			for invoice in rec.facturas_id:
				invoice.abono = 0
				if disponible > 0:
					if disponible >= invoice.factura_saldo:
						invoice.abono = invoice.factura_saldo
						disponible = disponible - invoice.abono
					else:
						invoice.abono = disponible
						disponible = 0
						break

	def action_cero(self):
		for rec in self:
			for invoice in rec.facturas_id:
				invoice.abono = 0

	def action_saldar(self):
		for rec in self:
			for invoice in self.facturas_id:
				invoice.abono = invoice.factura_saldo

	@api.onchange(
		'persona_id',
		'moneda_id',
		'tipo', 'busqueda_fecha_inicial',
		'busqueda_fecha_final'
	)
	def _onchange_persona_id(self):
		for rec in self:
			rec.CargaFacturas()

	def CargaFacturas(self):
		for rec in self:
			lista_clientes = []
			rec.facturas_id = []
			tipo = ""
			if not rec.persona_id or not rec.moneda_id:
				return

			if rec.tipo == 'noespecificado':
				return

			if rec.tipo == 'proveedor':
				tipo = "in_invoice"

			if rec.tipo == 'cliente':
				tipo = "out_invoice"
			facturas_cliente = self.env['account.move'].search([
					('partner_id', '=', rec.persona_id.id),
					('move_type', '=', tipo),
					('amount_residual', '>', 0),
					('state', '=', 'open'),
					('currency_id', '=', rec.moneda_id.id),
					('date', '>=', rec.busqueda_fecha_inicial),
					('date', '<=', rec.busqueda_fecha_final)
				],
				order='date asc'
			)
			for invoice in facturas_cliente:
				nuevo = {
					'pagomasivo_id': False,
					'moneda_id': invoice.currency_id.id,
					'factura_id': invoice.id,
					'factura_fecha': invoice.date,
					'factura_total': invoice.amount_total,
					'factura_saldo': invoice.amount_residual,
					'abono': 0
				}
				lista_clientes.append(nuevo)
			rec.facturas_id = lista_clientes