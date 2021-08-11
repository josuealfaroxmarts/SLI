# -*- coding: utf-8 -*-

import datetime
from . import amount_to_text

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class cancelacion_cuentas(models.Model):
    _name = 'trafitec.cancelacioncuentas'
    _description = 'Cancelacion cuentas'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Folio', default='')
    persona_id = fields.Many2one(
        string='Persona',
        comodel_name='res.partner',
        required=True,
        tracking=True,
        domain="[('supplier','=',True),('customer','=',True)]"
    )
    referencia = fields.Text(
        string='Referencia',
        default='',
        required=True,
        tracking=True
    )
    detalles = fields.Text(
        string='Detalles',
        default='',
        required=True,
        tracking=True
    )
    fecha = fields.Date(
        string='Fecha',
        required=True,
        default=datetime.datetime.today(),
        tracking=True
    )
    moneda_id = fields.Many2one(
        string='Moneda',
        comodel_name='res.currency',
        required=True,
        tracking=True
    )
    total = fields.Monetary(
        string='Suma',
        currency_field='moneda_id',
        required=True,
        default=0,
        tracking=True
    )
    total_txt = fields.Char(string='Total en texto', default='')
    total_txt_ver = fields.Char(
        string='Cantidad con letra',
        related='total_txt'
    )
    abonos = fields.Monetary(
        string='Total',
        currency_field='moneda_id',
        default=0,
        store=True,
        compute='_total'
    )
    facturas_cliente_id = fields.One2many(
        string='Facturas cliente',
        comodel_name='trafitec.cancelacioncuentas.facturas.cliente',
        inverse_name='cancelacion_cuentas_id'
    )
    facturas_proveedor_id = fields.One2many(
        string='Facturas proveedor',
        comodel_name='trafitec.cancelacioncuentas.facturas.proveedor',
        inverse_name='cancelacion_cuentas_id'
    )
    facturas_relacion_id = fields.One2many(
        string='Relación',
        comodel_name='trafitec.cancelacioncuentas.relacion',
        inverse_name='cancelacion_cuentas_id'
    )
    diario_pago_cliente = fields.Many2one(
        string='Diario de pago a cliente',
        comodel_name='account.journal',
        required=True,
        tracking=True
    )
    diario_pago_proveedor = fields.Many2one(
        string='Diario de pago a proveedor',
        comodel_name='account.journal',
        required=True,
        tracking=True
    )
    persona_cobranza = fields.Char(
        string='Persona de cobranza',
        required=True,
        tracking=True
    )
    estado = fields.Boolean(string='Activa', default=True, tracking=True)
    state = fields.Selection([
            ('nuevo', 'Nuevo'),
            ('validado', 'Validado'),
            ('cancelado', 'Cancelado')
        ],
        string='Estado',
        default='nuevo',
        tracking=True
    )

    @api.depends('facturas_proveedor_id.abono')
    def _total(self):
        total = 0
        for f in self.facturas_id:
            total += f.abono
        self.abonos = total

    @api.onchange('total', 'moneda_id')
    def _onchange_total(self):
        for rec in self:
            if rec.total >= 0:
                if rec.moneda_id:
                    if rec.moneda_id.name.upper() in [
                        'MXN',
                        'MXP',
                        'PESOS',
                        'PESOS MEXICANOS'
                    ]:
                        rec.total_txt = amount_to_text(
                        ).amount_to_text_cheque(rec.total).upper()
                    else:
                        rec.total_txt = amount_to_text().amount_to_text(
                            rec.total
                        ).upper()
                else:
                    rec.total_txt = ''
            else:
                rec.total_txt = ''

    @api.onchange('persona_id', 'moneda_id')
    def _onchange_persona_id(self):
        for rec in self:
            lista_clientes = []
            lista_proveedores = []
            rec.facturas_cliente_id = []
            rec.facturas_proveedor_id = []
            rec.facturas_relacion_id = []

            if not rec.persona_id or not rec.moneda_id:
                return

            facturas_cliente = self.env['account.move'].search([
                    ('partner_id', '=', rec.persona_id.id),
                    ('move_type', '=', 'out_invoice'),
                    ('amount_residual', '>', 0),
                    ('state', '=', 'open'),
                    ('currency_id', '=', rec.moneda_id.id)
                ],
                order='date asc'
            )
            for invoice in facturas_cliente:
                nuevo = {
                    'factura_cliente_id': invoice.id,
                    'factura_cliente_total': invoice.amount_total,
                    'factura_cliente_saldo': invoice.amount_residual,
                    'abono': invoice.amount_residual
                }
                lista_clientes.append(nuevo)
            rec.facturas_cliente_id = lista_clientes

            facturas_proveedores = self.env['account.move'].search([
                    ('partner_id', '=', rec.persona_id.id),
                    ('move_type', '=', 'in_invoice'),
                    ('amount_residual', '>', 0),
                    ('state', '=', 'open'),
                    ('currency_id', '=', rec.moneda_id.id)
                ],
                order='date asc'
            )
            for invoice in facturas_proveedores:
                nuevo = {
                    'factura_proveedor_id': invoice.id,
                    'factura_proveedor_total': invoice.amount_total,
                    'factura_proveedor_saldo': invoice.amount_residual,
                    'abono': 0
                }
                lista_proveedores.append(nuevo)
            rec.facturas_proveedor_id = lista_proveedores

    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            vals['name'] = self.env['ir.sequence'].with_context(
                force_company=vals['company_id']
            ).next_by_code('Trafitec.CancelacionCuentas') or _('Nuevo')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'Trafitec.CancelacionCuentas'
            ) or _('Nuevo')

        if 'facturas_cliente_id' in vals:
            for invoice in vals['facturas_cliente_id']:
                total = invoice[2]['factura_cliente_total']
                saldo = invoice[2]['factura_cliente_saldo']
        nuevo = super(cancelacion_cuentas, self).create(vals)
        return nuevo

    def action_saldar(self):
        for rec in self:
            for invoice in rec.facturas_proveedor_id:
                invoice.abono = invoice.factura_proveedor_saldo

    def action_ceros(self):
        for rec in self:
            rec.facturas_relacion_id = None
            for invoice in rec.facturas_proveedor_id:
                invoice.abono = 0

    def action_distribuir(self):
        for rec in self:
            fc_saldo = 0
            fp_saldo = 0
            relacion = []
            error = False
            errores = ""
            if not rec.facturas_proveedor_id:
                error = True
                errores += "No hay facturas de proveedor.\n"
            if not rec.facturas_cliente_id:
                error = True
                errores += "No hay facturas de cliente.\n"
            if error:
                raise ValidationError(_(errores))
            rec.facturas_relacion_id = None
            for supplier_invoice in rec.facturas_proveedor_id:
                supplier_invoice.abono = 0
            for client_invoice in rec.facturas_cliente_id:
                fc_saldo = client_invoice.factura_cliente_saldo
                for supplier_invoice in rec.facturas_proveedor_id:
                    fp_saldo = (
                        supplier_invoice.factura_proveedor_id.amount_residual
                        - supplier_invoice.abono
                    )
                    if fc_saldo <= 0:
                        break
                    if fp_saldo <= 0:
                        continue
                    if fc_saldo >= fp_saldo:
                        supplier_invoice.abono += fp_saldo
                        fc_saldo -= fp_saldo
                        rnueva = {
                            'factura_cliente_id': (
                                client_invoice.factura_cliente_id.id
                            ),
                            'factura_proveedor_id': (
                                supplier_invoice.factura_proveedor_id.id
                            ),
                            'abono': fp_saldo
                        }
                        relacion.append(rnueva)
                    else:
                        supplier_invoice.abono += fc_saldo
                        rnueva = {
                            'factura_cliente_id': (
                                client_invoice.factura_cliente_id.id
                            ),
                            'factura_proveedor_id': (
                                supplier_invoice.factura_proveedor_id.id
                            ),
                            'abono': fc_saldo
                        }
                        relacion.append(rnueva)
                        fc_saldo = 0
            rec.facturas_relacion_id = relacion

    @api.constrains('total')
    def validar(self):
        for rec in self:
            error = False
            errores = ""
            if rec.total <= 0:
                error = True
                errores += "El total debe ser mayor a cero.\n"
            for client_invoice in rec.facturas_cliente_id:
                if client_invoice.abono < 0:
                    error = True
                    errores += (
                        "El abono de las facturas cliente debe ser mayor o "
                        + "igual a cero ({}).\n".format(
                            client_invoice.factura_cliente_id.name
                        )
                    )
                if client_invoice.abono > (
                    client_invoice.factura_cliente_saldo
                ):
                    error = True
                    errores += (
                        "El abono de las facturas cliente debe ser menor o "
                        + "igual al saldo de la factuta ({}).\n".format(
                            client_invoice.factura_cliente_id.name
                        )
                    )
            for supplier_invoice in self.facturas_proveedor_id:
                if supplier_invoice.abono < 0:
                    error = True
                    errores += (
                        "El abono de las facturas proveedor debe ser mayor o "
                        + "igual a cero ({}).\n".format(
                            supplier_invoice.factura_proveedor_id.name
                        )
                    )
                if supplier_invoice.abono > (
                    supplier_invoice.factura_proveedor_saldo
                ):
                    error = True
                    errores += (
                        "El abono de las facturas proveedor debe ser menor o "
                        + "igual al saldo de la factuta ({}).\n".format(
                            supplier_invoice.factura_proveedor_id.name
                        )
                    )
            if error:
                raise ValidationError(_(errores))

    def _aplicapago(
        self,
        diario_id,
        factura_id,
        abono,
        moneda_id,
        persona_id,
        tipo='supplier',
        subtipo='inbound'
    ):
        for rec in self:
            metodo = 2
            if subtipo == 'inbound':
                metodo = 1
            valores = {
                'journal_id': diario_id,
                'payment_method_id': metodo,
                'payment_date': datetime.datetime.now().date(),
                'communication': 'Pago por cancelación de cuentas {}.'.format(
                    str(rec.name)
                ),
                'move_ids': [(4, factura_id, None)],
                'payment_type': subtipo,
                'amount': abono,
                'currency_id': moneda_id,
                'partner_id': persona_id,
                'partner_type': tipo,
            }
            pago = self.env['account.payment'].create(valores)
            pago.post()
            return pago

    def action_validar(self):
        for rec in self:
            error = False
            errores = ""
            if not rec.facturas_relacion_id:
                error = True
                errores += (
                    "Debe especificar la relacion de facturas y abonos.\n"
                )
            totalabonos = 0
            for invoice in rec.facturas_relacion_id:
                totalabonos += invoice.abono
            if totalabonos != rec.total:
                error = True
                errores += (
                    "El total de los abonos debe ser igual al total del "
                    + "documento.\n"
                )
            if (
                not rec.diario_pago_cliente.default_debit_account_id
                or not rec.diario_pago_cliente.default_credit_account_id
            ):
                error = True
                errores += (
                    "El diario de pago a cliente no tiene cuentas contables "
                    + "configuradas.\n"
                )
            if (
                not rec.diario_pago_proveedor.default_debit_account_id
                or not rec.diario_pago_proveedor.default_credit_account_id
            ):
                error = True
                errores += (
                    "El diario de pago a proveedor no tiene cuentas contables"
                    + " configuradas.\n"
                )
            for invoice in rec.facturas_relacion_id:
                fc = invoice.factura_cliente_id
                fp = invoice.factura_proveedor_id
                abono = invoice.abono
                if not fc or not fp:
                    continue
                if abono <= 0:
                    continue
                fc_o = rec.env['account.move'].search([('id', '=', fc.id)])
                fp_o = rec.env['account.move'].search([('id', '=', fp.id)])
                if abono > fc_o.amount_residual:
                    error = True
                    errores += (
                        "El abono {} es mayor al saldo de la factura cliente "
                        + "{}/{}.\n".format(
                            abono,
                            fc.name,
                            fc.amount_residual
                        )
                    )
                if abono > fp_o.amount_residual:
                    error = True
                    errores += (
                        "El abono {} es mayor al saldo de la factura proveedor"
                        + " {}/{}.\n".format(
                            abono,
                            fp.name,
                            fp.amount_residual
                        )
                    )
            if error:
                raise ValidationError(_(errores))
            if rec.state == 'nuevo':
                for invoice in rec.facturas_relacion_id:
                    abono = invoice.abono
                    if abono <= 0:
                        continue
                    pago1 = None
                    pago2 = None
                    pago1 = self._aplicapago(
                        rec.diario_pago_cliente.id,
                        invoice.factura_cliente_id.id,
                        abono,
                        rec.moneda_id.id,
                        rec.persona_id.id,
                        'customer',
                        'inbound'
                    )
                    pago2 = self._aplicapago(
                        rec.diario_pago_proveedor.id,
                        invoice.factura_proveedor_id.id,
                        abono,
                        rec.moneda_id.id,
                        rec.persona_id.id,
                        'supplier',
                        'outbound'
                    )
                rec.state = 'validado'

    def action_cancelar(self):
        for rec in self:
            if rec.state == 'nuevo' or rec.state == 'validado':
                rec.state = 'cancelado'

    def unlink(self):
        for rec in self:
            if rec.state == 'validado':
                raise ValidationError(_("El documento ya esta validado."))
        super(cancelacion_cuentas, self).unlink()
