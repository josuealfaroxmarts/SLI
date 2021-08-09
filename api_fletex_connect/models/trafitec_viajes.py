# -*- coding: utf-8 -*-

from odoo import api, fields, models


class TrafitecViajes(models.Model):
    _inherit = "trafitec.viajes"
    
    id_fletex = fields.Integer()