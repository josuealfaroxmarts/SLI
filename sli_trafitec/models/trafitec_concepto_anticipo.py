# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class trafitec_concepto_anti(models.Model):
    _name = 'trafitec.concepto.anticipo'
    _description = 'concepto anticipo'

    name = fields.Char(string='Concepto', required=True)
    requiere_orden = fields.Boolean(string='Requiere orden de carga')
