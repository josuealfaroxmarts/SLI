# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from . import amount_to_text
import xlsxwriter
import base64


class TrafitecLineaNegocio(models.Model):
    _name = "trafitec.linea.negocio"
    _description = "Linea Negocio"

    name = fields.Char(
        string="Nombre",
        required=True
    )
    porcentaje = fields.Float(
        string="Porcentaje de comisión",
        required=True
    )
