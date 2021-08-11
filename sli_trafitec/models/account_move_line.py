from odoo import models, fields


class AccountMoveLine(models.Model):
	_inherit = ['account.move.line']
	
	sistema = fields.Boolean(
		string='Sistema',
		default=True
	)