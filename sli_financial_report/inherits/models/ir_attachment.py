# -*- coding: utf-8 -*-
# Viridiana Cruz Santos

from odoo import _, fields, models


class Attachments(models.Model):
	_inherit = "ir.attachment"


	# active = fields.Boolean(
	# 	default=True,
	# 	string=_("Activo")
	# )
