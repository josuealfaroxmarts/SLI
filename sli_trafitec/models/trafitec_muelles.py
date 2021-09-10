# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from . import amount_to_text
import xlsxwriter
import base64


class TrafitecMuelles(models.Model):
    _name = "trafitec.muelles"
    _description = "Muelles"

    name = fields.Char(
        string="Nombre",
        required=True
    )
    ubicacion = fields.Many2one(
        "trafitec.ubicacion",
        string="Ubicación",
        required=True,
        domain=[
            ("tipo_ubicacion", "=", "puerto")
        ]
    )
    detalles = fields.Text(string="Detalles")
