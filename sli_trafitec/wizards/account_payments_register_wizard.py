# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools


class AccountPaymentsRegisterWizard(models.TransientModel):
	_inherit = "account.payments.register.wizard"
	
	facturas_id = fields.Many2many(
		"account.move",
		"account_invoice_payment_pagosmasivosx_rel",
		"payment_id",
		"move_id",
		string="Invoices"
	)
	detalles = fields.Char(string="Detalles")
	
	@api.model
	def default_get(self, fields):
		rec = super(AccountPaymentsRegister, self).default_get(fields)
		return rec
	
	def _get_invoices(self):
		self.Abonar(500)
		self.facturas_id = None
		ids = self._context.get("active_ids")
		nuevas=[]
		for x in ids:
			f=self.env["account.move"].browse(x)
			n = {
				"id": f.move_id,
				"name": f.name,
				"name": f.name,
				"pay_method_id": f.pay_method_id,
				"date": f.date,
				"partner_id": f.partner_id,
				"company_id": f.company_id,
				"journal_id": f.journal_id,
				"amount_residual": 666,
				"currency_id": f.currency_id,
				"amount_residual_company_signed": 666,
				"amount_residual_signed": 666
			}
			nuevas.append(n)

		self.facturas_id = nuevas

		return nuevas

	@api.onchange("journal_id")
	def _onchange_journal(self):
		self._get_invoices()