# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from . import amount_to_text
import xlsxwriter
import base64

	
class TrafitecUnidadmedida(models.Model):
	_inherit = 'uom.uom'

	trafitec = fields.Boolean(string='Es unidad de medida para Trafitec')
