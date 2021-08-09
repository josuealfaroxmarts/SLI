# -*- coding: utf-8 -*-

import base64
from odoo import models, fields, api, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from xml.dom import minidom


class AccountPayment(models.Model):
	_inherit = 'account.payment'

	def post(self):
		try:
			active_ids = self._context.get('active_ids', []) or []
			for f in active_ids:
				saldo = self.partner_id.saldo_facturas - self.amount
				saldo_restante = self.partner_id.limite_credito + saldo
				self.partner_id.write({'saldo_facturas': saldo, 'limite_credito_fletex': saldo_restante})
		except:
			pass

		return super(AccountPayment, self).post()