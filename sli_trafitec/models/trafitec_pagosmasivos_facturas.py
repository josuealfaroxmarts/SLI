from odoo import models, fields


class TrafitecPagosmasivosFacturas(models.Model):
    _name = 'trafitec.pagosmasivos.facturas'
    _description = 'Facturas pagos masivos'

    pagomasivo_id = fields.Many2one(
        string='Pago masivo',
        comodel_name='trafitec.pagosmasivos'
    )
    moneda_id = fields.Many2one(
        string='Moneda',
        comodel_name='res.currency',
        required=True
    )
    factura_id = fields.Many2one(
        string='Factura',
        comodel_name='account.move',
        required=True
    )
    factura_fecha = fields.Date(
        string='Fecha',
        related='factura_id.date',
        store=True
    )
    factura_total = fields.Monetary(
        string='Total',
        related='factura_id.amount_total',
        default=0,
        store=True,
        currency_field='moneda_id'
    )
    factura_saldo = fields.Monetary(
        string='Saldo',
        related='factura_id.amount_residual',
        default=0,
        store=True,
        currency_field='moneda_id'
    )
    abono = fields.Monetary(
        string='Abono',
        required=True,
        default=0,
        currency_field='moneda_id'
    )
