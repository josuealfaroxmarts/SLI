# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError


class TrafitecCotizacionLineCargos(models.Model):
    _name = 'trafitec.cotizaciones.linea.cargos'
    _description = 'cotizaciones linea cargos'

    name = fields.Many2one(
        'trafitec.tipocargosadicionales',
        string='Tipos de cargos adicionales',
        required=True
    )
    iva = fields.Many2one(
        'account.tax',
        string='IVAS',
        required=True
    )
    tipocalculo = fields.Selection([
            ('Suma', 'Suma'),
            ('Multiplicado', 'Multiplicado')
        ],
        string='Tipo de cálculo',
        required=True
    )
    valor = fields.Float(
        string='Valor',
        required=True
    )
    linea_id = fields.Many2one(
        'trafitec.cotizaciones.linea',
        ondelete='restrict'
    )
    total = fields.Float(
        string='Total',
        readonly=True,
        compute='_total_lineas'
    )

    @api.constrains('valor')
    def _check_valor(self):
        for rec in self:
            if self.valor <= 0:
                raise UserError(
                    ('Error !\nEn el valor debe ser un valor mayor 0')
                )
