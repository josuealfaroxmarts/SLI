## -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import xlrd
import shutil
import datetime
import logging


#from openerp.tools import amount_to_text
from . import amount_to_text

import xlsxwriter
import base64



#from amount_to_text import *


#from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx

_logger = logging.getLogger(__name__)


class TrafitecProgramacionPagosX(models.Model):
	_name = "trafitec.programacionpagosx"
	name = fields.Char(string="Folio", help="Folio de la programación.")
	nombre = fields.Char(string="Nombre", help="Nombre de la programación.")
	tipo = fields.Selection(string="Tipo", selection=[('proveedor', 'Proveedor'), ('cliente', 'Cliente')],
							default='proveedor', help='Tipo de pago para proveedor o de cliente.')
	moneda_id = fields.Many2one(string="Moneda", comodel_name="res.currency", required=True)
	facturas_aplicar_id = fields.One2many(string="Facturas a aplicar",
										  comodel_name="trafitec.programacionpagosx.facturas.aplicar",
										  inverse_name="programacionpagos_id")
	
	buscar_persona_id = fields.Many2one(string="Persona", comodel_name="res.partner")
	buscar_folio = fields.Char(string="Folio")
	buscar_fecha_inicial = fields.Date(string="Fecha inicial")
	buscar_fecha_final = fields.Date(string="Fecha inicial")
	buscar_facturas_id = fields.One2many(string="Facturas a buscar",
										 comodel_name="trafitec.programacionpagosx.facturas.buscar",
										 inverse_name="programacionpagos_id")
	
	diario_id = fields.Many2one(string="Diario de pagos", comodel_name='account.journal', required=True)
	
	total = fields.Float(string="Total", help="Total de la programación de pagos", default=0)
	detalles = fields.Char(string="Detalles", help="Detalles de la programación.")
	state = fields.Selection(string="Estado",
							 selection=[('nuevo', 'Nuevo'), ('revisado', 'Revisado'), ('autorizado', 'Autorizado'),
										('aplicado', 'Aplicado'), ('cancelado', 'Cancelado')], default='nuevo')
	
	@api.depends('facturas_aplicar_id.abono')
	def compute_total_abonos(self):
		total = 0
		for f in self.facturas_aplicar_id:
			total += f.abono
		self.total_abonos = total
	
	total_abonos = fields.Monetary(string="Total abonos", compute="compute_total_abonos", currency_field="moneda_id",
								   store=True)
	
	def action_seleccionar(self):
		lista_actual = []
		for fa in self.facturas_aplicar_id:
			lista_actual.append({'factura_id': fa.factura_id.id, 'abono': fa.abono})
		
		print("*****Context*****")
		print(self._context)
		
		print("*****Env*****")
		print(self.env)
		
		existe = False
		for fb in self.buscar_facturas_id:
			existe = False
			for fa in self.facturas_aplicar_id:
				print("FB"+str(fb.factura_id.id))
				print("FA"+str(fa.factura_id.id))
				if int(fb.factura_id.id) == int(fa.factura_id.id):
					existe = True
					break
			
			if not existe:
				lista_actual.append({'factura_id': fb.factura_id.id, 'abono': fb.factura_id.residual})

		print("***LISTA ACTUAL***")
		print(lista_actual)
		self.facturas_aplicar_id = None
		self.buscar_facturas_id = None
		self.facturas_aplicar_id = lista_actual
	
	def action_buscar_facturas(self):
		print("Buscar facturas señores...")
		self.buscar_facturas_id = None
		
		lista = []
		facturas_obj = self.env['account.move']
		facturas_dat = facturas_obj.search(
			[('partner_id', '=?', self.buscar_persona_id.id), ('state', '=', 'open'), ('type', '=', 'in_invoice'),
			 ('date', '>=', self.buscar_fecha_inicial), ('date', '<=', self.buscar_fecha_final),('number', 'ilike', '%'+(self.buscar_folio or '')+'%')],
			order="id asc")
		
		for f in facturas_dat:
			lista.append({'factura_id': f.id})
		
		self.buscar_facturas_id = lista
	
	def validar(self):
		error = False
		errores = ""
		
		if self.total <= 0:
			error = True
			errores += "El total debe ser mayor a cero.\n"
		
		if self.total_abonos <= 0:
			error = True
			errores += "El total de abonos debe ser mayor a cero.\n"
		
		if self.total_abonos > self.total:
			error = True
			errores += "El total de abonos debe ser menor o igual al total del documento.\n"
		
		for f in self.facturas_aplicar_id:
			if f.abono > f.factura_id.residual:
				error = True
				errores += "El abono debe ser menor o igual al saldo de la factura.\n"
			
			if f.abono < 0:
				error = True
				errores += "El abono debe ser mayor o igual a cero.\n";
		
		if error:
			raise UserError((errores))
	
	
	def action_facturas_aplicar_limpiar(self):
		self.facturas_aplicar_id = None
	
	
	def action_facturas_aplicar_saldar(self):
		for f in self.facturas_aplicar_id:
			f.abono = f.factura_id.residual
	
	
	def action_facturas_aplicar_cero(self):
		for f in self.facturas_aplicar_id:
			f.abono = 0
	
	def action_limpiar_facturas_buscar(self):
		self.buscar_facturas_id = None
	
	def action_nuevo(self):
		self.state = 'nuevo'
	
	def action_revisar(self):
		self.validar()
		self.state = 'revisado'
	
	def action_autorizar(self):
		self.validar()
		self.state = 'autorizado'
	
	def action_aplicar(self):
		self.validar()
		self.state = 'aplicado'
	
	def action_cancelar(self):
		self.state = 'cancelado'
	
	# context="{'form_view_ref': 'account.view_account_payment_from_invoices', 'invoice_ids' : facturas_id}"
	def action_batch_payments(self):
		losids = []
		lasfids = []
		print("****LAS FACTURAS*****")
		for f in self.facturas_aplicar_id:
			if f.factura_id.residual > 0:
				losids.append(f.factura_id.id)
				lasfids.append({'id': f.factura_id.id, 'receiving_amt': f.abono})
		
		# print("Id: "+str(f.factura_id.id)+" Folio: "+str(f.factura_id.number)+" Residual: "+str(f.factura_id.residual))
		
		return {'name': 'Programación de pagos X', 'type': 'ir.actions.act_window', 'type': 'ir.actions.act_window',
			'res_model': 'account.register.payments',  # 'res_model': 'trafitec.programacionpagos',
			'view_type': 'form', 'view_mode': 'form',
				'form_view_ref': 'action_invoice_invoice_batch_process',
				#'form_view_ref': 'sli_account_register_payments_formx2',
				# 'form_view_ref': 'account.view_account_payment_from_invoices',
			'target': 'new', 'multi': True,
			'context': {'invoice_ids': lasfids, 'active_ids': losids, 'active_model': 'account.move', 'batch': True,
				'programacionpagosx': True, 'programacionpagosx_id': self.id, 'default_programacionpagos_id': 1}}
	
	@api.model
	def create(self, vals):
		if 'company_id' in vals:
			vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
				'Trafitec.ProgramacionPagosX') or _('Nuevo')
		else:
			vals['name'] = self.env['ir.sequence'].next_by_code('Trafitec.ProgramacionPagosX') or _('Nuevo')
		
		# vals['buscar_persona_id'] = False
		nuevo = super(TrafitecProgramacionPagosX, self).create(vals)
		return nuevo
	
	
	def write(self, vals):
		# if 'buscar_persona_id' in vals:
		#	vals['buscar_persona_id'] = False
		return super(TrafitecProgramacionPagosX, self).write(vals)
	
	
	def unlink(self):
		# if self.state = ''
		raise UserError(_("No esta permitido borrar."))  # return super(TrafitecProgramacionPagosX, self).unlink()



	def genera_movimiento_general(self,empresa_id,moneda_id,diario_id,total,persona_id,referencia):
		movimiento_general_obj = self.env['account.move'].with_context(check_move_validity=False)
		valores = {
			'company_id': empresa_id,
			 'currency_id': moneda_id,
			 'journal_id': diario_id,# Ok diario de pago.
			'amount': total,
			 'narration': '',
			 'partner_id': persona_id,
			 'ref': referencia,
			'state': 'draft' #draft,posted
		}
		nuevo = movimiento_general_obj.create(valores)
		return nuevo

	def genera_movimiento_detalle(self, movimiento_id, diario_id, moneda_id, factura_id, persona_id, monto, debito, credito, cuenta_id, pago_id, tipo_id):
		movimiento_linea_obj = self.env['account.move.line']
		valores = {
				'move_id': movimiento_id,
				   'name': 'DETALLE' + str(movimiento_id),
				   'journal_id': diario_id,
				   'currency_id': moneda_id,
				   'invoice_id': factura_id,
				   'partner_id': persona_id,
				   'amount_base': monto,
				   'debit': debito,
					'credit': credito,
				   'account_id': cuenta_id,
				   'payment_id': pago_id,
				   'reconciled': True,
				   'user_type_id': tipo_id
				}
		nuevo = movimiento_linea_obj.with_context(check_move_validity=False).create(valores)
		return nuevo
		
	def genera_movimiento_abono(self,empresa_id,abono,movimiento_detalle_debito_id,movimiento_detalle_credito_id):
		abono_obj = self.env['account.partial.reconcile']
		valores = {
			'company_id': empresa_id,
			'amount': abono,
			'debit_move_id': movimiento_detalle_debito_id,
			'credit_move_id': movimiento_detalle_credito_id
		}
		nuevo = abono_obj.create(valores)
		return nuevo
	
	def genera_pago(self,movimiento_nombre,diario_id,movimientos,lista_facturas,total,moneda_id,persona_id,):
		pagos_obj = self.env['account.payment']
		
		folios = ''
		for inv in lista_facturas:
			folios += str(inv['factura_folio'])+' '
			
		valores = {
			'move_name': movimiento_nombre,
			'journal_id': diario_id,
			'payment_method_id': 1,
			'payment_date': datetime.datetime.today(),
			'communication': folios,
			'move_line_ids': [(4, mov['id'], None) for mov in movimientos],
			'invoice_ids': [(4, inv['id'], None) for inv in lista_facturas],
			'payment_type': 'outbound',# outbound=Enviar dinero,inbound=Recibir dinero.
			'amount': total,
			'currency_id': moneda_id,
			'partner_id': persona_id,
			'partner_type': 'supplier',
			'state': 'posted'  # draft,posted,sent,reconciled
			}
		nuevo = pagos_obj.create(valores)
		return nuevo
		
	
	def aplica_pagos(self):
		movimiento_general_obj = self.env['account.move']
		movimiento_linea_obj = self.env['account.move.line'].with_context(check_move_validity=False)
		pagos_obj = self.env['account.payment']
		empresa_actual_id = self.env.user.company_id.id
		
		if len(self.facturas_aplicar_id) <= 0:
			raise UserError(_("Debe haber al menos una factura."))
		
		las_facturas = []
		grupos = []
		for r in self.facturas_aplicar_id:
			f = r.factura_id
			las_facturas.append({'persona_id': f.partner_id.id, 'factura_id': f.id, 'abono': r.abono, 'factura_folio': f.reference})
		
		las_facturas_ordenadas = sorted(las_facturas, key=lambda k: k['persona_id'])
		print("--LISTA DE FACTURAS A PAGAR---")
		print(las_facturas_ordenadas)
		
		id_actual = 0
		id_anterior = 0
		facturas_actual = []
		total = 0
		if len(las_facturas_ordenadas) > 0:
			id_actual = las_facturas_ordenadas[0]['persona_id']
			id_anterior = id_actual
			
			for c, f in enumerate(las_facturas_ordenadas, 1):
				id_actual = f['persona_id']
				
				if id_actual == id_anterior:
					facturas_actual.append({'id': f['factura_id'], 'abono': f['abono'], 'factura_folio': f['factura_folio']})
					total += f['abono']
					
				if id_actual != id_anterior:
					grupos.append({'persona_id': id_anterior, 'total': total, 'facturas': facturas_actual})
					facturas_actual = []
					total = 0
					facturas_actual.append({'id': f['factura_id'], 'abono': f['abono'], 'factura_folio': f['factura_folio']})
					total += f['abono']

				if c == len(las_facturas_ordenadas):
					grupos.append({'persona_id': id_anterior, 'total': total, 'facturas': facturas_actual})
				
				id_anterior = id_actual
		print("--GRUPOS---")
		print(grupos)
		"""
		--------------------------------------------------------------------------------------------------
		APLICAR PAGOS Y REALIZAR CONTABILIZACION.
		--------------------------------------------------------------------------------------------------
		"""
		movimientos = []
		for g in grupos:
			nuevo_movimiento = self.genera_movimiento_general(empresa_actual_id, self.moneda_id.id, self.diario_id.id, g['total'], g['persona_id'], '')
			nuevo_movimiento_credito_linea = self.genera_movimiento_detalle(nuevo_movimiento.id, self.diario_id.id, False, False, g['persona_id'], 0, 0, g['total'], self.diario_id.default_credit_account_id.id, False, 3)

			nuevo_pago = self.genera_pago('', self.diario_id.id, movimientos, g['facturas'],
										  g['total'], self.moneda_id.id, g['persona_id'])

			#----------------------------------------------------------------------------
			# Se generan 2 account.move.line
			movimientos = []
			for f in g['facturas']:
				abono = f['abono']
				
				nuevo_movimiento_debito_linea = self.genera_movimiento_detalle(nuevo_movimiento.id, self.diario_id.id, False, False, g['persona_id'], 0, abono, 0, self.diario_id.default_debit_account_id.id, nuevo_pago.id, 2)
				movimientos.append({'id': nuevo_movimiento_debito_linea.id})
				persona_obj = self.env['res.partner'].browse(g['persona_id'])
				factura_obj = self.env['account.move'].browse(f['id'])
				
				
				#nuevo_parcial = self.genera_movimiento_abono(empresa_actual_id, abono, nuevo_movimiento_debito_linea.id, nuevo_movimiento_credito_linea.id)
			

			#nuevo_movimiento.post()
			#nuevo_movimiento_nombre = nuevo_movimiento.name
			#print("MOVIMIENTO NUEVO::" + str(nuevo_movimiento_nombre))
			#nuevo_pago.write({'move_name', nuevo_movimiento_nombre})
			
			
			

			#---------------------------------------------
			#FULL RECONCILE
			#---------------------------------------------
				
				
