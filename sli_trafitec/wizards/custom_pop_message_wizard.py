# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class CustomPopMessageWizard(models.TransientModel):
	_name = "custom.pop.message.wizard"
	_description = "Custom Pop Message Wizard"
	
	name = fields.Char(
		string="Mensaje", 
		readonly=True
	)