# -*- coding: utf-8 -*-

from odoo import models, fields, api

class InfoSyncFletex(models.Model):
    _name = 'info.sync.fletex'

    description = fields.Text(string='Descripción')