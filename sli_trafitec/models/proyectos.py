## -*- coding: utf-8 -*-
from openerp import models, fields, api, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError
import logging

_logger = logging.getLogger(__name__)

class sli_proyectos_tareas(models.Model):
	_inherit = 'project.task'
	bloquear_fechalimite = fields.Boolean(string='Bloquear fecha limite', default=False)
	
	@api.model
	def create(self, vals):
		vals['bloquear_fechalimite'] = True
		return super(sli_proyectos_tareas, self).create(vals)