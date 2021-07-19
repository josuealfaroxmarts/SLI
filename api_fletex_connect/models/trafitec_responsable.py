# -*- coding: utf-8 -*-
from requests.sessions import default_headers
from openerp import models, fields, api, _
from openerp.exceptions import UserError

class FletexFleetVehicle(models.Model):
    _inherit = 'trafitec.responsable'
    id_fletex = fields.Integer()

