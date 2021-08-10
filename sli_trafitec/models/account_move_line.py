from odoo import models, fields, api
from xml.dom import minidom


class AccountMoveLine(models.Model):
	_inherit = ['account.move.line']
	
	sistema=fields.Boolean(
		string='Sistema',
		default=True
	) #Indica si es un registro del sistema.


	@api.model
	def create(self, vals):
		concepto=super(AccountMoveLine, self).create(vals)
		return concepto