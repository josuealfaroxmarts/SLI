# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, tools


class cancelacion_cuentas_facturas_cliente(models.Model):
	_name = 'trafitec.cancelacioncuentas.facturas.cliente'
	_description = 'Cancelacion cuentas en facturas cliente'
	
	cancelacion_cuentas_id = fields.Many2one(
		string='Cancelación de cuentas',
		comodel_name='trafitec.cancelacioncuentas'
	)
	moneda_id = fields.Many2one(string='Moneda', comodel_name='res.currency')

	factura_cliente_id = fields.Many2one(
		string='Factura cliente',
		comodel_name='account.move'
	)
	factura_cliente_fecha = fields.Date(
		string='Fecha',
		related='factura_cliente_id.date'
	)
	factura_cliente_total = fields.Monetary(
		string='Total',
		related='factura_cliente_id.amount_total',
		currency_field='moneda_id'
	)
	factura_cliente_saldo = fields.Monetary(
		string='Saldo',
		related='factura_cliente_id.amount_residual',
		currency_field='moneda_id'
	)
	abono = fields.Monetary(
		string='Abono',
		default=0,
		currency_field='moneda_id'
	)