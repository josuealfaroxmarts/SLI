# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class cancelacion_cuentas_facturas_proveedor(models.Model):
    _name = 'trafitec.cancelacioncuentas.facturas.proveedor'
    _description = 'Cancelacion cuentas en facturas proveedor'

    cancelacion_cuentas_id = fields.Many2one(
        string='Cancelación de cuentas',
        comodel_name='trafitec.cancelacioncuentas'
    )
    moneda_id = fields.Many2one(
        string='Moneda',
        comodel_name='res.currency'
    )

    factura_proveedor_id = fields.Many2one(
        string='Factura proveedor',
        comodel_name='account.move'
    )
    factura_proveedor_fecha = fields.Date(
        string='Fecha',
        related='factura_proveedor_id.date'
    )
    factura_proveedor_total = fields.Monetary(
        string='Total',
        related='factura_proveedor_id.amount_total',
        currency_field='moneda_id'
    )
    factura_proveedor_saldo = fields.Monetary(
        string='Saldo',
        related='factura_proveedor_id.amount_residual',
        currency_field='moneda_id'
    )

    abono = fields.Monetary(
        string='Abono',
        default=0,
        currency_field='moneda_id'
    )
