# -*- coding: utf-8 -*-

import base64
from odoo import models, fields, api, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from xml.dom import minidom


class AccountMove(models.Model):
	_inherit = 'account.move'
	_order = 'id desc'

	es_facturamanual = fields.Boolean(
		string='Es factura manual?',
		default= False
	)
	origen = fields.Char(string='Origen')
	destino = fields.Char(string='Destino')
	cliente_origen_id = fields.Many2one(
		'res.partner',
		string='Cliente origen',
		domain=[
			('customer', '=', True), 
			('parent_id', '=', False)
		]
	)
	domicilio_origen_id = fields.Many2one(
		'res.partner', 
		string='Domicilio origen',
		domain=[
			'|', ('parent_id', '=', cliente_origen_id), 
			('id', '=', cliente_origen_id)
		]
	)
	cliente_destino_id = fields.Many2one(
		'res.partner', 
		string='Cliente destino',
		domain=[
			('customer', '=', True), 
			('parent_id', '=', False)
		]
	)
	domicilio_destino_id = fields.Many2one(
		'res.partner', 
		string='Domicilio destino',
		domain=[
			'|', ('parent_id', '=', cliente_destino_id), 
			('id','=',cliente_destino_id)
		]
	)
	contiene = fields.Text(string='Contiene')
	lineanegocio = fields.Many2one(
		'trafitec.lineanegocio', 
		string='Linea de negocios'
	)
	placas_id = fields.Char(string='Vehiculo')
	operador_id = fields.Char(string='Operador')
	abonado = fields.Float(string='Abonado')
	pagada = fields.Boolean(string='Pagada')
	factura_encontrarecibo = fields.Boolean(string='Factura en contra recibo',)
	x_folio_trafitecw = fields.Char(string='Folio Trafitec Windows')
	es_cartaporte = fields.Boolean(
		string='Es carta porte',
		default=False
	)
	es_provision = fields.Boolean(string='Es provisión')
	contrarecibo_id = fields.Many2one(
		string='Contra recibo',
		comodel_name='trafitec.contrarecibo'
	)
	invoice_from_xml = fields.Many2one(
		'invoice.from.fletex',
		string='Factura XML',
		domain=[
			('clientId' ,'=', partner_id)
		]
	)
	abonos = fields.Float(
		string='Abonos', 
		compute=compute_abonos, 
		store=True, 
		help='Abonos a la factura.'
	)
	cliente_bloqueado = fields.Boolean(
		string='Cliente bloqueado', 
		compute=compute_bloqueado, 
		default=False, 
		help='Indica si el cliente esta bloqueado.'
	)


	@api.depends('amount_total', 'amount_residual')
	def compute_abonos(self):
		self.abonos = self.amount_total - self.amount_residual


	@api.depends('partner_id.bloqueado_cliente_bloqueado')
	def compute_bloqueado(self):
		self.cliente_bloqueado = (self.partner_id.bloqueado_cliente_bloqueado or False)
	

	@api.depends('viajes_id')
	def _compute_totales(self):
		totalflete = 0.0
		for v in self.viajes_id:
			viaje_dat = self.env['trafitec.viajes'].search([('id','=',v.id)])
			totalflete += viaje_dat.flete_cliente
		
		self.total_fletes = totalflete
	

	@api.depends('viajescp_id')
	def _compute_totalescp(self):
		totalflete = 0.0
		for v in self.viajescp_id:
			_logger.info('KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK')
			_logger.info(v.id)
			numbers = [int(temp)for temp in str(v.id).split() if temp.isdigit()]
			_logger.info(numbers)
			viaje_dat = self.env['trafitec.viajes'].search([('id', '=', numbers)])
			totalflete += viaje_dat.flete_asociado

		self.total_fletescp = totalflete


	@api.onchange('invoice_from_xml')
	def xml_invoice(self):
		if self.invoice_from_xml:
			self.documentos_archivo_xml = base64.b64decode(self.invoice_from_xml.invoiceXml)
			self.documentos_archivo_pdf = self.invoice_from_xml.invoicePdf
			self.documentos_nombre_pdf = 'Factura PDF de {} Folio viaje: {}.pdf'.format(self.invoice_from_xml.clientId.name, self.invoice_from_xml.shipmentId.name)
			xml = minidom.parseString(base64.b64decode(self.invoice_from_xml.invoiceXml))
			issuing = xml.getElementsByTagName('cfdi:Emisor')[0]
			id_account = self.env['account.analytic.account'].search([('name', '=', '11-701-0001')])
			product = self.env['product.product'].search([('name', '=', 'Flete')])
			tax_one = self.env['account.tax'].search([('amount', '=', 16.0000)])
			tax_two = self.env['account.tax'].search([('amount', '=', -4.0000)])
			taxes = [tax_one[0].id, tax_two[0].id]
			voucher = xml.getElementsByTagName('cfdi:Comprobante')[0]
			subtotal = voucher.getAttribute('SubTotal')
			self.amount_total = subtotal
			self.invoice_date = voucher.getAttribute('Fecha')
			concepts = []
			concepts_xml = xml.getElementsByTagName('cfdi:Conceptos')[0]
			concept_xml = xml.getElementsByTagName('cfdi:Concepto')
			for x in concept_xml:
				flete = {
					'id': False,
					'product_id': product.id,
					'name': x.getAttribute('Descripcion'),
					'quantity': x.getAttribute('Cantidad'),
					'analytic_account_id': id_account.id,
					'tax_ids': taxes,
					'price_unit': subtotal,
					'sistema': False,
					'price_subtotal': subtotal
				}
				concepts = flete
				break

			self.invoice_line_ids = [(0,0,concepts)]


	@api.depends('documentos_archivo_xml')
	def _compute_documentos_tiene_xml(self):
		if self.documentos_archivo_xml:
			self.documentos_tiene_xml = True
		else:
			self.documentos_tiene_xml = False


	@api.depends('documentos_archivo_pdf')
	def _compute_documentos_tiene_pdf(self):
		if self.documentos_archivo_pdf:
			self.documentos_tiene_pdf = True
			'''
			#url_path = url_path.decode(sys.getfilesystemencoding())
			obj = self.env['ir.attachment']Nombre
			values = dict(
				name=self.documentos_nombre_pdf,
				#datas_fname=self.documentos_nombre_pdf,
				url='',
				res_model='account.move',
				type='binary',
				db_datas=base64.b64decode(self.documentos_archivo_pdf),
			)
			
			obj.create(values)
			'''
		else:
			self.documentos_tiene_pdf = False


	def action_adjuntar_pdf(self):
		if not self.documentos_anexado_pdf:
			self.env['ir.attachment'].create(
				{
					'name': 'Carta porte del asociado pdf',
					'type': 'binary',
					'datas': self.documentos_archivo_pdf,
					'res_model': 'account.move',
					'res_id': self.id,
					'mimetype': 'application/x-pdf'
				}
			)

			self.documentos_anexado_pdf = True

		else:
			raise UserError(_('Alerta..\nEl archivo ya fue anexado.'))


	def action_adjuntar_xml(self):
		if not self.documentos_anexado_xml:
			self.env['ir.attachment'].create(
					{
						'name': 'Carta porte del asociado xml',
						'type': 'binary',
						'datas': self.documentos_archivo_xml,
						'res_model': 'account.move',
						'res_id': self.id,
						'mimetype': 'application/x-xml'
					}
			)

			self.documentos_anexado_xml = True

		else:
			raise UserError(_('Alerta..\nEl archivo ya fue anexado.'))
	

	def proceso_adjuntar_archivos(self, xid):
		if not xid:
			xid = 1000000

		facturas = self.env['account.move'].search(
			[
				'&','&', 
				('id', '>=', xid),
				('type', '=', 'in_invoice'),
				('state', 'in', ['open']), '|',
				('documentos_anexado_pdf', '=', False),
				('documentos_anexado_xml', '=', False)
			]
		)

		if not facturas:
			return

		for f in facturas:
			if not f.documentos_anexado_pdf and not f.documentos_archivo_pdf and not f.documentos_anexado_xml and not f.documentos_archivo_xml:
				continue

			if not f.documentos_anexado_pdf and f.documentos_archivo_pdf:
				self.env['ir.attachment'].create(
					{
						'name': 'Carta porte del asociado pdf',
						'type': 'binary',
						'datas': f.documentos_archivo_pdf,
						'res_model': 'account.move',
						'res_id': f.id,
						'mimetype': 'application/x-pdf'
					}
				)

				f.documentos_anexado_pdf = True

			if not f.documentos_anexado_xml and f.documentos_archivo_xml:
				self.env['ir.attachment'].create(
					{
						'name': 'Carta porte del asociado xml',
						'type': 'binary',
						'datas': f.documentos_archivo_xml,
						'res_model': 'account.move',
						'res_id': f.id,
						'mimetype': 'application/x-xml'
					}
				)

				f.documentos_anexado_xml = True

		'''
		#Enviar correo a las personas involucradas.
		asunto = 'sli_2611'  #Asunto del correo.
		contenido = 'http://odoo.sli.mx/web/login?db=sli_2611'  #Contenido del correo.
		contenido = 'http://odoo.sli.mx/web/login?id=1564&view_type=form&model=website.support.ticket&menu_id=956&action=1056&db=sli_2611'
		para = 'ds1@sli.mx' #La persona de contra recibos.
		valores = {
			'subject': asunto,
			'body_html': contenido,
			'email_to': para,
			'email_cc': ';',
			'email_from': 'info@sli.mx',
		}
		create_and_send_email = self.env['mail.mail'].create(valores).send()
		'''

	viajes_id = fields.Many2many(
		string='Viajes de trafitec', 
		comodel_name='trafitec.viajes'
	) #Mike
	viajescp_id = fields.Many2many(
		string='Viajes trafitec',
		comodel_name='trafitec.viajes',
		relation='trafitec_facturas_viajescp_rel'
	) #Mike
	tipo = fields.Selection(
		string='Tipo de factura', 
		selection=[
			('normal', 'Normal'), 
			('manual', 'Manual'), 
			('automatica','Automatica')
		], 
		default='normal'
	) #Mike
	total_fletes = fields.Float(
		string='Total fletes', 
		store=True, 
		compute='_compute_totales'
	)
	total_fletescp = fields.Float(
		string='Total de fletes', 
		store=True, 
		compute='_compute_totalescp'
	)
	tipo_contiene = fields.Selection(
		string='', 
		selection=[
			('ninguno', '(Ninguno)'), 
			('simple', 'Simple'), 
			('detallado','Detallado')
		], 
		default='simple'
	)
	documentos_id = fields.One2many(
		string='Documentos', 
		comodel_name='trafitec.facturas.documentos',
		inverse_name='factura_id'
	)
	documentos_archivo_pdf = fields.Binary(string='Archivos PDF')
	documentos_archivo_xml = fields.Binary(
		string='Archivos XML', 
		compute='_compute_documentos_tiene_xml'
	)
	documentos_nombre_pdf = fields.Char(
		string='Nombre de archivo PDF', 
		default=''
	)
	documentos_nombre_xml = fields.Char(
		string='Nombre de archivo XML', 
		default=''
	)
	documentos_tiene_pdf = fields.Boolean(
		string='Tiene PDF', 
		default=False, 
		compute='_compute_documentos_tiene_pdf', 
		store=True
	)
	documentos_tiene_xml = fields.Boolean(
		string='Tiene XML', 
		default=False, 
		compute='_compute_documentos_tiene_xml', 
		store=True
	)
	documentos_anexado_pdf = fields.Boolean(
		string='Anexado PDF', 
		default=False
	)
	documentos_anexado_xml = fields.Boolean(
		string='Anexado XML', 
		default=False
	)
	cancelacion_detalles = fields.Char('Motivo de cancelación')
	folios_boletas = fields.Char(
		string='Folios de boletas', 
		compute='_compute_folios_boletas', 
		help='Lista de folios de boletas de los viajes relacionados.'
	)


	@api.onchange('es_facturamanual', 'partner_id')
	def _onchange_partner_trafitec(self):
		if self.es_facturamanual == True:
			self.cliente_origen_id = self.partner_id
			self.domicilio_origen_id = self.partner_id
			self.cliente_destino_id = self.partner_id
			self.domicilio_destino_id = self.partner_id


	@api.onchange('partner_id')
	def _onchange_partner_trafitec(self):
		self.team_id = self.partner_id.equipoventa_id
		return


	def _agrega_conceptos_viaje(self, id, preceiounitario):
		if preceiounitario <= 0:
			return []
		empresa = self.env['res.company']._company_default_get('account.move')
		cfg = self.env['trafitec.parametros'].search([('company_id', '=', empresa.id)])
		conceptos = []
		impuestos = []

		# Obtener impuestos de venta del producto
		for i in cfg.product.taxes_id:
			impuestos.append(i.id)

		# Flete
		flete = {
			'id': False,
			'move_id': id,
			'product_id': cfg.product_invoice.id,
			'name': cfg.product.name,
			'quantity': 1, # Cantidad
			'account_id': cfg.product_invoice.property_account_income_id.id, # Plan contable
			'uom_id': cfg.product_invoice.uom_id.id, # Unidad de medida
			'price_unit': preceiounitario,
			'discount': 0,
			'invoice_line_tax_ids': impuestos,
			'sistema': False
		}
		conceptos.append(flete)

		return conceptos


	def _agrega_conceptos_cargos_viajes(self, id):
		conceptos=[]
		impuestos=[]

		# Cargo para cartas porte
		for v in self.viajescp_id:

			# Cargos adicionales
			cargos = self.env['trafitec.viaje.cargos'].search(
				[
					('line_cargo_id', '=', v.id),
					('tipo', 'in', ('pagar_cr_cobrar_f', 'pagar_cr_nocobrar_f')),
					('valor', '>', 0)
				]
			)
			for c in cargos:

				# Obtener impuestos del producto actual
				for i in c.name.product_id.supplier_taxes_id:
					impuestos.append(i.id)

				# Concepto
					cargo = {
						'id': False,
						'move_id': id,
						'product_id': c.name.product_id.id,
						'name': c.name.product_id.name,
						'quantity': 1,  # Cantidad.
						'account_id': c.name.product_id.property_account_expense_id.id, # Plan contable
						'uom_id': c.name.product_id.uom_id.id, # Unidad de medida
						'price_unit': c.valor,
						'discount': 0,
						'invoice_line_tax_ids': impuestos,
						'sistema': False
					}
				conceptos.append(cargo)

		# Cargo para factura de clientes
		for v in self.viajes_id:

			# Cargos adicionales
			cargos = self.env['trafitec.viaje.cargos'].search(
				[
					('line_cargo_id', '=', v.id),
					('tipo', 'in', ('pagar_cr_cobrar_f', 'nopagar_cr_cobrar_f')),
					('valor', '>', 0)
				]
			)
			
			for c in cargos:

				# Obtener impuestos del producto actual
				for i in c.name.product_id.taxes_id:
					impuestos.append(i.id)

				# Concepto
					cargo = {
						'id': False,
						'move_id': id,
						'product_id': c.name.product_id.id,
						'name': c.name.product_id.name,
						'quantity': 1,  # Cantidad.
						'account_id': c.name.product_id.property_account_income_id.id,  # Plan contable.
						'uom_id': c.name.product_id.uom_id.id,  # Unidad de medida.
						'price_unit': c.valor,
						'discount': 0,
						'invoice_line_tax_ids': impuestos,
						'sistema': False
					}
				conceptos.append(cargo)

		return conceptos

	
	def _agrega_conceptos_sistema(self):

		# Agregar conceptos existentes
		conceptos=[]
		for l in self.invoice_line_ids:
			if l.sistema == True:
				concepto = {
					'id': l.id,
					'move_id': l.move_id.id,
					'product_id': l.product_id.id,
					'name': l.name,
					'quantity': l.quantity, # Cantidad
					'account_id': l.account_id.id, # Plan contable
					'uom_id': l.uom_id.id, # Unidad de medida
					'price_unit': l.price_unit,
					'discount': l.discount,
					'invoice_line_tax_ids': l.invoice_line_tax_ids,
					'sistema': l.sistema
				}
				conceptos.append(concepto)

		return conceptos


	def _compute_folios_boletas(self):

		# Obtener los viajes relacionados de la factura
		folios = ''
		viajes_obj = self.env['trafitec.viajes']
		boletas_obj = self.env['trafitec.viajes.boletas']
		
		try:
			viajes_dat = viajes_obj.search([('factura_cliente_id', '=', self.id)])
			for v in viajes_dat:
				boletas_dat = boletas_obj.search([('linea_id', '=', v.id)])
				for b in boletas_dat:
					folios += (b.name or '') + ', '
		except:
		self.folios_boletas = folios
	

	@api.onchange('viajes_id')
	def _onchange_viajes(self):
		contiene = ''
		tons = 0
		productos = ''
		origenes = ''
		destinos = ''
		
		tarifa_ac = 0
		tarifa_an = 0
		
		origen_diferente=False
		origen_ac = ''
		origen_an = ''
		
		destino_diferente=False
		destino_ac = ''
		destino_an = ''

		producto_diferente=False
		producto_ac = ''
		producto_an = ''

		placas_diferente=False
		placas_ac = ''
		placas_an = ''
		placas = ''

		operadores_diferente=False
		operadores_ac = ''
		operadores_an = ''
		operadores = ''

		tarifas = ''
		c = 0

		if self.tipo == 'automatica':
			for v in self.viajes_id:
				c += 1
				tarifa_ac = v.tarifa_cliente or 0
				origen_ac = v.origen or ''
				destino_ac = v.destino or ''
				producto_ac = v.product.name or ''
				operadores_ac = v.operador_id.name or ''
				placas_ac = v.placas_id.license_plate or ''

				if c == 1:
					tarifa_an = tarifa_ac or 0
					origen_an = origen_ac or ''
					destino_an = destino_ac or ''
					producto_an = producto_ac or ''
					operadores_an = operadores_ac or ''
					placas_an = placas_ac or ''

				tarifas = '{:.2f}'.format(tarifa_ac)

				if tarifa_an != tarifa_ac:
					tarifas = 'Varias'
				
				if origen_an != origen_ac:
					origen_diferente = True
				
				if destino_an != destino_ac:
					destino_diferente = True
				
				if producto_an != producto_ac:
					producto_diferente = True

				if operadores_an != operadores_ac:
					operadores_diferente = True

				if placas_an != placas_ac:
					placas_diferente = True

				origenes = v.origen.name
				destinos = v.destino.name

				placas = v.placas_id.license_plate or ''
				operadores = v.operador_id.name or ''

				productos = v.product.name
				tons += (v.peso_origen_remolque_1 + v.peso_origen_remolque_2) / 1000

				tarifa_an = v.tarifa_cliente or 0
				origen_an = v.origen or ''
				destino_an = v.destino or ''
				producto_an = v.product.name or ''
				operadores_an = v.operador_id.name or ''
				placas_an = v.placas_id.license_plate or ''

			if origen_diferente:
				origenes = 'Varios'
			
			if destino_diferente:
				destinos = 'Varios'
			
			if producto_diferente:
				productos = 'Varios'

			if operadores_diferente:
				operadores = 'Varios'

			if placas_diferente:
				placas = 'Varios'

			self.origen = origenes
			self.destino = destinos
			self.operador_id = operadores
			self.placas_id = placas
			
			if tons > 0:
				contiene += 'Flete con: {:.3f} toneladas del producto(s): {}, con la tarifa: {} '.format(tons,productos,tarifas)
				self.contiene = contiene

			conceptos = []
			viajes = []
			cargos = []
			sistema = []

			# self.invoice_line_ids = []
			sistema = self._agrega_conceptos_sistema()
			viajes = self._agrega_conceptos_viaje(self._origin.id,self.total_fletes)
			cargos = self._agrega_conceptos_cargos_viajes(self._origin.id)

			self.invoice_line_ids = [] # Vaciar
			conceptos.extend(viajes)
			conceptos.extend(cargos)
			conceptos.extend(sistema)

			print('****Cargos:' + str(conceptos))

			self.invoice_line_ids = conceptos

		if self.tipo == 'manual' or self.tipo == 'automatica':

			if self.viajes_id and len(self.viajes_id) > 0:

				try:
					viaje1 = self.viajes_id[0]

					if viaje1.subpedido_id.linea_id.cotizacion_id.cliente_plazo_pago_id:
						self.payment_term_id = viaje1.subpedido_id.linea_id.cotizacion_id.cliente_plazo_pago_id.id
				except:
					pass


	@api.onchange('viajescp_id')
	def _onchange_viajescp(self):
		contiene = ''
		tons = 0
		productos = ''
		origenes = ''
		destinos = ''

		tarifa_ac = 0
		tarifa_an = 0

		origen_diferente = False
		origen_ac = ''
		origen_an = ''

		destino_diferente = False
		destino_ac = ''
		destino_an = ''

		producto_diferente = False
		producto_ac = ''
		producto_an = ''

		tarifas = ''
		c = 0

		if self.es_cartaporte:

			for v in self.viajescp_id:
				c += 1
				tarifa_ac = v.tarifa_cliente
				origen_ac = v.origen
				destino_ac = v.destino
				producto_ac = v.product.name

				if c == 1:
					tarifa_an = tarifa_ac
					origen_an = origen_ac
					destino_an = destino_ac
					producto_an = producto_ac

				tarifas = '{:.2f}'.format(tarifa_ac)

				if tarifa_an != tarifa_ac:
					tarifas = 'Varias'

				if origen_an != origen_ac:
					origen_diferente = True

				if destino_an != destino_ac:
					destino_diferente = True

				if producto_an != producto_ac:
					producto_diferente = True

				origenes = v.origen.name
				destinos = v.destino.name

				productos = v.product.name
				tons += (v.peso_origen_remolque_1 + v.peso_origen_remolque_2) / 1000
				tarifa_an = v.tarifa_cliente
				origen_an = v.origen
				destino_an = v.destino
				producto_an = v.product.name

			if origen_diferente:
				origenes = 'Varios'

			if destino_diferente:
				destinos = 'Varios'

			if producto_diferente:
				productos = 'Varios'

			self.origen = origenes
			self.destino = destinos

			conceptos = []

			# self.invoice_line_ids = []
			sistema = self._agrega_conceptos_sistema()
			viajes = self._agrega_conceptos_viaje(self._origin.id, self.total_fletes)
			cargos = self._agrega_conceptos_cargos_viajes(self._origin.id)

			self.invoice_line_ids = [] # Vaciar

			# conceptos.extend(viajes)
			conceptos.extend(cargos)
			conceptos.extend(sistema)

			print('****Cargos:' + str(conceptos))

			self.invoice_line_ids = conceptos


	# Al crear
	@api.model
	def create(self, vals):

		# Si es factura de cliente:
		cliente_obj = None
		cliente_dat = None
		
		# raise UserError(str(self._context))
		
		if self._context.get('type', 'out_invoice') == 'out_invoice':
			cliente_obj = self.env['res.partner']
			cliente_dat = cliente_obj.browse([vals.get('partner_id')])

			if cliente_dat:

				if cliente_dat.bloqueado_cliente_bloqueado:
					raise UserError(_('El cliente esta bloqueado, motivo: ' + (cliente_dat.bloqueado_cliente_clasificacion_id.name or '')))

		factura = super(trafitec_account_invoice, self).create(vals)

		return factura


	# Obtener los viajes relacionados con el documento
	def obtener_viajes(self):
		lista = []

		if self.id:
			sql = 'select trafitec_viajes_id from account_invoice_trafitec_viajes_rel where account_move_id=' + str(self.id)
			self.env.cr.execute(sql)
			viajessql = self.env.cr.fetchall()
			for v in viajessql:
				id = v[0]
				lista.append(id)

		return lista


	def viaje_facturado(self, id):
		viaje = self.env['trafitec.viajes'].search([('id','=',id)])

		if viaje.en_factura == False:
			return False

		return True


	def write(self, vals):
		factura = None
		for invoice in self:
			antes = []  # Lista de ids de los viajes antes de la actualizacion
			despues = []  # Lista de ids de los viajes despues de la actualizacion

			if invoice.tipo == 'manual' or invoice.tipo == 'automatica':
				antes = invoice.obtener_viajes()
			
			factura = super(trafitec_account_invoice, self).write(vals)

			if invoice.tipo == 'manual' or invoice.tipo == 'automatica':
				despues = invoice.obtener_viajes()

		return factura

	
	def action_invoice_open(self):
		error = False
		errores = ''
		
		cliente_nombre = ''
		cliente_saldo = 0
		cliente_limite_credito = 0
		prorroga_hay = False
		prorroga_fecha = None

		# INICIO VALIDACIONES:
		error = False
		errores = ''

		factura = self.env['account.move'].search([('id', '=', self.id)])

		if self.es_cartaporte:

			if not self.viajescp_id:
				raise ValidationError('Debe seleccionar al menos un viaje relacionado con la carta porte.')

			# Validacion general de los viajes
			for v in self.viajescp_id:
				vobj = self.env['trafitec.viajes'].search([('id', '=', v.id)])

				if v.asociado_id.id != self.partner_id.id:
					error = True
					errores += 'El asociado del viaje ' + (str(v.name)) + ' debe ser igual al de la factura.\r\n'

				if v.flete_asociado <= 0:
					error = True
					errores += 'El viaje ' + (str(v.name)) + ' deben tener el flete del asociado calculado.\r\n'

				if v.documentacion_completa == False:
					error = True
					errores += 'El viaje ' + (str(v.name)) + ' deben tener documentación completa.\r\n'

				if v.en_cp == True:
					error = True
					errores += 'El viaje ' + (str(v.name)) + ' ya tiene carta porte relacionada.\r\n'

		if self.tipo == 'automatica' or self.tipo == 'manual':

			if not self.lineanegocio:
				error = True
				errores += 'Debe especificar la línea de negocio.\r\n'

			if self.tipo == 'automatica':

				if not self.viajes_id:
					error = True
					errores += 'Debe especificar al menos un viaje relacionado con la factura de cliente.\r\n'

				totalflete = 0
				for v in self.viajes_id:
					totalflete += v.flete_cliente

				totalconceptos = 0
				for l in self.invoice_line_ids:
					totalconceptos += l.price_subtotal

				if totalflete <= 0:
					error = True
					errores += 'El total de flete de viajes debe ser mayor a cero.\r\n'

				if totalconceptos <= 0:
					error = True
					errores += 'El total de flete de los conceptos debe ser mayor a cero.\r\n'
				'''
				diferencia = totalflete - totalconceptos
				if abs(diferencia) >= 1:
					error = True
					errores += 'El total de flete {0:20,.2f} debe ser menor o igual al subtotal del documento {1:20,.2f}.\r\n'.format(
						totalflete, totalconceptos)
                '''

			'''	
			if self.tipo == 'manual':
				if self.cliente_origen_id.id == False:
					raise ValidationError(_('Aviso !\nEl cliente origen no debe estar vacio.'))
				if self.cliente_destino_id.id == False:
					raise ValidationError(_('Aviso !\nEl cliente destino no debe estar vacio.'))
				if self.domicilio_origen_id.id == False:
					raise ValidationError(_('Aviso !\nEl domicilio origen no debe estar vacio.'))
				if self.domicilio_destino_id.id == False:
					raise ValidationError(_('Aviso !\nEl domicilio destino no debe estar vacio.'))
				if self.origen == False:
					raise ValidationError(_('Aviso !\nEl origen no debe estar vacio.'))
				if self.destino == False:
					raise ValidationError(_('Aviso !\nEl destino no debe estar vacio.'))
			'''
			
			# Validacion general de los viajes
			for v in self.viajes_id:
				vobj = self.env['trafitec.viajes'].search([('id', '=', v.id)])

				if v.cliente_id.id != self.partner_id.id:
					error = True
					errores += 'El cliente del viaje ' + (str(v.name)) + ' debe ser igual al de la factura.\r\n'

				if v.flete_cliente <= 0:
					error = True
					errores += 'El viaje '+(str(v.name)) + ' debe tener el flete del cliente calculado.\r\n'

				if v.documentacion_completa == False:
					error = True
					errores += 'El viaje ' + (str(v.name)) + ' debe tener documentación completa.\r\n'

				if v.en_factura == True:
					error = True
					errores += 'El viaje ' + (str(v.name)) + ' ya esta relacionado con una factura.\r\n'

		if error:
			raise ValidationError(_('Alerta..\n' + errores))

		# FIN VALIDACIONES

		# El cliente con las funciones de saldo indicadas
		persona = self.env['res.partner']

		# aumentar el saldo de las facturas en el cliente
		saldo = self.partner_id.balance_invoices + self.amount_total
		saldo_restante = self.partner_id.limit_credit - saldo
		self.partner_id.write(
			{
				'balance_invoices': saldo, 
				'limit_credit_fletex': saldo_restante
			}
		)
		
		# --------------------------------------------------------------------------
		# EVALUAR CREDITO DEL CLIENTE
		# --------------------------------------------------------------------------
		try:
			cliente_nombre = self.partner_id.name
			cliente_saldo = persona.cliente_saldo_total(self.partner_id.id) + self.amount_total
			cliente_limite_credito = self.partner_id.limite_credito
			prorroga_hay = self.partner_id.prorroga
			if self.partner_id.fecha_prorroga:
				prorroga_fecha = datetime.datetime.strptime(self.partner_id.fecha_prorroga, '%Y-%m-%d').date()

			# print(cliente_nombre, cliente_saldo, cliente_limite_credito, prorroga_hay, prorroga_fecha)
			if self.type == 'out_invoice':

				if self._context.get('validar_credito_cliente', True):

					if cliente_saldo > cliente_limite_credito:

						if prorroga_hay:

							if prorroga_fecha and datetime.date.today() > prorroga_fecha:
								error = True
								errores += 'El cliente {} con saldo {:20,.2f} ha excedido su crédito {:20,.2f} por {:20,.2f} (Con prorroga).'.format(cliente_nombre, cliente_saldo, cliente_limite_credito,cliente_saldo - cliente_limite_credito)
						else:
							error = True
							errores += 'El cliente {} con saldo {:20,.2f} ha excedido su crédito {:20,.2f} por {:20,.2f} (Sin prorroga).'.format(cliente_nombre, cliente_saldo, cliente_limite_credito,cliente_saldo - cliente_limite_credito)
		except:

		for f in self:

			# Factura de cliente
			if self._context.get('type', 'out_invoice') == 'out_invoice':
				for v in f.viajes_id:
					vobj = self.env['trafitec.viajes'].search([('id', '=', v.id)])

					if vobj.en_factura:
						error = True
						errores += 'El viaje {} ya tiene factura cliente: {}.\r\n'.format(v.name, (v.factura_cliente_id.name or v.factura_cliente_id.name or ''))

			else: # Factura de proveedor
				for vcp in f.viajescp_id:
					vobj = self.env['trafitec.viajes'].search([('id', '=', vcp.id)])

					if vobj.en_cp:
						error = True
						errores += 'El viaje {} ya tiene carta porte: {}.\r\n'.format(vcp.name, (vcp.factura_proveedor_id.name or vcp.factura_proveedor_id.name or ''))

		if error:
			raise ValidationError(_(errores))

		# Estabelece cada viaje como Con factura de cafa viaje relacionado
		for f in self:

			# Es factura de cliente
			if self._context.get('type', 'out_invoice') == 'out_invoice':
				for v in f.viajes_id:
					v.with_context(validar_credito_cliente=False).write({'en_factura': True, 'factura_cliente_id': self.id})
			else: # Es factura de proveedor
				for v in f.viajescp_id:
					v.with_context(validar_credito_cliente=False).write({'en_cp': True, 'factura_proveedor_id': self.id})

		factura = super(trafitec_account_invoice, self).action_invoice_open()

		return factura

	# Al presionar boton cancelar
	

	def action_invoice_cancel(self):

		# Factura de cliente: Llamar al asistente de cancelacion para preguntar motivo
		if self._context.get('type', 'out_invoice') == 'out_invoice':
			view_id = self.env.ref('sli_trafitec.sli_trafitec_facturas_cancelar').id

			return {
				'name': _('Cancelar factura de cliente'),
				'type': 'ir.actions.act_window',
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'trafitec.facturas.cancelar',
				'views': [(view_id, 'form')],
				'view_id': view_id,
				'target': 'new',
				#'res_id': self.ids[0],
				'context': {
					'default_factura_id': self.id
				}
			}

		# Factura de proveedor
		else: # Factura de proveedor
			# raise UserError('Al cancelar factura proveedor!!')
			for f in self:
				f.factura_encontrarecibo = False
				f.contrarecibo_id = False
				
				if f.viajescp_id:
					for v in f.viajescp_id:
						v.with_context(validar_credito_cliente=False).write({'en_cp': False, 'factura_proveedor_id': False})
					f.viajescp_id = [(5, _, _)]

			factura = super(trafitec_account_invoice, self).action_invoice_cancel()

			return factura

	
	def action_liberar_viajes(self):
		self.ensure_one()

		if self.tipo != 'manual':
			raise UserError(_('La factura debe ser manual.'))
		
		# Establece el estado de Sin factura en cada viaje relacionado
		for v in self.viajes_id:
			if v.factura_cliente_id.id == self.id:
				v.with_context(validar_credito_cliente=False).write({'factura_cliente_id': False, 'en_factura': False})
	

	def action_relacionar_viajes(self):
		self.ensure_one()

		if self.tipo != 'manual':
			raise UserError(_('La factura debe ser manual.'))

		# Establece el estado de Sin factura en cada viaje relacionado
		for v in self.viajes_id:
			if v.factura_cliente_id.id == False:
				v.with_context(validar_credito_cliente=False).write({'factura_cliente_id': self.id, 'en_factura': True})
	

	def action_liberar_viajescp(self):

		# Establece el estado de Sin factura en cada viaje relacionado
		for f in self:
			viajes = self.env['trafitec.viajes'].search([('factura_proveedor_id', '=', f.id)])

			if len(viajes) <= 0:
				raise UserError(_('No se encontraron viajes relacionados.'))

			for v in viajes:
				v.with_context(validar_credito_cliente=False).write({'factura_proveedor_id': False, 'en_cp': False})

	# Despues de cancelar.. se puede mandar a borrador
	

	def action_invoice_draft(self):
		factura = super(trafitec_account_invoice, self).action_invoice_draft()

		return factura
