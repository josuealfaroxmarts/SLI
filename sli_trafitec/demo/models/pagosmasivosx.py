## -*- coding: utf-8 -*-
from odoo import models, fields, api, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import logging
import datetime
_logger = logging.getLogger(__name__)

class trafitec_pagosmasivosx(models.TransientModel):
	_inherit = 'account.register.payments'
	
	facturas_id=fields.Many2many('account.move', 'account_invoice_payment_pagosmasivosx_rel', 'payment_id', 'invoice_id', string="Invoices")
	detalles=fields.Char(string='Detalles')
	
	@api.model
	def default_get(self, fields):
		rec = super(trafitec_pagosmasivosx, self).default_get(fields)
		#rec['amount'] = 77
		return rec
	
	def _get_invoices(self):
		self.Abonar(500)
		
		self.facturas_id = None
		ids=self._context.get('active_ids')
		lasfacturas = []
		#lasfacturas = self.env['account.move'].browse(ids)
		
		nuevas=[]
		for x in ids:
			f=self.env['account.move'].browse(x)
			print("***FACK:***"+str(f))
			n = {
			  'id' : f.invoice_id ,
			  'number' : f.number ,
			  'name' : f.name ,
			  'pay_method_id' : f.pay_method_id ,
			  'date' : f.date ,
			  'partner_id' : f.partner_id ,
			  'company_id' : f.company_id ,
			  'journal_id' : f.journal_id ,
			  'amount_residual' : 666 ,
		      'currency_id' : f.currency_id ,
				'amount_residual_company_signed': 666 ,
				'amount_residual_signed': 666
			}
			nuevas.append(n)
		
		print("Las facturas:"+str(lasfacturas))
		self.facturas_id = nuevas
		return nuevas
	                                                  
	@api.onchange('journal_id')
	def _onchange_journal(self):
		self._get_invoices()
		#self._compute_total_invoices_amount()
	
	
	
	

