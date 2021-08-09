# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools,_
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import logging
import datetime

_logger = logging.getLogger(__name__)


class trafitec_cotizaciones_documentos(models.Model):
    _name = 'trafitec.cotizaciones.documentos'
    _description = 'cotizaciones documentos'

    cotizacion_id = fields.Many2one(
    	string='Cotización', 
    	comodel_name='trafitec.cotizacion', 
    	help='Cotización'
    )
    tipodocumento_id = fields.Many2one(
    	string='Tipo de documento', 
    	comodel_name='trafitec.tipodoc', 
    	required=True, 
    	help='Tipo de documento'
    )
    tipo_tipo = fields.Selection(
    	string='Tipo', 
    	related='tipodocumento_id.tipo'
    )
    tipo_evidencia = fields.Boolean(
    	string='Evidencia', 
    	related='tipodocumento_id.evidencia'
    )
    tipo_dmc = fields.Boolean(
    	string='DMC', 
    	related='tipodocumento_id.dmc'
    )
