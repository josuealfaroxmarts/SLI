# -*- coding: utf-8 -*-

from io import StringIO
from odoo import models, fields, api

class InfoSyncFletex(models.Model):
    _name = 'info.sync.fletex'
    _description ='info sync'
    date = fields.Date(string='Fecha')
    record_type = fields.Char(string='Tipo de registro')
    result = fields.Char(string='Resultado')
    description = fields.Text(string='Descripción')
    