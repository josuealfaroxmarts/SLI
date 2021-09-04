# -*- coding: utf-8 -*-
from odoo import fields, models, _


class TrafitecResponsable(models.Model):
    _inherit = "trafitec.responsable"

    id_fletex = fields.Integer()

