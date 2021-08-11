# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class TrafitecBuques(models.Model):
    _name = 'trafitec.buques'
    _description = 'buques'

    name = fields.Char(
        string='Nombre',
        required=True
    )
    detalles = fields.Text(string='Detalles')
