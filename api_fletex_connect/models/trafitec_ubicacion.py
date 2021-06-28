# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

from odoo import api, fields, models


class FletexTrafitecUbicaciones(models.Model):
    _inherit = 'trafitec.ubicacion'
    
    id_fletex = fields.Integer()

    