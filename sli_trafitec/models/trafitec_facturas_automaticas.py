# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime


class TrafitecFacturasAutomaticas(models.Model):
    _name = 'trafitec.facturas.automaticas'
    _description = 'trafitec facturas automaticas'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Folio',
        default='Nuevo'
    )
    cliente_id = fields.Many2one(
        'res.partner',
        string="Cliente",
        domain=[('customer', '=', True), ('parent_id', '=', False)],
        required=True
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Moneda",
        required=True
    )
    lineanegocio = fields.Many2one(
        'trafitec.lineanegocio',
        string='Linea de negocios',
        required=True
    )
    csf = fields.Boolean(
        string='CSF',
        default=False
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'trafitec.facturas.automaticas'
        )
    )
    viaje_id = fields.Many2many(
        'trafitec.viajes',
        'facturas_viaje_relation',
        'facturas_id',
        'viajes_id',
        string='Viajes',
        domain=[
            ('cliente_id', '=', cliente_id),
            ('lineanegocio', '=', lineanegocio),
            ('state', '=', 'Nueva'),
            ('tipo_viaje', '=', 'Normal'),
            ('en_factura', '=', False)
        ]
    )
    payment_term_id = fields.Many2one(
        'account.payment.term',
        string='Forma de pago',
        required=True
    )
    metodo_pago_id = fields.Many2one(
        'l10n_mx_edi.payment.method',
        'Metodo de Pago',
        help='Metodo de Pago Requerido por el SAT',
        required=True
    )
    uso_cfdi_id = fields.Many2one(
        'sat.uso.cfdi',
        'Uso CFDI',
        required=True,
        help='Define el motivo de la compra.'
    )
    cargo_id = fields.One2many(
        'trafitec.fact.aut.cargo',
        'line_cargo_id'
    )
    state = fields.Selection([
        ('Nueva', 'Nueva'),
        ('Validada', 'Validada'),
        ('Cancelada', 'Cancelada')],
        string='Estado',
        default='Nueva'
    )
    move_id = fields.Many2one(
        'account.move',
        string='Factura cliente',
        domain=[
            ('type', '=', 'out_invoice'),
            ('partner_id', '=', cliente_id)
        ]
    )
    subtotal_g = fields.Monetary(
        string='Subtotal',
        compute='_compute_subtotal'
    )
    iva_g = fields.Monetary(
        string='Iva',
        compute='_compute_iva'
    )
    r_iva_g = fields.Monetary(
        string='R. IVA',
        compute='_compute_riva'
    )
    total_g = fields.Monetary(
        string='Total',
        compute='_compute_total'
    )
    origen = fields.Char(string='Origen')
    destino = fields.Char(string='Destino')
    cliente_origen_id = fields.Many2one(
        'res.partner',
        string="Cliente origen",
        domain=[('customer', '=', True), ('parent_id', '=', False)],
        required=True
    )
    domicilio_origen_id = fields.Many2one(
        'res.partner',
        string="Domicilio origen",
        domain=[
            '|',
            ('parent_id', '=', cliente_origen_id),
            ('id', '=', cliente_origen_id)
        ],
        required=True
    )
    cliente_destino_id = fields.Many2one(
        'res.partner',
        string="Cliente destino",
        domain=[('customer', '=', True), ('parent_id', '=', False)],
        required=True
    )
    domicilio_destino_id = fields.Many2one(
        'res.partner',
        string="Domicilio destino",
        domain=[
            '|',
            ('parent_id', '=', cliente_destino_id),
            ('id', '=', cliente_destino_id)
        ],
        required=True
    )
    usar_origen_destino = fields.Boolean(
        string='Usar origen y destino del viaje',
        default=False
    )
    contiene = fields.Text(string='Contiene')
    observaciones = fields.Text(string='Observaciones')

    def unlink(self):
        for reg in self:
            if reg.state == 'Validada':
                raise UserError(
                    'Aviso !\nNo se puede eliminar la factura automatica '
                    + '({}) si esta validada.'.format(reg.name)
                )
        return super(TrafitecFacturasAutomaticas, self).unlink()

    @api.onchange('cliente_id')
    def _onchange_partner_trafitec(self):
        for rec in self:
            if rec.cliente_id:
                rec.cliente_origen_id = rec.cliente_id
                rec.domicilio_origen_id = rec.cliente_id
                rec.cliente_destino_id = rec.cliente_id
                rec.domicilio_destino_id = rec.cliente_id

    def _get_parameter_company(self, vals):
        if vals.company_id.id:
            company_id = vals.company_id
        else:
            company_id = self.env['res.company']._company_default_get(
                'trafitec.contrarecibo'
            )
        parametros_obj = self.env['trafitec.parametros'].search([
            ('company_id', '=', company_id.id)
        ])
        if len(parametros_obj) == 0:
            raise UserError(
                'Aviso !\nNo se ha creado ningun parametro para la compañia '
                + '{}'.format(company_id.name)
            )
        return parametros_obj

    @api.onchange('csf', 'cliente_id', 'currency_id', 'lineanegocio')
    def _onchange_csf(self):
        for rec in self:
            if rec.csf:
                return {
                    'domain': {
                        'viaje_id': [
                            ('cliente_id', '=', rec.cliente_id.id),
                            ('moneda', '=', rec.currency_id.id),
                            ('lineanegocio', '=', rec.lineanegocio.id),
                            ('state', '=', 'Nueva'),
                            ('tipo_viaje', '=', 'Normal'),
                            ('csf', '=', True),
                            ('en_factura', '=', False)
                        ]
                    }
                }
            else:
                return {
                    'domain': {
                        'viaje_id': [
                            ('cliente_id', '=', rec.cliente_id.id),
                            ('moneda', '=', rec.currency_id.id),
                            ('lineanegocio', '=', rec.lineanegocio.id),
                            ('state', '=', 'Nueva'),
                            ('tipo_viaje', '=', 'Normal'),
                            ('en_factura', '=', False)
                        ]
                    }
                }

    @api.onchange('viaje_id')
    def _onchange_viaje_id(self):
        for rec in self:
            if rec.viaje_id:
                r = []
                for viaje in rec.viaje_id:
                    if len(viaje.cargo_id) > 0:
                        for cargos in viaje.cargo_id:
                            apagador = False
                            for rr in r:
                                if rr.get('name') == cargos.name:
                                    apagador = True
                                    rr['valor'] = rr.get(
                                        'valor'
                                    ) + cargos.valor
                            if not apagador:
                                value = {
                                    'name': cargos.name,
                                    'valor': cargos.valor
                                }
                                r.append(value)
                rec.cargo_id = r

    @api.onchange('cargo_id')
    def _onchange_subtotal_g(self):
        for rec in self:
            if rec.viaje_id:
                amount = 0
                for viaje in rec.viaje_id:
                    amount += viaje.flete_cliente
                for cargo in rec.cargo_id:
                    amount += cargo.valor
                rec.subtotal_g = amount
            else:
                rec.subtotal_g = 0

    def _compute_subtotal(self):
        for rec in self:
            if rec.viaje_id:
                amount = 0
                for viaje in rec.viaje_id:
                    amount += viaje.flete_cliente
                for cargo in rec.cargo_id:
                    amount += cargo.valor
                rec.subtotal_g = amount
            else:
                rec.subtotal_g = 0

    @api.onchange('subtotal_g')
    def _onchange_iva(self):
        for rec in self:
            parametros_obj = self._get_parameter_company(rec)
            if rec.subtotal_g:
                rec.iva_g = rec.subtotal_g * (parametros_obj.iva.amount / 100)
            else:
                rec.iva_g = 0

    def _compute_iva(self):
        for rec in self:
            parametros_obj = self._get_parameter_company(rec)
            if rec.subtotal_g:
                rec.iva_g = rec.subtotal_g * (parametros_obj.iva.amount / 100)
            else:
                rec.iva_g = 0

    @api.onchange('subtotal_g')
    def _onchange_riva(self):
        for rec in self:
            parametros_obj = self._get_parameter_company(rec)
            if rec.subtotal_g:
                rec.r_iva_g = (
                    rec.subtotal_g
                    * (parametros_obj.retencion.amount / 100)
                )
            else:
                rec.r_iva_g = 0

    def _compute_riva(self):
        for rec in self:
            parametros_obj = self._get_parameter_company(rec)
            if rec.subtotal_g:
                rec.r_iva_g = (
                    rec.subtotal_g
                    * (parametros_obj.retencion.amount / 100)
                )
            else:
                rec.r_iva_g = 0

    @api.onchange('subtotal_g', 'iva_g', 'r_iva_g')
    def _onchange_total(self):
        for rec in self:
            rec.total_g = rec.subtotal_g + rec.iva_g + rec.r_iva_g

    def _compute_total(self):
        for rec in self:
            rec.total_g = rec.subtotal_g + rec.iva_g + rec.r_iva_g

    def action_available(self):
        for rec in self:
            if not rec.move_id.id:
                parametros_obj = self._get_parameter_company(rec)
                valores = {
                    'type': 'out_invoice',
                    'date': datetime.datetime.now(),
                    'partner_id': rec.cliente_id.id,
                    'partner_shipping_id': rec.domicilio_origen_id.id,
                    'metodo_pago_id': rec.metodo_pago_id.id,
                    'payment_term_id': rec.payment_term_id.id,
                    'uso_cfdi_id': rec.uso_cfdi_id.id,
                    'journal_id': parametros_obj.journal_id_invoice.id,
                    'company_id': rec.company_id.id,
                    'currency_id': rec.currency_id.id,
                    'account_id': parametros_obj.account_id_invoice.id,
                    'ref': 'Factura generada automaticamente.'
                }
                move_id = self.env['account.move'].create(valores)
                amount = 0
                uom = parametros_obj.product_invoice.product_tmpl_id.uom_id
                for viaje in rec.viaje_id:
                    amount += viaje.flete_cliente
                inv_line = {
                    'move_id': move_id.id,
                    'product_id': parametros_obj.product_invoice.id,
                    'name': parametros_obj.product_invoice.name,
                    'quantity': 1,
                    'account_id': parametros_obj.account_id_invoice.id,
                    'uom_id': uom.id,
                    'price_unit': amount,
                    'discount': 0
                }
                self.env['account.move.line'].create(inv_line)
                for cargo in rec.cargo_id:
                    uom = cargo.name.product_id.product_tmpl_id.uom_id
                    inv_line = {
                        'move_id': move_id.id,
                        'product_id': cargo.name.product_id.id,
                        'name': cargo.name.product_id.name,
                        'quantity': 1,
                        'account_id': parametros_obj.account_id_invoice.id,
                        'uom_id': uom.id,
                        'price_unit': cargo.valor,
                        'discount': 0
                    }
                    self.env['account.move.line'].create(inv_line)
                account_tax_obj = self.env['account.account'].search([
                    ('name', '=', 'IVA Retenido Efectivamente Cobrado')
                ])
                if account_tax_obj:
                    inv_tax = {
                        'move_id': move_id.id,
                        'name': 'Impuestos',
                        'account_id': account_tax_obj.id,
                        'amount': rec.iva_g + rec.r_iva_g,
                        'sequence': '0'
                    }
                    self.env['account.move.tax'].create(inv_tax)
                rec.move_id = move_id
                for viaje in self.viaje_id:
                    viaje.write({'en_factura': True})
                rec.write({'state': 'Validada'})

    def action_cancel(self):
        for rec in self:
            for viaje in rec.viaje_id:
                viaje.write({'en_factura': False})
            rec.write({'state': 'Cancelada'})

    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            vals['name'] = self.env['ir.sequence'].with_context(
                force_company=vals['company_id']
            ).next_by_code('Trafitec.Factura.Automatica') or ('Nuevo')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'Trafitec.Factura.Automatica'
            ) or ('Nuevo')
        return super(TrafitecFacturasAutomaticas, self).create(vals)
