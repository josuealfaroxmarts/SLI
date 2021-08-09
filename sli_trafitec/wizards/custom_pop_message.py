# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class CustomPopMessage(models.TransientModel):
	_name = 'custom.pop.message'
	_description = 'Custom pop message'
	
	name = fields.Char('Mensaje', readonly=True)