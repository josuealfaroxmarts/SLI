# -*- coding: utf-8 -*-

from odoo import api, fields, models


class TrafitecUbicacion(models.Model):
    _inherit = "trafitec.ubicacion"
    
    id_fletex = fields.Integer()

    