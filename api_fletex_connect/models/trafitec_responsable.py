# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class TrafitecResponsable(models.Model):
    _inherit = "trafitec.responsable"

    id_fletex = fields.Integer()

