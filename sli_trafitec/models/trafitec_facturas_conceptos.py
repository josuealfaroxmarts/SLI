# -*- coding: utf-8 -*-

import base64
from odoo import models, fields, api, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from xml.dom import minidom


class trafitec_facturas_conceptos(models.Model): #Mike
	_inherit = ['account.move.line']
	sistema=fields.Boolean(string='Sistema',default=True) #Indica si es un registro del sistema.


	@api.model
	def create(self, vals):
		print('***************************Modelo:'+str(self))
		#print('***Create Vals:' + str(vals))
		#print('***Create Vals:' + str(self._origin))
		#vals['sistema']= self._origin.sistema
		#if not vals['sistema']:
		#  vals['sistema']=False

		concepto=super(trafitec_facturas_conceptos, self).create(vals)
		#concepto.write({'sistema':self.sistema})
		return concepto