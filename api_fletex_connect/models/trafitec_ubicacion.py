# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError

from odoo import api, fields, models


class FletexTrafitecUbicaciones(models.Model):
    _inherit = 'trafitec.ubicacion'
    
    id_fletex = fields.Integer()

    