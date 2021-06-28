## -*- coding: utf-8 -*-
from odoo import models, fields, api, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import logging
import datetime
from xml.dom import minidom

import base64
_logger = logging.getLogger(__name__)


class trafitec_account_invoice(models.Model):
	_inherit = 'account.invoice'
	_order = 'id desc'

	es_facturamanual = fields.Boolean(string='Es factura manual?',default= False)
	origen = fields.Char(string='Origen')
	destino = fields.Char(string='Destino')
	cliente_origen_id = fields.Many2one('res.partner', string="Cliente origen",
										domain="[('customer','=',True), ('parent_id', '=', False)]")
	domicilio_origen_id = fields.Many2one('res.partner', string="Domicilio origen",
										  domain="['|',('parent_id', '=', cliente_origen_id),('id','=',cliente_origen_id)]")
	cliente_destino_id = fields.Many2one('res.partner', string="Cliente destino",
										 domain="[('customer','=',True), ('parent_id', '=', False)]")
	domicilio_destino_id = fields.Many2one('res.partner', string="Domicilio destino",
										   domain="['|',('parent_id', '=', cliente_destino_id),('id','=',cliente_destino_id)]")
	contiene = fields.Text(string='Contiene')
	lineanegocio = fields.Many2one('trafitec.lineanegocio', string='Linea de negocios')
	placas_id = fields.Char(string='Vehiculo')
	operador_id = fields.Char(string='Operador')
	abonado = fields.Float(string='Abonado')
	pagada = fields.Boolean(string='Pagada', default=False)
	factura_encontrarecibo = fields.Boolean(string='Factura en contra recibo',default=False)
	x_folio_trafitecw = fields.Char(string="Folio Trafitec Windows")
	es_cartaporte = fields.Boolean(string='Es carta porte', default=False,help='Indica si la factura es una factura de flete (Carta porte).')
	es_provision = fields.Boolean(string='Es provisión', default=False, help='Indica si la factura esta provisionada.')
	contrarecibo_id = fields.Many2one(string='Contra recibo', comodel_name='trafitec.contrarecibo')
	invoice_xml = fields.Many2one('invoice.fletex', string="Factura XML", domain="[('clientId' ,'=', partner_id)]", compute='xml_invoice')

	
	@api.depends('amount_total', 'residual')
	def compute_abonos(self):
		self.abonos = self.amount_total-self.residual

	abonos = fields.Float(string="Abonos", compute=compute_abonos, store=True, help='Abonos a la factura.')

	
	@api.depends('partner_id.bloqueado_cliente_bloqueado')
	def compute_bloqueado(self):
		self.cliente_bloqueado = (self.partner_id.bloqueado_cliente_bloqueado or False)
	
	cliente_bloqueado = fields.Boolean(string='Cliente bloqueado', compute=compute_bloqueado, default=False, help='Indica si el cliente esta bloqueado.')

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
			viaje_dat = self.env['trafitec.viajes'].search([('id', '=', v.id)])
			totalflete += viaje_dat.flete_asociado

		self.total_fletescp = totalflete

	@api.onchange('invoice_xml')
	def xml_invoice(self):
		if self.invoice_xml:
			self.documentos_archivo_xml = base64.b64decode(self.invoice_xml.invoiceXml)
			xml = minidom.parseString(base64.b64decode(self.invoice_xml.invoiceXml))
			issuing = xml.getElementsByTagName('cfdi:Emisor')[0]
			id_distributor = self.env['res.partner'].search([('name', '=', issuing.getAttribute('Nombre'))])
			id_account = self.env['account.account'].search([('code', '=', '11-701-0001')])
			self.partner_id = id_distributor.id
			self.reference = id_distributor.name
			voucher = xml.getElementsByTagName('cfdi:Comprobante')[0]
			self.date_invoice = voucher.getAttribute('Fecha')
			concepts = []
			concepts_xml = xml.getElementsByTagName('cfdi:Conceptos')[0]
			concept_xml = xml.getElementsByTagName('cfdi:Concepto')
			for x in concept_xml:
				flete = {
					'id': False,
					'name': x.getAttribute('Descripcion'),
					'quantity': x.getAttribute('Cantidad'),
					'account_id': id_account.id,
					'price_unit': 15000,
					'sistema': False
				}
				concepts.append(flete)
			self.invoice_line_ids = concepts

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
			"""
			#url_path = url_path.decode(sys.getfilesystemencoding())
			obj = self.env['ir.attachment']Nombre
			values = dict(
				name=self.documentos_nombre_pdf,
				#datas_fname=self.documentos_nombre_pdf,
				url="",
				res_model='account.invoice',
				type='binary',
				db_datas=base64.b64decode(self.documentos_archivo_pdf),
			)
			
			obj.create(values)
			"""
		else:
			self.documentos_tiene_pdf = False


	
	def action_adjuntar_pdf(self):
		if not self.documentos_anexado_pdf:
			self.env['ir.attachment'].create(
				{
				'name': 'Carta porte del asociado pdf',
				'type': 'binary',
				'datas': self.documentos_archivo_pdf,
				'res_model': 'account.invoice',
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
				 'res_model': 'account.invoice',
				 'res_id': self.id,
				 'mimetype': 'application/x-xml'
				}
			)
			self.documentos_anexado_xml = True
		else:
			raise UserError(_('Alerta..\nEl archivo ya fue anexado.'))

	
	def proceso_adjuntar_archivos(self, xid):
		print("Ejecutando: proceso_adjuntar_archivos: Id incial: "+str(xid))

		if not xid:
			xid = 1000000

		#Obtener las facturas.
		facturas = self.env['account.invoice'].search(['&','&', ('id', '>=', xid), ('type', '=', 'in_invoice'), ('state', 'in', ['open']), '|', ('documentos_anexado_pdf', '=', False), ('documentos_anexado_xml', '=', False)])
		#facturas=self.env['account.invoice'].search(['&', '|', ('id', '>=', xid), '&', ('documentos_tiene_pdf', '=', True), ('documentos_anexado_pdf', '=', False), '&', ('documentos_tiene_xml', '=', True), ('documentos_anexado_xml', '=', False)])

		if not facturas:
			print("No hay facturas para procesar.")
			return

		print("Facturas N:" + str(len(facturas)))
		#Recorrer las facturas.
		for f in facturas:
			#Evita las facturas.
			if not f.documentos_anexado_pdf and not f.documentos_archivo_pdf and not f.documentos_anexado_xml and not f.documentos_archivo_xml:
				continue
			
			#Adjuntar archivos..
			print("Factura: "+str(f.id)+" N:"+str(len(facturas)))
			if not f.documentos_anexado_pdf and f.documentos_archivo_pdf:
				self.env['ir.attachment'].create(
					{
						'name': 'Carta porte del asociado pdf',
						'type': 'binary',
						'datas': f.documentos_archivo_pdf,
						'res_model': 'account.invoice',
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
						'res_model': 'account.invoice',
						'res_id': f.id,
						'mimetype': 'application/x-xml'
					}
				)
				f.documentos_anexado_xml = True
		print("Terminado: proceso_adjuntar_archivos")
		"""
		#Enviar correo a las personas involucradas.
		asunto = "sli_2611"  #Asunto del correo.
		contenido = "http://odoo.sli.mx/web/login?db=sli_2611"  #Contenido del correo.
		contenido = "http://odoo.sli.mx/web/login?id=1564&view_type=form&model=website.support.ticket&menu_id=956&action=1056&db=sli_2611"
		para = "ds1@sli.mx" #La persona de contra recibos.
		valores = {
			'subject': asunto,
			'body_html': contenido,
			'email_to': para,
			'email_cc': ';',
			'email_from': 'info@sli.mx',
		}
		create_and_send_email = self.env['mail.mail'].create(valores).send()
		"""

	viajes_id = fields.Many2many(string='Viajes de trafitec', comodel_name='trafitec.viajes') #Mike
	viajescp_id = fields.Many2many(
		string='Viajes de trafitec',
		comodel_name='trafitec.viajes',
		relation='trafitec_facturas_viajescp_rel'
	) #Mike
	tipo = fields.Selection(string='Tipo de factura', selection=[('normal', 'Normal'), ('manual', 'Manual'), ('automatica','Automatica')], default='normal') #Mike
	total_fletes = fields.Float(string="Total de fletes", store=True, compute='_compute_totales')
	total_fletescp = fields.Float(string="Total de fletes", store=True, compute='_compute_totalescp')
	tipo_contiene = fields.Selection(string="", selection=[('ninguno', '(Ninguno)'), ('simple', 'Simple'), ('detallado','Detallado')], default='simple')

	"""
	
	@api.onchange('viajescp_id')
	def onchange_viajescp_id(self):
		for rec in self:
			for v in rec.viajescp_id:
				v.write({'en_cp': True})
		
		for rec in self:
			lista_quitar = []
			lista_poner = []
			_logger.info('************viajescp_id:: '+str(rec.viajescp_id)+' Origin:: '+str(self._origin.viajescp_id))
			for o in self._origin.viajescp_id:
				if not o in rec.viajescp_id:
					_logger.info("**No esta, si estaba, se quito. "+str(o))
					#o.write({'en_cp': False})
					lista_quitar.append(o.id)

			for a in rec.viajescp_id:
				if not a in self._origin.viajescp_id:
					_logger.info("**No esta, no estaba, se agrego. "+str(a))
					#a.write({'en_cp': True})
					lista_poner.append(a.id)
		self.actualiza_concp(lista_quitar, lista_poner)
        
		
	def actualiza_concp(self, lista_quitar, lista_poner):
		for lp in lista_poner:
			viaje = self.env['trafitec.viajes'].browse([lp])
			viaje.write({'en_cp': True})

		for lq in lista_quitar:
			viaje = self.env['trafitec.viajes'].browse([lq])
			viaje.write({'en_cp': False})
    """
	
	#DOCUMENTOS.
	documentos_id = fields.One2many(string="Documentos", comodel_name="trafitec.facturas.documentos",
								   inverse_name="factura_id")
	documentos_archivo_pdf = fields.Binary(string = "Archivo PDF")
	documentos_archivo_xml = fields.Binary(string = "Archivo XML", compute='_compute_documentos_tiene_xml')
	
	documentos_nombre_pdf = fields.Char(string = "Nombre de archivo PDF", default="")
	documentos_nombre_xml = fields.Char(string = "Nombre de archivo XML", default="")
	
	documentos_tiene_pdf = fields.Boolean(string = "Tiene PDF", default=False,compute="_compute_documentos_tiene_pdf", store=True)
	documentos_tiene_xml = fields.Boolean(string = "Tiene XML", default=False, compute="_compute_documentos_tiene_xml", store=True)
	
	documentos_anexado_pdf = fields.Boolean(string = "Anexado PDF", default=False)
	documentos_anexado_xml = fields.Boolean(string = "Anexado XML", default=False)


	cancelacion_detalles = fields.Char('Motivo de cancelación')

	folios_boletas = fields.Char(string = "Folios de boletas", compute='_compute_folios_boletas', help='Lista de folios de boletas de los viajes relacionados.')

	#@api.constrains('viajes_id', 'viajescp_id', 'invoice_line_ids', 'es_cartaporte', 'tipo', 'state', 'total_fletes', 'amount_untaxed', 'es_facturamanual','cliente_origen_id','domicilio_origen_id','cliente_destino_id','domicilio_destino_id','origen','destino','lineanegocio')
	#def _check_trafic_factura(self):


	@api.onchange('es_facturamanual','partner_id')
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
	
	
	
	"""
	@api.onchange('payment_term_id', 'date_invoice')
	def _onchange_payment_term_date_invoice(self):
		date_invoice = self.date_invoice
		if not date_invoice:
			date_invoice = fields.Date.context_today(self)
		if not self.payment_term_id:
			# When no payment term defined
			self.date_due = self.date_due or date_invoice
		else:
			
			#Obtener los de la cotizacion.
			pterm = self.payment_term_id
			pterm_list = \
			pterm.with_context(currency_id=self.company_id.currency_id.id).compute(value=1, date_ref=date_invoice)[0]
			self.date_due = max(line[0] for line in pterm_list)
	"""
	
	
	def _agrega_conceptos_viaje(self,id,preceiounitario):
		if preceiounitario<=0:
			return []
		empresa = self.env['res.company']._company_default_get('account.invoice')
		cfg = self.env['trafitec.parametros'].search([('company_id', '=', empresa.id)])

		conceptos = []
		impuestos = []

		#Obtener impuestos de venta del producto.
		for i in cfg.product.taxes_id:
			impuestos.append(i.id)

		#Flete.
		flete = {
			'id': False,
			'invoice_id': id,
			'product_id': cfg.product_invoice.id,
			'name': cfg.product.name,
			'quantity': 1,# Cantidad.
			'account_id': cfg.product_invoice.property_account_income_id.id,#Plan contable.
			'uom_id': cfg.product_invoice.uom_id.id,#Unidad de medida.
			'price_unit': preceiounitario,
			'discount': 0,
			'invoice_line_tax_ids': impuestos,
			'sistema': False
		}

		conceptos.append(flete)

		return conceptos


	#return { 'warning': {'title': 'Product error', 'message':warning_message} }
	#@api.onchange('invoice_line_ids')
	#def _onchange_lines(self):
		#self.invoice_line_ids=self._origin.invoice_line_ids
		#print("****Self ids:"+str(self.invoice_line_ids)+" _origin: "+str(self._origin.invoice_line_ids))
		#return {'warning': {'title': 'Error', 'message': 'Cambio'}}
		#for co in self._origin.invoice_line_ids:
		#    if co not in self.invoice_line_ids:

   




	
	def _agrega_conceptos_cargos_viajes(self, id):
		conceptos=[]
		impuestos=[]

		#Cargo para cartas porte.
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
				#Obtener impuestos del producto actual.
				for i in c.name.product_id.supplier_taxes_id:
					impuestos.append(i.id)

				#Concepto.
				cargo = {
				 'id': False,
				 'invoice_id': id,
				 'product_id': c.name.product_id.id,
				 'name': c.name.product_id.name,
				 'quantity': 1,  # Cantidad.
				 'account_id': c.name.product_id.property_account_expense_id.id,  # Plan contable.
				 'uom_id': c.name.product_id.uom_id.id,  # Unidad de medida.
				 'price_unit': c.valor,
				 'discount': 0,
				 'invoice_line_tax_ids': impuestos,
				 'sistema': False
				}
				conceptos.append(cargo)

		#Cargo para factura de clientes.
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
				#Obtener impuestos del producto actual.
				for i in c.name.product_id.taxes_id:
					impuestos.append(i.id)

				#Concepto.
				cargo = {
				 'id': False,
				 'invoice_id': id,
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
		# Agregar conceptos existentes.
		conceptos=[]
		for l in self.invoice_line_ids:
			if l.sistema == True:
				concepto = {
					'id': l.id,
					'invoice_id': l.invoice_id.id,
					'product_id': l.product_id.id,
					'name': l.name,
					'quantity': l.quantity,  # Cantidad.
					'account_id': l.account_id.id,  # Plan contable.
					'uom_id': l.uom_id.id,  # Unidad de medida.
					'price_unit': l.price_unit,
					'discount': l.discount,
					'invoice_line_tax_ids': l.invoice_line_tax_ids,
					'sistema': l.sistema
				}
				conceptos.append(concepto)
		return conceptos

	
	def _compute_folios_boletas(self):
		#Obtener los viajes relacionados de la factura.
		folios = ""
		
		viajes_obj = self.env['trafitec.viajes']
		boletas_obj = self.env['trafitec.viajes.boletas']
		
		try:
			viajes_dat = viajes_obj.search([('factura_cliente_id', '=', self.id)])
			for v in viajes_dat:
				boletas_dat = boletas_obj.search([('linea_id', '=', v.id)])
				for b in boletas_dat:
					folios += (b.name or '') + ', '
		except:
			print("**Error al obtener los folios de las boletas.")
		
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
			   c+=1
			   tarifa_ac=v.tarifa_cliente or 0
			   origen_ac=v.origen or ''
			   destino_ac=v.destino or ''
			   producto_ac=v.product.name or ''
			   operadores_ac=v.operador_id.name or ''
			   placas_ac=v.placas_id.license_plate or ''

			   if c==1:
				  tarifa_an=tarifa_ac or 0
				  origen_an=origen_ac or ''
				  destino_an=destino_ac or ''
				  producto_an=producto_ac or ''
				  operadores_an=operadores_ac or ''
				  placas_an=placas_ac or ''


			   tarifas='{:.2f}'.format(tarifa_ac)
			   if tarifa_an!=tarifa_ac:
				  tarifas='Varias'
			   
			   if origen_an!=origen_ac:
				  origen_diferente=True
			   
			   if destino_an!=destino_ac:
				  destino_diferente=True
			   
			   if producto_an!=producto_ac:
				  producto_diferente=True

			   if operadores_an!=operadores_ac:
				  operadores_diferente=True

			   if placas_an!=placas_ac:
				  placas_diferente=True

			   origenes=v.origen.name
			   destinos=v.destino.name

			   placas = v.placas_id.license_plate or ''
			   operadores = v.operador_id.name or ''

			   productos=v.product.name
			   tons+=(v.peso_origen_remolque_1+v.peso_origen_remolque_2)/1000

			   tarifa_an=v.tarifa_cliente or 0
			   origen_an=v.origen or ''
			   destino_an=v.destino or ''
			   producto_an=v.product.name or ''
			   operadores_an=v.operador_id.name or ''
			   placas_an=v.placas_id.license_plate or ''


		   if origen_diferente:
			  origenes="Varios"
		   
		   if destino_diferente:
			  destinos="Varios"
		   
		   if producto_diferente:
			  productos="Varios"

		   if operadores_diferente:
			  operadores="Varios"

		   if placas_diferente:
			  placas="Varios"

		   self.origen=origenes
		   self.destino=destinos
		   self.operador_id = operadores
		   self.placas_id = placas
		   
		   if tons>0:
			 contiene += 'Flete con: {:.3f} toneladas del producto(s): {}, con la tarifa: {} '.format(tons,productos,tarifas)
			 self.contiene=contiene

		   conceptos=[]
		   viajes=[]
		   cargos=[]
		   sistema=[]

		   #self.invoice_line_ids = []
		   sistema=self._agrega_conceptos_sistema()
		   viajes=self._agrega_conceptos_viaje(self._origin.id,self.total_fletes)
		   cargos=self._agrega_conceptos_cargos_viajes(self._origin.id)

		   self.invoice_line_ids=[] #Vaciar.
		   conceptos.extend(viajes)
		   conceptos.extend(cargos)
		   conceptos.extend(sistema)

		   print("****Cargos:"+str(conceptos))

		   self.invoice_line_ids = conceptos

		if self.tipo == 'manual' or self.tipo == 'automatica':
			if self.viajes_id and len(self.viajes_id) > 0:
				try:
					viaje1 = self.viajes_id[0]
					#print("---VIAJE1---")
					#print(viaje1)
					if viaje1.subpedido_id.linea_id.cotizacion_id.cliente_plazo_pago_id:
						self.payment_term_id = viaje1.subpedido_id.linea_id.cotizacion_id.cliente_plazo_pago_id.id
				except:
					print("TRAFITEC: Error al calcula la fecha de vencimiento de la factura de cliente.")

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
				origenes = "Varios"

			if destino_diferente:
				destinos = "Varios"

			if producto_diferente:
				productos = "Varios"

			self.origen = origenes
			self.destino = destinos

			#if tons > 0:
				#contiene += 'Flete con: {:.3f} toneladas del producto(s): {}, con la tarifa: {} '.format(tons,
				#self.contiene = contiene

			conceptos = []
			viajes = []
			cargos = []
			sistema = []

			# self.invoice_line_ids = []
			sistema = self._agrega_conceptos_sistema()
			viajes = self._agrega_conceptos_viaje(self._origin.id, self.total_fletes)
			cargos = self._agrega_conceptos_cargos_viajes(self._origin.id)

			self.invoice_line_ids = []  # Vaciar.
			#conceptos.extend(viajes)
			conceptos.extend(cargos)
			conceptos.extend(sistema)

			print("****Cargos:" + str(conceptos))

			self.invoice_line_ids = conceptos

	#Nuevo.
	@api.model
	def default_get(self, fields_list):
		print("***XGET***")
		factura = super(trafitec_account_invoice, self).default_get(fields_list)
		return factura

	#Al crear.
	@api.model
	def create(self, vals):
		#Si es factura de cliente:
		cliente_obj = None
		cliente_dat = None
		
		#raise UserError(str(self._context))
		
		if self._context.get('type', 'out_invoice') == 'out_invoice':
			cliente_obj = self.env['res.partner']
			cliente_dat = cliente_obj.browse([vals.get('partner_id')])
			if cliente_dat:
				if cliente_dat.bloqueado_cliente_bloqueado:
					raise UserError(_('El cliente esta bloqueado, motivo: ' + (cliente_dat.bloqueado_cliente_clasificacion_id.name or '')))
        

		factura = super(trafitec_account_invoice, self).create(vals)
		print("******Self factura al crear:"+str(self))
		print("******Factura factura al crear:"+str(factura))
		#Relaciona el viaje con la factura del cliente.
		#for v in factura.viajes_id:
		#    v.write({'factura_cliente_id':factura.id,'en_factura':True})
		
		
		return factura

	#Obtener los viajes relacionados con el documento.
	def obtener_viajes(self):
		print("*******************Actualizar viajes....")
		lista=[]
		if self.id:
			sql = "select trafitec_viajes_id from account_invoice_trafitec_viajes_rel where account_invoice_id=" + str(self.id)
			self.env.cr.execute(sql)
			viajessql = self.env.cr.fetchall()
			for v in viajessql:
				id = v[0]
				lista.append(id)
		return lista

	def viaje_facturado(self,id):
		viaje=self.env['trafitec.viajes'].search([('id','=',id)])
		if viaje.en_factura==False:
			return False
		return True

	def _viajes_actualizaestado(self,factura_id):
		#BD-----------------------------------------------------------------------------------------------------
		  #Todos los viajes de la bd:
		  #viajes=self.env['trafitec.viajes'].search([])

		  #Todos los viajes (Ids) de la bd:
		  #viajes_ids=self.env['trafitec.viajes'].search([]).ids

		#MEMORIA-----------------------------------------------------------------------------------------------------
		  #Todos los viajes de memoria:
		  #viajes=self.viajes_id

		  #Todos los viajes (Ids) en memoria:
		  #viajes_ids=self.viajes_id.ids

		#Todos los ids relacionados del documento actual.
		#print(">>>>>>Ids de viajes"+str(self.viajes_id.ids))
		#print(">>>>>>Viajes bd"+str(viajes))
		#print(">>>>>>Viajes Ids"+str(viajes_ids))
		print("")
		#viajesbd_ids=self.env['trafitec.viajes'].search([('factura_cliente_id','=',factura_id)]).ids
		#viajesme_ids=self.viajes_id.ids

	
	def write(self,vals):
		factura=None
		for invoice in self:
			antes = []  # Lista de ids de los viajes antes de la actualizacion.
			despues = []  # Lista de ids de los viajes despues de la actualizacion.
			if invoice.tipo == "manual" or invoice.tipo == "automatica":
				antes = invoice.obtener_viajes()
			
			factura = super(trafitec_account_invoice, self).write(vals)

			if invoice.tipo == "manual" or invoice.tipo == "automatica":
				despues = invoice.obtener_viajes()

			"""
			#print("Context: "+str(self.env.context))
			if invoice.tipo == "manual" or invoice.tipo == "automatica":
				# Se quitaron:
				for va in antes:
					if va not in despues:
						vo = self.env['trafitec.viajes'].search([('id', '=', va)])
						vo.write({'factura_cliente_id': False, 'en_factura': False})

				# Se pusieron:
				for vd in despues:
					if vd not in antes:
						vo = self.env['trafitec.viajes'].search([('id', '=', vd)])
						vo.write({'factura_cliente_id': invoice.id, 'en_factura': True})
		    """
		return factura

	
	def action_invoice_open(self):
		error = False
		errores = ""
		
		cliente_nombre = ""
		cliente_saldo = 0
		cliente_limite_credito = 0
		prorroga_hay = False
		prorroga_fecha = None

		#INICIO VALIDACIONES
		error = False
		errores = ""

		factura = self.env['account.invoice'].search([('id', '=', self.id)])

		if self.es_cartaporte:
			if not self.viajescp_id:
				raise ValidationError("Debe seleccionar al menos un viaje relacionado con la carta porte.")

			# Validacion general de los viajes.
			for v in self.viajescp_id:
				vobj = self.env['trafitec.viajes'].search([('id', '=', v.id)])
				if v.asociado_id.id != self.partner_id.id:
					error = True
					errores += "El asociado del viaje " + (str(v.name)) + " debe ser igual al de la factura.\r\n"

				if v.flete_asociado <= 0:
					error = True
					errores += "El viaje " + (str(v.name)) + " deben tener el flete del asociado calculado.\r\n"

				if v.documentacion_completa == False:
					error = True
					errores += "El viaje " + (str(v.name)) + " deben tener documentación completa.\r\n"

				if v.en_cp == True:
					error = True
					errores += "El viaje " + (str(v.name)) + " ya tiene carta porte relacionada.\r\n"

		if self.tipo == 'automatica' or self.tipo == 'manual':
			if not self.lineanegocio:
				error = True
				errores += "Debe especificar la línea de negocio.\r\n"

			if self.tipo == 'automatica':
				if not self.viajes_id:
					error = True
					errores += "Debe especificar al menos un viaje relacionado con la factura de cliente.\r\n"

				totalflete = 0
				for v in self.viajes_id:
					totalflete += v.flete_cliente

				totalconceptos = 0
				for l in self.invoice_line_ids:
					totalconceptos += l.price_subtotal

				if totalflete <= 0:
					error = True
					errores += "El total de flete de viajes debe ser mayor a cero.\r\n"

				if totalconceptos <= 0:
					error = True
					errores += "El total de flete de los conceptos debe ser mayor a cero.\r\n"
				"""
				diferencia = totalflete - totalconceptos
				if abs(diferencia) >= 1:
					error = True
					errores += "El total de flete {0:20,.2f} debe ser menor o igual al subtotal del documento {1:20,.2f}.\r\n".format(
						totalflete, totalconceptos)
                """

			"""	
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
			"""
			
			#Validacion general de los viajes.
			for v in self.viajes_id:
				vobj = self.env['trafitec.viajes'].search([('id', '=', v.id)])
				if v.cliente_id.id != self.partner_id.id:
					error = True
					errores+="El cliente del viaje "+(str(v.name))+" debe ser igual al de la factura.\r\n"

				if v.flete_cliente <= 0:
					error = True
					errores += "El viaje "+(str(v.name))+" deben tener el flete del cliente calculado.\r\n"

				if v.documentacion_completa==False:
					error = True
					errores += "El viaje "+(str(v.name))+" deben tener documentación completa.\r\n"

				if v.en_factura==True:
					error = True
					errores += "El viaje "+(str(v.name))+" ya esta relacionado con una factura.\r\n"

		if error:
			raise ValidationError(_('Alerta..\n'+errores))

		#FIN VALIDACIONES

		#El cliente con las funciones de saldo indicadas.
		persona = self.env['res.partner']
		
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

			#print(cliente_nombre,cliente_saldo,cliente_limite_credito,prorroga_hay,prorroga_fecha)
			if self.type == 'out_invoice':
				if self._context.get('validar_credito_cliente', True):
					if cliente_saldo > cliente_limite_credito:
						if prorroga_hay:
							if prorroga_fecha and datetime.date.today() > prorroga_fecha:
								error = True
								errores += "El cliente {} con saldo {:20,.2f} ha excedido su crédito {:20,.2f} por {:20,.2f} (Con prorroga).".format(cliente_nombre, cliente_saldo, cliente_limite_credito,cliente_saldo-cliente_limite_credito)
						else:
							error = True
							errores += "El cliente {} con saldo {:20,.2f} ha excedido su crédito {:20,.2f} por {:20,.2f} (Sin prorroga).".format(cliente_nombre, cliente_saldo, cliente_limite_credito,cliente_saldo-cliente_limite_credito)

		except:
			print("**Error al evaluar el crédito del cliente al crear la factura.")
			#raise UserError(_("Error al evaluar el crédito del cliente al crear factura."))
		#--------------------------------------------------------------------------
		
		#Validar los viajes.
		for f in self:
			#Factura de cliente.
			if self._context.get('type', 'out_invoice') == 'out_invoice':
				for v in f.viajes_id:
					vobj = self.env['trafitec.viajes'].search([('id', '=', v.id)])
					if vobj.en_factura:
						error = True
						errores += "El viaje {} ya tiene factura cliente: {}.\r\n".format(v.name, (v.factura_cliente_id.name or v.factura_cliente_id.number or ''))

			else: #Factura de proveedor.
				for vcp in f.viajescp_id:
					vobj = self.env['trafitec.viajes'].search([('id', '=', vcp.id)])
					if vobj.en_cp:
						error = True
						errores += "El viaje {} ya tiene carta porte: {}.\r\n".format(vcp.name, (vcp.factura_proveedor_id.name or vcp.factura_proveedor_id.number or ''))

		if error:
			raise ValidationError(_(errores))

		#Estabelece cada viaje como Con factura de cafa viaje relacionado.
		for f in self:
			#Es factura de cliente.
			if self._context.get('type', 'out_invoice') == 'out_invoice':
				for v in f.viajes_id:
					v.with_context(validar_credito_cliente=False).write({'en_factura': True, 'factura_cliente_id': self.id})
			else: # Es factura de proveedor.
				for v in f.viajescp_id:
					v.with_context(validar_credito_cliente=False).write({'en_cp': True, 'factura_proveedor_id': self.id})
		
		#------------------------
		#TIPO DE COMPROBANTE
		#------------------------
		"""
		sat_tipo_obj = self.env['sat.tipo.comprobante']
		for rec in self:
			tipo_id = sat_tipo_obj.search([('code', '=', 'T')], limit=1)
			self.type_document_id = tipo_id[0].id if tipo_id else False
		"""
		
		factura = super(trafitec_account_invoice, self).action_invoice_open()
		return factura

	#Al presionar boton cancelar.
	
	def action_invoice_cancel(self):
		#Factura de cliente: Llamar al asistente de cancelacion para preguntar motivo.
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

		#Factura de proveedor.
		else:# Factura de proveedor.
			#raise UserError("Al cancelar factura proveedor!!")
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
		if self.tipo != "manual":
			raise UserError(_("La factura debe ser manual."))
		
		#Establece el estado de Sin factura en cada viaje relacionado.
		for v in self.viajes_id:
			if v.factura_cliente_id.id == self.id:
				v.with_context(validar_credito_cliente=False).write({'factura_cliente_id': False, 'en_factura': False})

		"""
		#Establece el estado de Sin factura en cada viaje relacionado.
		for f in self:
			viajes = self.env['trafitec.viajes'].search([('factura_cliente_id', '=', f.id)])
			
			if len(viajes) <= 0:
				raise UserError(_("No se encontraron viajes relacionados."))
			
			for v in viajes:
				v.with_context(validar_credito_cliente=False).write({'factura_cliente_id': False, 'en_factura': False})
		"""
		
	
	def action_relacionar_viajes(self):
		self.ensure_one()
		if self.tipo != "manual":
			raise UserError(_("La factura debe ser manual."))

		#Establece el estado de Sin factura en cada viaje relacionado.
		for v in self.viajes_id:
			if v.factura_cliente_id.id == False:
				v.with_context(validar_credito_cliente=False).write({'factura_cliente_id': self.id, 'en_factura': True})

	
	def action_liberar_viajescp(self):
		#Establece el estado de Sin factura en cada viaje relacionado.
		for f in self:
			viajes = self.env['trafitec.viajes'].search([('factura_proveedor_id', '=', f.id)])

			if len(viajes) <= 0:
				raise UserError(_("No se encontraron viajes relacionados."))

			for v in viajes:
				v.with_context(validar_credito_cliente=False).write({'factura_proveedor_id': False, 'en_cp': False})

	#Despues de cancelar.. se puede mandar a borrador.
	
	def action_invoice_draft(self):
		factura = super(trafitec_account_invoice, self).action_invoice_draft()
		return factura

class trafitec_facturas_cancelar(models.TransientModel):
	_name = 'trafitec.facturas.cancelar'
	factura_id = fields.Many2one(string='Factura', comodel_name='account.invoice', help='Factura que se cancelara.')
	detalles = fields.Char(string='Detalles', default='', help='Detalles.')
	
	
	
	def cancelar(self):
		for rec in self:
			for v in rec.factura_id.viajes_id:
				vobj = rec.env['trafitec.viajes'].search([('id', '=', v.id)])
				vobj.write({'factura_cliente_id': False, 'en_factura': False})
			
			rec.factura_id.write({'cancelacion_detalles': self.detalles})
			factura = rec.factura_id.action_cancel()
		#return factura


#Cancelación para facturas de clientes:
class trafitec_argil_factura_cancelar(models.TransientModel):
	_inherit = 'account_invoice.cancel_wizard'
	cancelacion_detalles = fields.Char(string='Motivo de cancelación', default='', help='Motivo de cancelación de factura.')
	
	
	def action_cancel(self):
		self.ensure_one()
		_logger.info("**************CANCELAR*******************")

		#raise UserError(str(active_ids))
		accion = super(trafitec_argil_factura_cancelar, self).action_cancel()
		try:
			active_ids = self._context.get('active_ids', []) or []
			for f in active_ids:
				factura_obj = self.env['account.invoice']
				factura_dat = factura_obj.browse([f])
				#factura_dat.with_context(validar_credito_cliente=False).write({'cancelacion_detalles': (self.cancelacion_detalles or '')})

				# Marcar sin factura los viajes relacionados con la factura.
				if factura_dat.travel_ids:
					for v in factura_dat.viajes_id:
						v.with_context(validar_credito_cliente=False).write({'en_factura': False, 'factura_cliente_id': False})
					factura_dat.viajes_id = [(5, _, _)]
		except:
			_logger.info("**Error al guardar el motivo de cancelación.")
			pass

		return accion

class trafitec_facturas_documentos(models.Model):
	_name = 'trafitec.facturas.documentos'


	name = fields.Selection(string="Tipo",
							selection=[('cartaporte_pdf', 'Carta porte PDF'), ('cartaporte_xml', 'Carta porte XML')],
							required=True, default='cartaporte_pdf')
	documento_nombre = fields.Char("Nombre del archivo")
	documento_archivo = fields.Binary(string="Archivo", required=True)
	factura_id = fields.Many2one(comodel_name="account.invoice", string="Factura", ondelete='cascade')

	
	@api.constrains('documento_nombre')
	def _check_filename(self):
		if self.documento_archivo:
			if self.documento_nombre:
				raise UserError(_('Alerta..\n No hay archivo.'))
			else:
				# Check the file's extension
				tmp = self.documento_nombre.split('.')
				ext = tmp[len(tmp) - 1]
				if ext != 'pdf' and self.name == "cartaporte_pdf":
					raise UserError(_('Alerta..\nSolo se permiten archivos pdf para.'))
				if ext != 'xml' and self.name == "cartaporte_xml":
					raise UserError(_('Alerta..\nSolo se permiten archivos xml para el cfdi.'))

class trafitec_facturas_conceptos(models.Model): #Mike
	_inherit = ['account.invoice.line']
	sistema=fields.Boolean(string="Sistema",default=True) #Indica si es un registro del sistema.


	@api.model
	def create(self, vals):
		print("***************************Modelo:"+str(self))
		#print("***Create Vals:" + str(vals))
		#print("***Create Vals:" + str(self._origin))
		#vals['sistema']= self._origin.sistema
		#if not vals['sistema']:
		#  vals['sistema']=False

		concepto=super(trafitec_facturas_conceptos, self).create(vals)
		#concepto.write({'sistema':self.sistema})
		return concepto

class trafitec_facturas_agregar_quitar(models.Model):
	_name = 'trafitec.agregar.quitar'
	_inherit = ['mail.thread', 'mail.activity.mixin']

	name = fields.Char(string='Folio', default='Nuevo')
	factura_id = fields.Many2one('account.invoice',string='Factura',domain="[('es_facturamanual','=',True),('pagada','=',False)]")
	cliente_id = fields.Many2one('res.partner', string="Cliente",
										domain="[('customer','=',True), ('parent_id', '=', False)]", related='factura_id.partner_id', store=True)
	domicilio_id = fields.Many2one('res.partner', string="Domicilio",
										  domain="['|',('parent_id', '=', cliente_origen_id),('id','=',cliente_origen_id)]", related='factura_id.partner_shipping_id', store=True)
	placas_id = fields.Many2one('fleet.vehicle', string='Vehiculo',
								domain="['&',('asociado_id','!=',False),('operador_id','!=',False)]", store=True,readonly=True)
	operador_id = fields.Many2one('res.partner', string="Operador", domain="[('operador','=',True)]", store=True,readonly=True)
	currency_id = fields.Many2one("res.currency", string="Moneda", store=True, related='factura_id.currency_id',readonly=True)
	lineanegocio = fields.Many2one('trafitec.lineanegocio', string='Linea de negocios', store=True, related='factura_id.lineanegocio',readonly=True)
	contiene = fields.Text(string='Contiene', store=True, related='factura_id.contiene',readonly=True)
	total = fields.Monetary(string='Total', store=True, related='factura_id.amount_total',readonly=True)
	fecha = fields.Date(string='Fecha', store=True, related='factura_id.date_invoice',readonly=True)
	state = fields.Selection([('Nueva', 'Nueva'), ('Validada', 'Validada'),
							  ('Cancelada', 'Cancelada')], string='Estado',
							 default='Nueva')
	viaje_id = fields.Many2many('trafitec.viajes', 'facturas_viaje', 'facturas_id', 'viajes_id',
								string='Viajes',
								domain="[('cliente_id','=',cliente_id),('lineanegocio','=',lineanegocio),('state','=','Nueva'),('tipo_viaje','=','Normal'),('en_factura','=',False),('csf','=',False)]")
	viajes_cobrados_id =fields.Many2many('trafitec.viajes', 'facturas_cobrados_viaje', 'facturas_id', 'viajes_id',
								string='Viajes')
	observaciones = fields.Text(string='Observaciones')
	company_id = fields.Many2one('res.company', 'Company',
								 default=lambda self: self.env['res.company']._company_default_get(
									'trafitec.agregar.quitar'))
	invoice_id = fields.Many2one('account.invoice', string='Factura excedente',readonly=True)

	
	def unlink(self):
		for reg in self:
			if reg.state == 'Validada':
				raise UserError(_(
					'Aviso !\nNo se puede eliminar ({}) si esta validada.'.format(reg.name)))
		return super(trafitec_facturas_agregar_quitar, self).unlink()

	@api.onchange('invoice_id')
	def _onchange_abono(self):
		if self.invoice_id:
			res = {'warning': {
				'title': _('Advertencia'),
				'message': _('Se ha generado una factura excedente.')
			}}
			return res

	def _get_parameter_company(self,vals):
		if vals.company_id.id != False:
			company_id = vals.company_id
		else:
			company_id = self.env['res.company']._company_default_get('trafitec.contrarecibo')
		parametros_obj = self.env['trafitec.parametros'].search([('company_id', '=', company_id.id)])
		if len(parametros_obj) == 0:
			raise UserError(_(
				'Aviso !\nNo se ha creado ningun parametro para la compañia {}'.format(company_id.name)))
		return parametros_obj

	@api.onchange('factura_id')
	def _onchange_viajes_cobrados(self):
		if self.factura_id:
			obj = self.env['trafitec.agregar.quitar'].search([('factura_id','=',self.factura_id.id),('state','=','Validada')])
			r = []
			if len(obj) > 0:
				self.viajes_cobrados_id = obj.viaje_id

	@api.onchange('factura_id')
	def _onchange_abonado(self):
		if self.factura_id:
			self.abonado = self.factura_id.abonado

	
	def _compute_abonado(self):
		if self.factura_id:
			self.abonado = self.factura_id.abonado

	abonado = fields.Float(string='Abonado', compute='_compute_abonado')

	@api.onchange('factura_id')
	def _onchange_saldo(self):
		if self.factura_id:
			self.saldo = self.total - self.abonado

	
	def _compute_saldo(self):
		if self.factura_id:
			self.saldo = self.total - self.abonado

	saldo = fields.Float(string='Saldo', compute='_compute_saldo')

	@api.onchange('viaje_id')
	def _onchange_fletes(self):
		amount = 0
		for record in self.viaje_id:
			if amount == 0:
				amount = record.flete_cliente
			else:
				amount += record.flete_cliente
		self.fletes = amount

	
	def _compute_fletes(self):
		amount = 0
		for record in self.viaje_id:
			if amount == 0:
				amount = record.flete_cliente
			else:
				amount += record.flete_cliente
		self.fletes = amount

	fletes = fields.Monetary(string='Fletes', compute='_compute_fletes')

	def _generar_factura_excedente(self, vals, parametros_obj):
		fact = vals.factura_id
		valores = {
			'origin': vals.name,
			'type': fact.type,
			'date_invoice': datetime.datetime.now(),
			'partner_id': fact.partner_id.id,
			'journal_id': fact.journal_id.id,
			'company_id': fact.company_id.id,
			'currency_id': fact.currency_id.id,
			'account_id': fact.account_id.id,
			'reference': 'Factura generada por excedente en el folio {} '.format(vals.name)
		}
		invoice_id = vals.env['account.invoice'].create(valores)

		product = self.env['product.product'].search([('product_tmpl_id','=',parametros_obj.product_invoice.id)])

		piva = (parametros_obj.iva.amount / 100)
		priva = (parametros_obj.retencion.amount / 100)

		monto = self.factura_id.abonado - self.total

		subtotal = monto / (1 + (piva - priva))
		iva = subtotal * piva
		riva = subtotal * priva
		total = subtotal + iva + riva

		inv_line = {
			'invoice_id': invoice_id.id,
			'product_id': product.id,
			'name': product.name,
			'quantity': 1,
			'account_id': fact.account_id.id,
			# order.lines[0].product_id.property_account_income_id.id or order.lines[0].product_id.categ_id.property_account_income_categ_id.id,
			'uom_id': parametros_obj.product_invoice.uom_id.id,
			'price_unit': subtotal,
			'price_unit': subtotal,
			'discount': 0
		}
		vals.env['account.invoice.line'].create(inv_line)


		inv_tax = {
			'invoice_id': invoice_id.id,
			'name': parametros_obj.iva.name,
			'account_id': parametros_obj.iva.account_id.id,
			'amount': (iva - riva),
			'sequence': '0'
		}
		vals.env['account.invoice.tax'].create(inv_tax)

		inv_ret = {
			'invoice_id': invoice_id.id,
			'name': parametros_obj.retencion.name,
			'account_id': parametros_obj.retencion.account_id.id,
			'amount': riva,
			'sequence': '0'
		}
		vals.env['account.invoice.tax'].create(inv_ret)

		return invoice_id

	
	def action_available(self):
		apag = False
		if self.saldo > self.total_g:
		   self.factura_id.write({'abonado':(self.total_g + self.factura_id.abonado)})
		else:
			apag = True
			self.factura_id.write({'pagada': True, 'abonado':(self.factura_id.abonado + self.total_g)})

		for viaje in self.viaje_id:
			viaje.write({'en_factura': True})
		self.write({'state': 'Validada'})

		if apag == True:
			action_ctx = dict(self.env.context)
			view_id = self.env.ref('sli_trafitec.msj_factura_form').id
			return {
				'name': _('Advertencia'),
				'type': 'ir.actions.act_window',
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'trafitec.agregar.quitar',
				'views': [(view_id, 'form')],
				'view_id': view_id,
				'target': 'new',
				'res_id': self.ids[0],
				'context': action_ctx
			}

	#@api.multi
	#def confirmation_button(self):
		#parametros_obj = self._get_parameter_company(self)
		#invoice_id = self._generar_factura_excedente(self, parametros_obj)
		#self.invoice_id = invoice_id

	
	def action_cancel(self):
		self.factura_id.write({'pagada': False, 'abonado': (self.factura_id.abonado - self.total_g)})
		for viaje in self.viaje_id:
			viaje.write({'en_factura': False})
		self.write({'state': 'Cancelada'})
		
	@api.onchange('viaje_id')
	def _onchange_maniobras(self):
		amount = 0
		for record in self.viaje_id:
			if amount == 0:
				amount = record.maniobras
			else:
				amount += record.maniobras
		self.maniobras = amount

	
	def _compute_maniobras(self):
		amount = 0
		for record in self.viaje_id:
			if amount == 0:
				amount = record.maniobras
			else:
				amount += record.maniobras
		self.maniobras = amount

	maniobras = fields.Monetary(string='Maniobras', compute='_compute_maniobras')

	# Totales
	@api.onchange('fletes', 'maniobras')
	def _onchange_subtotal(self):
		self.subtotal_g = self.fletes + self.maniobras

	
	def _compute_subtotal(self):
		self.subtotal_g = self.fletes + self.maniobras

	subtotal_g = fields.Monetary(string='Subtotal', compute='_compute_subtotal')

	@api.onchange('subtotal_g')
	def _onchange_iva(self):
		parametros_obj = self._get_parameter_company(self)
		if self.subtotal_g:
			self.iva_g = self.subtotal_g * (parametros_obj.iva.amount / 100)
		else:
			self.iva_g = 0

	
	def _compute_iva(self):
		parametros_obj = self._get_parameter_company(self)
		if self.subtotal_g:
			self.iva_g = self.subtotal_g * (parametros_obj.iva.amount / 100)
		else:
			self.iva_g = 0

	iva_g = fields.Monetary(string='Iva', compute='_compute_iva')

	@api.onchange('fletes')
	def _onchange_riva(self):
		parametros_obj = self._get_parameter_company(self)
		if self.fletes:
			self.r_iva_g = (self.fletes * (parametros_obj.retencion.amount / 100))
		else:
			self.r_iva_g = 0

	
	def _compute_riva(self):
		parametros_obj = self._get_parameter_company(self)
		if self.fletes:
			self.r_iva_g = (self.fletes * (parametros_obj.retencion.amount / 100))
		else:
			self.r_iva_g = 0

	r_iva_g = fields.Monetary(string='R. IVA', compute='_compute_riva')

	@api.onchange('subtotal_g', 'iva_g', 'r_iva_g')
	def _onchange_total(self):
		self.total_g = self.subtotal_g + self.iva_g - self.r_iva_g

	
	def _compute_total(self):
		self.total_g = self.subtotal_g + self.iva_g - self.r_iva_g

	total_g = fields.Monetary(string='Total', compute='_compute_total')

	@api.model
	def create(self, vals):
		if 'company_id' in vals:
			vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
				'Trafitec.Agregar.Quitar') or _('Nuevo')
		else:
			vals['name'] = self.env['ir.sequence'].next_by_code('Trafitec.Agregar.Quitar') or _('Nuevo')

		return super(trafitec_facturas_agregar_quitar, self).create(vals)
