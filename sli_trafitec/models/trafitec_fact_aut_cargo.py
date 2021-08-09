# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import logging
import datetime
_logger = logging.getLogger(__name__)


class trafitec_fact_aut_cargo(models.Model):
    _name = 'trafitec.fact.aut.cargo'
    _description ='factura aut cargo'

    name = fields.Many2one('trafitec.tipocargosadicionales', string='Producto', required=True, readonly=True)
    valor = fields.Float(string='Total', required=True, readonly=True)
    line_cargo_id = fields.Many2one('trafitec.facturas.automaticas', string='Id factura automatica')
