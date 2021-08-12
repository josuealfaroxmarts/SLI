# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from . import amount_to_text
import xlsxwriter
import base64


class TrafitecLineanegocio(models.Model):
    _name = 'trafitec.lineanegocio'
    _description = 'linea negocio'

    name = fields.Char(
        string="Nombre",
        required=True
    )
    porcentaje = fields.Float(
        string="Porcentaje de comisión",
        required=True
    )