class TrafitecProgramacionPagosXFacturasAplicar(models.Model):
	_name = "trafitec.programacionpagosx.facturas.aplicar"
	programacionpagos_id = fields.Many2one(string="Programacion de pagos", comodel_name="trafitec.programacionpagosx")
	factura_id = fields.Many2one(string="Factura", comodel_name="account.move",
								 domain=[('state', '=', 'open'), ('type', '=', 'in_invoice')])
	fecha = fields.Date(string="Fecha", related="factura_id.date")
	persona_id = fields.Many2one(string="Persona", related="factura_id.partner_id")
	moneda_id = fields.Many2one(string="Moneda", related="factura_id.currency_id")
	total = fields.Monetary(string="Total", related="factura_id.amount_total", currency_field="moneda_id")
	saldo = fields.Monetary(string="Saldo", related="factura_id.residual", currency_field="moneda_id")
	abono = fields.Monetary(string="Abono", default=0, currency_field="moneda_id")


class TrafitecProgramacionPagosXFacturasBuscar(models.TransientModel):
	_name = "trafitec.programacionpagosx.facturas.buscar"
	programacionpagos_id = fields.Many2one(string="Programacion de pagos", comodel_name="trafitec.programacionpagosx")
	factura_id = fields.Many2one(string="Factura", comodel_name="account.move",
								 domain=[('state', '=', 'open'), ('type', '=', 'in_invoice')])
	fecha = fields.Date(string="Fecha", related="factura_id.date")
	persona_id = fields.Many2one(string="Persona", related="factura_id.partner_id")
	moneda_id = fields.Many2one(string="Moneda", related="factura_id.currency_id")
	total = fields.Monetary(string="Total", related="factura_id.amount_total", currency_field="moneda_id")
	saldo = fields.Monetary(string="Saldo", related="factura_id.residual", currency_field="moneda_id")



