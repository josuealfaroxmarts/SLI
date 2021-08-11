# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class cancelacion_cuentas_relacion(models.Model):
    _name = 'trafitec.cancelacioncuentas.relacion'
    _description = 'Cancelacion cuentas relacion'

    cancelacion_cuentas_id = fields.Many2one(
        string='Cancelación de cuentas',
        comodel_name='trafitec.cancelacioncuentas'
    )
    factura_cliente_id = fields.Many2one(
        string='Factura cliente',
        comodel_name='account.move'
    )
    factura_proveedor_id = fields.Many2one(
        string='Factura proveedor',
        comodel_name='account.move'
    )
    moneda_id = fields.Many2one(string='Moneda', comodel_name='res.currency')
    abono = fields.Monetary(string='Abono', currency_field='moneda_id')
