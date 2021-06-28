## -*- coding: utf-8 -*-
from openerp import models, fields, api, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError
import logging
import datetime

import base64
_logger = logging.getLogger(__name__)


class SliGlo(models.Model):
	_name = "sli.glo"
	_auto = False
	
	def cfg(self):
		emp = None
		emp = self.env['res.company']._company_default_get('sli_trafitec')
		cfg = self.env['trafitec.parametros'].search([('company_id', '=', emp.id)])
		return cfg
	
	def proveedor_saldo(self, persona_id):
		return 0
	
	def cliente_saldo(self, persona_id):
		return 0
	
	def seguridad_derecho(self, usuario_id, derecho_id):
		return False
	
