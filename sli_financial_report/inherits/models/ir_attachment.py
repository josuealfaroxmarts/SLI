# -*- coding: utf-8 -*-
# Viridiana Cruz Santos

from odoo import fields, models


class Attachments(models.Model):
	_inherit = "ir.attachment"

	# active = fields.Boolean(
	# 	string="Activo",
	# 	default=True
	# )