# -*- coding: utf-8 -*-
from requests.sessions import default_headers
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class FletexFleetVehicle(models.Model):
    _inherit = 'trafitec.responsable'
    id_fletex = fields.Integer()

