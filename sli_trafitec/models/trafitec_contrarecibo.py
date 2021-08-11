# -*- coding: utf-8 -*-

import datetime
import math
from odoo import models, fields, api, tools
from odoo.exceptions import UserError


class TrafitecContrarecibo(models.Model):
    _name = 'trafitec.contrarecibo'
    _description = 'Contrarecibo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    fletes = fields.Float(
        string='Fletes',
        compute='_compute_fletes',
        store=True
    )
    fletes_ver = fields.Float(
        string='+Fletes',
        related='fletes',
        readonly=True
    )
    fletesx = fields.Float(string='+Fletes_')
    maniobras = fields.Float(
        string='Maniobras',
        compute='_compute_maniobras'
    )
    maniobras_ver = fields.Float(
        string='+Maniobras',
        related='maniobras',
        readonly=True
    )
    cargosadicionales_total = fields.Float(
        string='+Cargos adicionales',
        default=0,
        store=True,
        compute=_compute_otros,
        help='Total de cargos adicionales.'
    )
    cargosadicionales_total_ver = fields.Float(
        string='Cargos adicionales',
        related='cargosadicionales_total',
        default=0,
        help='Total de cargos adicionales.'
    )
    maniobrasx = fields.Float(string='+Maniobras_')
    total_abono_des = fields.Float(
        string='Total de abono descuento',
        compute='_check_descuentos'
    )
    total_abonox_des = fields.Float(string='Total de abono descuento_')
    total_saldo_des = fields.Float(
        string='Total de saldo descuento',
        compute='_check_descuentos'
    )
    total_saldox_des = fields.Float(string='Total de saldo descuento_')
    total_abono_coms = fields.Float(
        string='Total de abono comision',
        compute='_check_comisiones'
    )
    total_abonox_coms = fields.Float(string='Total de abono comision_')
    total_saldo_coms = fields.Float(
        string='Total de saldo comision',
        compute='_check_comisiones'
    )
    total_saldox_coms = fields.Float(string='Total de saldo comision_')
    diferencia = fields.Float(
        string='Diferencias',
        compute='_compute_diferencia'
    )
    diferencia_ver = fields.Float(
        string='Diferencia',
        related='diferencia'
    )
    diferenciax = fields.Float(string='Diferencia_')
    notacargo = fields.Float(
        string='Nota cargo',
        compute='_compute_notacargo'
    )
    notacargo_ver = fields.Float(
        string='Nota de cargo',
        related='notacargo'
    )
    notacargox = fields.Float(string='Nota de cargo_')
    name = fields.Char(
        string='Folio',
        default='Nuevo'
    )
    asociado_id = fields.Many2one(
        'res.partner',
        string='Asociado',
        domain=[
            ('asociado', '=', True),
            ('supplier', '=', True)
        ],
        required=True,
        tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        required=True,
        default=lambda self: self._predeterminados_moneda(),
        tracking=True
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'trafitec.contrarecibo'
        )
    )
    viaje_id = fields.Many2many(
        'trafitec.viajes',
        'contrarecibo_viaje_relation',
        'contrarecibo_id', 'viajes_id',
        string='Viajes',
        domain=[
            ('asociado_id', '=', asociado_id),
            ('moneda', '=', currency_id),
            ('lineanegocio', '=', 'lineanegocio'),
            ('state', '=', 'Nueva'),
            ('en_contrarecibo', '=', False),
            ('tipo_viaje', '=', 'Normal')
        ]
    )
    cobrar_descuentos = fields.Selection([
            ('No cobrar', 'No cobrar'),
            ('Todos', 'Todos'),
            ('Viajes del contrarecibo', 'Viajes del contrarecibo')
        ],
        string='Cobrar descuentos',
        default='Todos',
        required=True,
        tracking=True
    )
    cobrar_comisiones = fields.Selection([
            ('No cobrar', 'No cobrar'),
            ('Viajes del contrarecibo', 'Viajes del contrarecibo'),
            ('Todos los viajes', 'Todos los viajes')
        ],
        string='Cobrar comisiones',
        default='Todos los viajes',
        required=True,
        tracking=True
    )
    iva_option = fields.Selection(
        [
            ('CIR', 'Con IVA y con RIVA'),
            ('SIR', 'Sin IVA y sin RIVA'),
            ('CISR', 'Con IVA y sin RIVA')
        ],
        string='IVA',
        default='CIR',
        required=True,
        tracking=True)
    state = fields.Selection(
        [
            ('Nueva', 'Nueva'),
            ('Validada', 'Validada'),
            ('Cancelada', 'Cancelada')
        ],
        string='Estado',
        default='Nueva',
        tracking=True
    )
    lineanegocio = fields.Many2one(
        'trafitec.lineanegocio',
        string='Linea de negocios',
        required=True,
        default=lambda self: self._predeterminados_lineanegocio(),
        tracking=True
    )
    move_id = fields.Many2one(
        'account.move',
        string='Factura proveedor',
        domain=[
            ('move_type', '=', 'out_invoice'),
            ('partner_id', '=', asociado_id),
            ('amount_total', '>', 0),
            ('factura_encontrarecibo', '=', False),
            ('state', '=', 'posted'),
            ('es_cartaporte', '=', True)
        ],
        tracking=True
    )
    fecha = fields.Date(
        string='Fecha',
        readonly=True,
        index=True,
        copy=False,
        default=fields.Datetime.now,
        tracking=True
    )
    normal = fields.Boolean(
        string='Normal',
        default=True,
        tracking=True
    )
    psf = fields.Boolean(
        string='PSF',
        default=False,
        tracking=True
    )
    factura_actual = fields.Many2one(
        'account.move',
        string='Factura proveedor actual',
        domain=[
            ('move_type', '=', 'in_invoice'),
            ('partner_id', '=', asociado_id),
            ('amount_total', '>', 0)
        ]
    )
    cargospendientes_id = fields.One2many(
        comodel_name='trafitec.cargospendientes',
        inverse_name='contrarecibo_id',
        string='Cargos pendientes'
    )
    x_folio_trafitecw = fields.Char(
        string='Folio Trafitec Windows',
        help='Folio del contra recibo en Trafitec para windows.',
        tracking=True
    )
    mermas_bol = fields.Boolean(
        string='Merma',
        default=False,
        tracking=True
    )
    mermas_des = fields.Float(
        string='Descuento de merma',
        store=False,
        compute='_compute_mermas_despues'
    )
    mermas_des_ver = fields.Float(
        string='-Merma',
        related='mermas_des'
    )
    mermasx_des = fields.Float(store=True)
    mermas_antes = fields.Float(
        store=False,
        compute='_compute_mermas_antes'
    )
    mermas_antes_ver = fields.Float(
        string='Merma antes',
        related='mermas_antes'
    )
    mermasx_antes = fields.Float(store=True)
    descuento_bol = fields.Boolean(
        string='Descuento',
        default=False,
        tracking=True
    )
    descuento_des = fields.Float(
        string='Descuentos',
        store=False,
        compute='_check_descuentos'
    )
    descuento_des_ver = fields.Float(
        string='-Descuento ',
        related='descuento_des'
    )
    descuentox_des = fields.Float(store=True)
    descuento_antes = fields.Float(
        string='Descuento',
        store=False,
        compute='_check_descuentos'
    )
    descuento_antes_ver = fields.Float(
        string='-Descuento',
        related='descuento_antes'
    )
    descuentox_antes = fields.Float(store=True)
    comision_bol = fields.Boolean(
        string='Comisions ',
        default=False,
        tracking=True
    )
    comision_des = fields.Float(
        string='-Comisiones',
        store=False,
        compute='_check_comisiones'
    )
    comision_des_ver = fields.Float(
        string='-Comision',
        related='comision_des'
    )
    comisionx_des = fields.Float(store=True)
    comisiones_antes = fields.Float(
        string='-Comisiones ',
        store=False,
        compute='_check_comisiones'
    )
    comisiones_antes_ver = fields.Float(
        string='- Comisiones',
        related='comisiones_antes'
    )
    comisionesx_antes = fields.Float(
        string='-Comisiones_',
        store=True
    )
    prontopago_bol = fields.Boolean(
        string='Pronto pago',
        default=False,
        tracking=True
    )
    prontopago_des = fields.Float(
        string='- Pronto pago',
        store=False,
        compute='_compute_prontopago'
    )
    prontopago_des_ver = fields.Float(
        string='-Pronto pago',
        related='prontopago_des'
    )
    prontopagox_des = fields.Float(
        string='-Pronto pago_',
        store=True
    )
    prontopago_antes = fields.Float(
        string='-Pronto pago ',
        store=False,
        compute='_compute_prontopago'
    )
    prontopago_antes_ver = fields.Float(
        string='- Pronto pago ',
        related='prontopago_antes'
    )
    prontopagox_antes = fields.Float(
        string='- Pronto pago_',
        store=True
    )
    subtotal_g = fields.Float(
        string='Subtotal',
        store=True,
        compute='_compute_subtotal'
    )
    subtotal_gSM = fields.Float(
        string='Subtotal SM (Sin maniobras)',
        store=True,
        compute='_compute_subtotalSM'
    )
    iva_g = fields.Float(
        string='IVA ',
        store=True,
        readonly=True,
        compute='_compute_iva_g'
    )
    r_iva_g = fields.Float(
        string='RIVA',
        store=True,
        compute='_compute_r_iva_g'
    )
    total_g = fields.Float(
        store=True,
        compute='_compute_total_g'
    )
    subtotal_g_ver = fields.Float(
        string='Subtotal ',
        related='subtotal_g',
        readonly=True
    )
    iva_g_ver = fields.Float(
        string=' IVA ',
        related='iva_g',
        readonly=True
    )
    r_iva_g_ver = fields.Float(
        string='RIVA ',
        related='r_iva_g',
        readonly=True
    )
    total_g_ver = fields.Float(
        string='Total ',
        related='total_g',
        readonly=True
    )
    subtotalx = fields.Float(
        string='Subtotal_',
        store=True
    )
    subtotalx_sm = fields.Float(
        string='Subtotal sm_',
        store=True
    )
    ivax = fields.Float(
        string='IVA_',
        store=True
    )
    rivax = fields.Float(
        string='RIVA_',
        store=True
    )
    totalx = fields.Float(
        string='Total_',
        store=True
    )
    folio = fields.Char(
        string='Folio carta porte',
        related='move_id.ref',
        store=True
    )
    fecha_porte = fields.Date(
        string='Fecha ',
        related='move_id.date',
        store=True
    )
    fletes_carta_porte = fields.Float(string='Fletes ')
    subtotal = fields.Monetary(
        string='Subtotal ',
        related='move_id.amount_untaxed'
    )
    observaciones = fields.Text(
        string='Observaciones',
        tracking=True
    )
    r_iva = fields.Float(
        string='R. IVA',
        compute='_compute_r_iva_carta'
    )
    total = fields.Monetary(
        string='Total',
        related='move_id.amount_total'
    )
    carta_porte = fields.Boolean(string='Carta porte')
    cfd = fields.Boolean(string='CFD')
    iva = fields.Float(
        string='IVA ',
        compute='_compute_iva_carta'
    )
    descuento_id = fields.One2many(
        comodel_name='trafitec.con.descuentos',
        inverse_name='linea_id'
    )
    comision_id = fields.One2many(
        comodel_name='trafitec.con.comision',
        inverse_name='line_id'
    )
    cargosadicionales_id = fields.One2many(
        string='Cargos adicionales ',
        comodel_name='trafitec.contrarecibos.cargos',
        inverse_name='contrarecibo_id'
    )
    folio_diferencia = fields.Many2one(
        'account.move',
        readonly=True,
        string='Folio por diferencia'
    )
    folio_merma = fields.Many2one(
        'account.move',
        readonly=True,
        string='Folio por merma'
    )
    folio_descuento = fields.Many2one(
        'account.move',
        readonly=True,
        string='Folio por descuento'
    )
    folio_comision = fields.Many2one(
        'account.move',
        readonly=True,
        string='Folio por comision'
    )
    folio_prontopago = fields.Many2one(
        'account.move',
        readonly=True,
        string='Folio por pronto pago'
    )
    observaciones = fields.Text(string='Observaciones')

    def totales(self):
        for rec in self:
            flete = 0
            seguro = 0
            maniobras = 0
            cargosadicionales = 0
            mermas = 0
            mermas_an = 0
            mermas_de = 0
            descuentos_viajes = 0
            descuentos = 0
            descuentos_an = 0
            descuentos_de = 0
            comisiones_viajes = 0
            comisiones = 0
            comisiones_an = 0
            comisiones_de = 0
            prontopago = 0
            prontopago_an = 0
            prontopago_de = 0
            subtotal = 0
            iva = 0
            riva = 0
            total = 0
            parametros_obj = rec._get_parameter_company(rec)
            for v in rec.viaje_id:
                flete += v.flete_asociado
                maniobras += v.maniobras
                mermas += v.merma_cobrar_pesos
                if rec.mermas_bol:
                    mermas_an = 0
                    mermas_de += v.merma_cobrar_pesos
                else:
                    mermas_an += v.merma_cobrar_pesos
                    mermas_de = 0
                if v.pronto_pago:
                    prontopago += (
                        v.flete_asociado
                        * (parametros_obj.pronto_pago / 100)
                    )
            for ca in rec.cargosadicionales_id:
                cargosadicionales += ca.valor
            for d in rec.descuento_id:
                descuentos += d.abono
                if d.viaje_id in rec.viaje_id:
                    descuentos_viajes += d.abono
            if rec.cobrar_descuentos == 'No cobrar':
                descuentos_an = 0
                descuentos_de = 0
            if rec.cobrar_descuentos == 'Todos':
                if rec.descuento_bol:
                    descuentos_an = 0
                    descuentos_de = descuentos
                else:
                    descuentos_an = descuentos
                    descuentos_de = 0
            if rec.cobrar_descuentos == 'Viajes del contrarecibo':
                if rec.descuento_bol:
                    descuentos_an = 0
                    descuentos_de = descuentos_viajes
                else:
                    descuentos_an = descuentos_viajes
                    descuentos_de = 0
            for c in rec.comision_id:
                comisiones += c.saldo
                if c.viaje_id in rec.viaje_id:
                    comisiones_viajes += c.saldo
            if rec.cobrar_comisiones == 'No cobrar':
                comisiones_an = 0
                comisiones_de = 0
            if rec.cobrar_comisiones == 'Todos los viajes':
                if rec.comision_bol:
                    comisiones_an = 0
                    comisiones_de = comisiones
                else:
                    comisiones_an = comisiones
                    comisiones_de = 0
            if rec.cobrar_comisiones == 'Viajes del contrarecibo':
                if rec.comision_bol:
                    comisiones_an = 0
                    comisiones_de = comisiones_viajes
                else:
                    comisiones_an = comisiones_viajes
                    comisiones_de = 0
            if rec.prontopago_bol:
                prontopago_an = 0
                prontopago_de = prontopago
            else:
                prontopago_an = prontopago
                prontopago_de = 0
            subtotal = (
                flete
                + seguro
                + maniobras
                + cargosadicionales
                - mermas_an
                - descuentos_an
                - comisiones_an
                - prontopago_an
            )
            if rec.iva_option == 'CIR' or rec.iva_option == 'CISR':
                iva = subtotal * 0.16
            if rec.iva_option == 'CIR':
                riva = subtotal * 0.04
            total = subtotal + iva - riva
            return {
                'flete': flete,
                'seguro': seguro,
                'maniobras': maniobras,
                'mermas': mermas,
                'mermas_an': mermas_an,
                'mermas_de': mermas_de,
                'descuentos': descuentos,
                'descuentos_an': descuentos_an,
                'descuentos_de': descuentos_de,
                'comisiones': comisiones,
                'comisiones_an': comisiones_an,
                'comisiones_de': comisiones_de,
                'prontopago': prontopago,
                'prontopago_an': prontopago_an,
                'prontopago_de': prontopago_de,
                'subtotal': subtotal,
                'iva': iva,
                'riva': riva,
                'total': total
            }

    @api.model
    def _predeterminados_moneda(self):
        emp = self.env['res.company']._company_default_get('sli_trafitec')
        res = self.env['trafitec.parametros'].search([
            ('company_id', '=', emp.id)
        ])
        return res[0].cr_moneda_id or False

    @api.model
    def _predeterminados_lineanegocio(self):
        res = self.env['trafitec.parametros'].search([])
        return res[0].cr_lineanegocio_id or False

    def _factura_relacionada(self, crear, vals):
        condiciones = []
        if 'move_id' in vals:
            if vals['move_id']:
                condiciones.append(('move_id', '=', vals['move_id']))
            else:
                return
        else:
            return
        for rec in self:
            if not crear:
                condiciones.append(('id', '!=', rec.id))
            contrarecibo = self.env['trafitec.contrarecibo'].search(
                condiciones
            )
            folios = ''
            if contrarecibo:
                for cr in contrarecibo:
                    folios += cr.name + ' '
                raise UserError((
                    'La carta porte ya esta en otro contra recibo '
                    + '({}).'.format(folios)
                ))

    def _carga_cargospendientes(self):
        for rec in self:
            rec.cargospendientes_id = []
            cargosx = []
            cargos = self.env['trafitec.cargospendientes']
            cargospendientes = self.env['trafitec.cargos'].search([
                ('asociado_id', '=', self.asociado_id.id),
                ('tipo_cargo', '=', 'descuentos')
            ])
            for c in cargospendientes:
                nuevo = {
                    'descuento_id': c.id,
                    'total': c.monto,
                    'abonos': c.abonado,
                    'saldo': c.saldo,
                    'detalles': c.descuento_id.concepto.name
                }
                cargosx.append(nuevo)
            rec.cargospendientes_id = cargosx

    def write(self, vals):
        self._factura_relacionada(False, vals)
        cr = super(TrafitecContrarecibo, self).write(vals)
        return cr

    def unlink(self):
        raise UserError(
            ('Alerta..\nNo esta permitido borrar contra recibos.')
        )
        for reg in self:
            if reg.state == 'Validada':
                raise UserError((
                    'Alerta..\nNo se puede eliminar si el contra '
                    + 'recibo({}) esta validado.'.format(reg.name)
                ))
        return super(TrafitecContrarecibo, self).unlink()

    @api.onchange('normal')
    def _onchange_tipo_normal_check(self):
        for rec in self:
            if rec.normal and rec.psf:
                rec.psf = False

    @api.onchange('psf')
    def _onchange_tipo_psf_check(self):
        for rec in self:
            if rec.normal and rec.psf:
                rec.normal = False

    def _crear_factura_proveedor(self, vals):
        for rec in self:
            rec._validar_viajes_seleccionados(vals)
            journal_obj = vals.env['account.journal'].search([
                ('name', '=', 'Proveedores Transportistas')
            ])
            account_obj = vals.env['account.account'].search([
                ('name', '=', 'Proveedores Transportistas')
            ])
            valores = {
                'origin': vals.name,
                'move_type': 'in_invoice',
                'date': datetime.datetime.now(),
                'partner_id': vals.asociado_id.id,
                'journal_id': journal_obj.id,
                'company_id': vals.company_id.id,
                'currency_id': vals.currency_id.id,
                'account_id': account_obj.id,
                'ref': 'Factura generada del contra recibo {} '.format(
                    vals.name
                )
            }
            move_id = vals.env['account.move'].create(valores)
            product_obj = vals.env['product.product'].search([
                ('default_code', '=', 'ServFletGran')
            ])
            inv_line = {
                'move_id': move_id.id,
                'product_id': product_obj.id,
                'name': 'Factura generada del contra recibo {} '.format(
                    vals.name
                ),
                'quantity': 1,
                'account_id': account_obj.id,
                'uom_id': product_obj.product_tmpl_id.uom_id.id,
                'price_unit': vals.subtotal,
                'price_unit': vals.subtotal,
                'discount': 0
            }
            vals.env['account.move.line'].create(inv_line)
            account_tax_obj = vals.env['account.account'].search([
                ('name', '=', 'IVA Retenido Efectivamente Cobrado')
            ])
            inv_tax = {
                'move_id': move_id.id,
                'name': vals.iva_option,
                'account_id': account_tax_obj.id,
                'amount': vals.iva + vals.r_iva,
                'sequence': '0'
            }
            vals.env['account.move.tax'].create(inv_tax)
            self._cambiar_estado_viaje(vals)
            return move_id

    def _cambiar_estado_viaje(self, vals):
        for viaje in vals.viaje_id:
            viaje.en_contrarecibo = True

    def _validar_viajes_seleccionados(self, vals):
        for viaje in vals.viaje_id:
            if viaje.en_contrarecibo:
                raise UserError((
                    'Error !\nEl viaje con el folio {}'.format(viaje.name)
                    + ' ya fue asignado en otro contra recibo.'
                ))

    def _cobrar_descuentos(self):
        for rec in self:
            if rec.cobrar_descuentos:
                if rec.cobrar_descuentos == 'Todos':
                    for descuento in rec.descuento_id:
                        obj_descuento = rec.env['trafitec.descuentos'].search(
                            [('id', '=', descuento.descuento_fk.id)]
                        )
                        if descuento.abono > obj_descuento.saldo:
                            raise UserError(
                                'Error !\nEl abono del descuento ({})'.format(
                                    descuento.abono
                                )
                                + ' es mayor al saldo del descuento '
                                + '({}).'.format(obj_descuento.saldo)
                            )
                        if descuento.abono <= 0:
                            continue
                        nuevo = {
                            'name': descuento.abono,
                            'fecha': datetime.datetime.now().date(),
                            'observaciones': (
                                'Generada en el contra recibo '
                                + '{}'.format(descuento.linea_id.name)
                            ),
                            'tipo': 'contrarecibo',
                            'abonos_id': descuento.descuento_fk.id,
                            'contrarecibo_id': rec.id,
                            'permitir_borrar': True
                        }
                        self.env['trafitec.descuentos.abono'].create(nuevo)
                if rec.cobrar_descuentos == 'Viajes del contrarecibo':
                    amount = 0
                    for descuento in rec.descuento_id:
                        if descuento.viaje_id in rec.viaje_id:
                            obj_descuento = self.env[
                                'trafitec.descuentos'
                            ].search([('id', '=', descuento.descuento_fk.id)])
                            if descuento.abono > obj_descuento.saldo:
                                raise UserError(
                                    'Error !\nEl abono del descuento '
                                    + '({}) es mayor al saldo del '.format(
                                        descuento.saldo
                                    )
                                    + 'descuento ({}).'.format(
                                        obj_descuento.saldo
                                    )
                                )
                            if descuento.abono <= 0:
                                continue
                            nuevo = {
                                'name': descuento.abono,
                                'fecha': datetime.datetime.now(),
                                'observaciones': (
                                    'Generada en el contra recibo '
                                    + '{}'.format(descuento.linea_id.name)
                                ),
                                'tipo': 'contrarecibo',
                                'abonos_id': descuento.descuento_fk.id,
                                'contrarecibo_id': rec.id,
                                'permitir_borrar': True
                            }
                            self.env['trafitec.descuentos.abono'].create(nuevo)

    def _cobrar_comisiones(self):
        for rec in self:
            if rec.cobrar_comisiones:
                if rec.cobrar_comisiones == 'Todos los viajes':
                    for comisi in rec.comision_id:
                        obj_comisi = self.env['trafitec.cargos'].search([
                            ('id', '=', comisi.cargo_id.id)
                        ])
                        if obj_comisi.saldo != comisi.saldo:
                            raise UserError(
                                'Error !\nEl abono de comisión ({})'.format(
                                    comisi.saldo
                                )
                                + ' es mayor al saldo de la comision '
                                + '({}).'.format(obj_comisi.saldo)
                            )
                        self.env['trafitec.comisiones.abono'].create(
                            {
                                'name': comisi.saldo,
                                'fecha': datetime.datetime.now().date(),
                                'abonos_id': comisi.cargo_id.id,
                                'observaciones': (
                                    'Generada en el contra recibo {}'.format(
                                        comisi.line_id.name
                                    )
                                ),
                                'tipo': 'contrarecibo',
                                'contrarecibo_id': rec.id,
                                'permitir_borrar': True
                            }
                        )
                if rec.cobrar_comisiones == 'Viajes del contrarecibo':
                    for comisi in rec.comision_id:
                        if comisi.viaje_id in rec.viaje_id:
                            obj_comisi = self.env['trafitec.cargos'].search([
                                ('id', '=', comisi.cargo_id.id)
                            ])
                            if obj_comisi.saldo != comisi.saldo:
                                raise UserError(
                                    'Error !\nEl abono de comisión '
                                    + '({}) es mayor al saldo de la '.format(
                                        comisi.saldo
                                    )
                                    + 'comision ({}).'.format(
                                        obj_comisi.saldo
                                    )
                                )
                            self.env['trafitec.comisiones.abono'].create(
                                {
                                    'name': comisi.saldo,
                                    'fecha': datetime.datetime.now().date(),
                                    'abonos_id': comisi.cargo_id.id,
                                    'observaciones': (
                                        'Generada en el contra recibo '
                                        + '{}'.format(
                                            comisi.line_id.name
                                        )
                                    ),
                                    'tipo': 'contrarecibo',
                                    'contrarecibo_id': rec.id,
                                    'permitir_borrar': True
                                }
                            )

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
        if abono <= 0:
            return
        metodo = 2
        if subtipo == 'inbound':
            metodo = 1
        valores = {
            'journal_id': diario_id,
            'payment_method_id': metodo,
            'payment_date': datetime.datetime.now().date(),
            'communication': 'Pago desde codigo por:{} de tipo:{} '.format(
                str(abono),
                tipo
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

    def truncar2(self, valor):
        return math.trunc(valor * 100.00) / 100.00

    def truncar3(self, valor):
        return math.trunc(valor * 1000.00) / 100.00

    def truncar4(self, valor):
        return math.trunc(valor * 10000.00) / 10000.00

    def _generar_nota_cargo(self, vals, tipo, parametros_obj):
        configuracion_trafitec = vals.env['trafitec.parametros'].search([
            ('company_id', '=', vals.company_id.id)
        ])
        diario = vals.env['account.journal'].search([
            ('id', '=', configuracion_trafitec.cr_diario_id.id)
        ])
        nca_diario_pagos_id = vals.env['account.journal'].search([
            ('id', '=', configuracion_trafitec.nca_diario_pagos_id.id)
        ])
        nca_diario_cobros_id = vals.env['account.journal'].search([
            ('id', '=', configuracion_trafitec.nca_diario_cobros_id.id)
        ])
        plancontable = vals.env['account.account'].search([
            ('id', '=', configuracion_trafitec.cr_plancontable_id.id)
        ])
        error = False
        errores = ''
        if not vals.asociado_id.customer:
            error = True
            errores += '\nEl asociado tambien debe ser cliente.'
        if not diario:
            error = True
            errores += (
                '\nNo se ha especificado un diario en contabilidad con el '
                + 'nombre: Proveedores Transportistas.'
            )
        if not plancontable:
            error = True
            errores += (
                '\nNo se ha especificado un plan contable en contabilidad con'
                + ' el nombre: Proveedores Transportistas.'
            )
        if not configuracion_trafitec:
            error = True
            errores += (
                '\nNo se ha especificado los parametros de trafitec:'
                + ' Trafitec/Sistema/Parametros.'
            )
        if not vals.asociado_id.uso_cfdi_id:
            error = True
            errores += '\nDebe especificar el uso del cfdi del Cliente.'
        if not vals.asociado_id.pay_method_id:
            error = True
            errores += '\nDebe especificar el método de pago del Cliente.'
        if not parametros_obj.iva.account_id:
            error = True
            errores += '\nLos impuestos de IVA no tienen cuenta de impuestos.'
        if not parametros_obj.retencion.account_id:
            error = True
            errores += (
                '\nLos impuestos de IVA retenido no tiene cuenta de '
                + 'impuestos.'
            )
        if error:
            raise UserError(
                ('Alerta..\n' + errores)
            )
        for rec in self:
            if tipo == 'merma':
                monto = rec.mermas_des
            elif tipo == 'descuento':
                monto = rec.descuento_des
            elif tipo == 'comision':
                monto = rec.comision_des
            elif tipo == 'pronto':
                monto = rec.prontopago_des
            elif tipo == 'diferencia':
                monto = rec.diferencia
            if monto <= 0:
                return
            piva = (parametros_obj.iva.amount / 100)
            priva = (parametros_obj.retencion.amount / 100)
            c_subtotal = rec.truncar4(monto / (1 + (piva + priva)))
            c_iva = c_subtotal * piva
            c_riva = c_subtotal * priva
            c_total = c_subtotal + c_iva + c_riva
            subtotal = c_subtotal
            iva = c_iva
            riva = c_riva
            total = c_total
            if total <= 0:
                raise UserError(
                    ('Alerta..\nEl total de la nota es menor o igual a cero.')
                )
                return
            valores = {
                'origin': vals.name,
                'move_type': 'out_invoice',
                'date': datetime.datetime.now(),
                'partner_id': vals.asociado_id.id,
                'journal_id': diario.id,
                'company_id': vals.company_id.id,
                'currency_id': vals.currency_id.id,
                'uso_cfdi_id': vals.asociado_id.uso_cfdi_id.id,
                'pay_method_id': vals.asociado_id.pay_method_id.id,
                'metodo_pago_id': configuracion_trafitec.metodo_pago_id.id,
                'account_id': plancontable.id,
                'ref': (
                    'Nota de cargo por {} generada del contra recibo '.format(
                        tipo
                    )
                    + '{} / {} '.format(vals.name, rec.move_id.ref)
                )
            }
            move_id = vals.env['account.move'].create(valores)
            move_id.update({'pay_method_ids': [
                (6, 0, [vals.asociado_id.pay_method_id.id])
            ]})
            valores = {
                'move_id': move_id,
                'pay_method_id': vals.asociado_id.pay_method_id.id
            }
            product = self.env['product.product'].search([
                ('product_tmpl_id', '=', parametros_obj.product.id)
            ])
            inv_line = {
                'move_id': move_id.id,
                'product_id': product.id,
                'name': (
                    'Nota de cargo por {} generada del contra recibo'.format(
                        tipo
                    )
                    + ' {} / {} '.format(vals.name, rec.move_id.ref)
                ),
                'account_id': product.property_account_income_id.id,
                'uom_id': parametros_obj.uom.uom_id.id,
                'quantity': 1,
                'price_unit': subtotal,
                'discount': 0
            }
            linea_id = vals.env['account.move.line'].create(inv_line)
            linea_id.update({'invoice_line_tax_ids': [
                (6, 0, [parametros_obj.iva.id, parametros_obj.retencion.id])
            ]})
            inv_tax = {
                'move_id': move_id.id,
                'name': parametros_obj.iva.name,
                'account_id': parametros_obj.iva.account_id.id,
                'amount': iva,
                'tax_id': parametros_obj.iva.id,
                'sequence': '0'
            }
            inv_ret = {
                'move_id': move_id.id,
                'name': parametros_obj.retencion.name,
                'account_id': parametros_obj.retencion.account_id.id,
                'amount': riva,
                'tax_id': parametros_obj.retencion.id,
                'sequence': '0'
            }
            try:
                move_id.compute_taxes()
            except Exception as err:
                raise UserError(
                    'Error al aplicar los impuestos de la nota de cargo: '
                    + '{}.'.format(str(err))
                )
            try:
                move_id.action_invoice_open()
            except Exception as err:
                raise UserError(
                    'Error al validar la nota de cargo: {}.'.format(str(err))
                )
            if move_id.state != 'open':
                raise UserError(
                    'No fue posible validar la nota de cargo: {}.'.format(
                        str(move_id.state)
                    )
                )
            if total > 0:
                rec._aplicapago(
                    nca_diario_pagos_id.id,
                    rec.move_id.id, move_id.amount_total,
                    vals.currency_id.id,
                    rec.asociado_id.id,
                    'supplier',
                    'outbound'
                )
                rec._aplicapago(
                    nca_diario_cobros_id.id,
                    move_id.id,
                    move_id.amount_total,
                    vals.currency_id.id,
                    rec.asociado_id.id,
                    'customer',
                    'inbound'
                )
            return move_id

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

    def action_available(self):
        for rec in self:
            error = False
            errores = ''
            if not rec.move_id:
                error = True
                errores += 'Debe especificar la carta porte.\r\n'
            if not rec.viaje_id:
                error = True
                errores += 'Debe especificar al menos un viaje.\r\n'
            rec.fletesx = 0
            rec.maniobrasx = 0
            for v in rec.viaje_id:
                rec.fletesx += v.flete_asociado
                rec.maniobrasx += v.maniobras
            rec.total_abonox_des = rec.total_abono_des
            rec.total_saldox_des = rec.total_saldo_des
            rec.total_abonox_coms = rec.total_abono_coms
            rec.total_saldox_coms = rec.total_saldo_coms
            rec.descuentox_antes = rec.descuento_antes
            rec.descuentox_des = rec.descuento_des
            rec.mermasx_antes = rec.mermas_antes
            rec.mermasx_des = rec.mermas_des
            rec.comisionesx_antes = rec.comisiones_antes
            rec.comisionx_des = rec.comision_des
            rec.prontopagox_antes = rec.prontopago_antes
            rec.prontopagox_des = rec.prontopago_des
            rec.subtotalx = (
                rec.fletesx
                + rec.maniobrasx
                - rec.mermasx_antes
                - rec.descuentox_antes
                - rec.comisionesx_antes
                - rec.prontopagox_antes
            )
            rec.subtotalx_sm = (
                rec.fletesx
                - rec.mermasx_antes
                - rec.descuentox_antes
                - rec.comisionesx_antes
                - rec.prontopagox_antes
            )
            rec.ivax = 0
            if rec.iva_option == 'CIR' or rec.iva_option == 'CISR':
                rec.ivax = rec.subtotalx * 0.16
            rec.rivax = 0
            if rec.iva_option == 'CIR':
                rec.rivax = rec.subtotalx_sm * 0.04
            rec.totalx = rec.subtotalx + rec.ivax - rec.rivax
            rec.diferenciax = rec.move_id.amount_total - rec.totalx
            rec.notacargox = rec.diferenciax
            if rec.move_id:
                if rec.move_id.amount_total <= 0:
                    error = True
                    errores += (
                        'El total de la carta porte debe ser mayor a cero.'
                        + '\r\n'
                    )
            viajes_encp = False
            for viaje in rec.viaje_id:
                vobj = rec.env['trafitec.viajes'].search([
                    ('id', '=', viaje.id)
                ])
                fl_obj = self.env['account.move.line']
                vca_obj = self.env['trafitec.viaje.cargos']
                fl_dat = fl_obj.search([
                    ('move_id', '=', rec.move_id.id)
                ])
                vca_dat = vca_obj.search([
                    ('line_cargo_id', '=', viaje.id),
                    ('validar_en_cr', '=', True)
                ])
                viaje_encp = False
                for vcp in rec.move_id.viajescp_id:
                    if vcp.id == viaje.id:
                        viaje_encp = True
                        break
                if not viaje_encp:
                    error = True
                    errores += (
                        'El viaje {} no se encontro en los'.format(viaje.name)
                        + ' viajes de la carta porte.\r\n'
                    )
                if vobj.en_contrarecibo:
                    error = True
                    errores += (
                        'El viaje {} ya tiene contra recibo.\r\n'.format(
                            viaje.name
                        )
                    )
                if not viaje.documentacion_completa:
                    error = True
                    errores += (
                        'El viaje con el folio: {} no '.format(viaje.name)
                        + 'tiene documentación completa.\r\n'
                    )
                if viaje.peso_origen_total == 0:
                    error = True
                    errores += (
                        'El viaje con el folio: {} no '.format(viaje.name)
                        + 'tiene el peso origen capturado.\r\n'
                    )
                if viaje.peso_destino_total == 0:
                    error = True
                    errores += (
                        'El viaje con el folio: {} no '.format(viaje.name)
                        + 'tiene el peso destino capturado.\r\n'
                    )
                if viaje.peso_convenido_total == 0:
                    error = True
                    errores += (
                        'El viaje con el folio: {} no '.format(viaje.name)
                        + 'tiene el peso convenido capturado.\r\n'
                    )
                boletas = self.env['trafitec.viajes.boletas'].search([
                    ('linea_id', '=', viaje.id)
                ])
                if not boletas:
                    error = True
                    errores += (
                        'El viaje con el folio {} no '.format(viaje.name)
                        + 'tiene boletas.\r\n'
                        )
            totales = rec.totales()
            if totales['subtotal'] <= 0:
                error = True
                errores += 'El subtotal debe ser mayor a cero.\n'
            if totales['total'] <= 0:
                error = True
                errores += 'El total debe ser mayor a cero.\n'
            if rec.move_id:
                diferencia = abs(totales['total'] - rec.move_id.amount_total)
                if (
                    totales['total'] > rec.move_id.amount_total
                    and diferencia > 1
                ):
                    error = True
                    errores += (
                        'El total de la carta porte debe ser mayor o igual al'
                        + ' total del contra recibo.\n'
                    )
            if error:
                raise UserError(
                    (errores)
                )
            parametros_obj = rec._get_parameter_company(rec)
            if rec.subtotal_g > 0:
                rec._cobrar_descuentos()
                rec._cobrar_comisiones()
                if rec.diferencia > 1:
                    invoice = rec._generar_nota_cargo(
                        rec,
                        'diferencia',
                        parametros_obj
                    )
                    rec.folio_diferencia = invoice
                for viaje in rec.viaje_id:
                    viaje.with_context(validar_credito_cliente=False).write({
                        'en_contrarecibo': True,
                        'factura_proveedor_id': rec.move_id.id,
                        'contrarecibo_id': rec.id
                    })
                try:
                    rec.move_id.write({
                        'factura_encontrarecibo': True,
                        'es_cartaporte': True,
                        'contrarecibo_id': rec.id
                    })
                except TypeError:
                    raise UserError(
                        'Alerta..\nError al marcar la factura {} como'.format(
                            rec.move_id.name
                        )
                        + ': En contra recibo.'
                    )
                rec.write({'state': 'Validada'})

    def action_cancel(self):
        for rec in self:
            if rec.state == 'Validada':
                if rec.move_id.state == 'open' or rec.move_id.state == 'paid':
                    raise UserError(
                        'Alerta !\nLa factura carta porte ya fue '
                        + 'contabilizada, no podra cancelar el contra recibo.'
                    )
                if rec.folio_diferencia:
                    if (
                        rec.folio_diferencia.state == 'open'
                        or rec.folio_diferencia.state == 'paid'
                    ):
                        raise UserError(
                            'Alerta !\nLa nota de cargo por diferencia ya fue'
                            + ' contabilizada, no podra cancelar el contra '
                            + 'recibo.'
                        )
                if rec.folio_merma:
                    if rec.folio_merma.state == 'open':
                        raise UserError(
                            'Alerta !\nLa nota de cargo por merma ya fue '
                            + 'contabilizada, no podra cancelar el contra '
                            + 'recibo.'
                        )
                if rec.folio_descuento:
                    if rec.folio_descuento.state == 'open':
                        raise UserError(
                            'Alerta !\nLa nota de cargo por descuentos ya fue'
                            + ' contabilizada, no podra cancelar el contra '
                            + 'recibo.'
                        )
                if rec.folio_comision:
                    if rec.folio_comision.state == 'open':
                        raise UserError(
                            'Alerta !\nLa nota de cargo por comision ya fue '
                            + 'contabilizada, no podra cancelar el contra '
                            + 'recibo.'
                        )
                if rec.folio_prontopago:
                    if rec.folio_prontopago.state == 'open':
                        raise UserError(
                            'Alerta !\nLa nota de cargo por pronto pago ya '
                            + 'fue contabilizada, no podra cancelar el contra'
                            + ' recibo.'
                        )
                for comision in rec.comision_id:
                    comision_obj = self.env[
                        'trafitec.comisiones.abono'
                    ].search([
                        ('abonos_id', '=', comision.cargo_id.id),
                        ('permitir_borrar', '=', True)
                    ])
                    for c in comision_obj:
                        c.write({'permitir_borrar': False})
                        c.unlink()
                for descuento in rec.descuento_id:
                    descuento_obj = self.env[
                        'trafitec.descuentos.abono'
                    ].search([
                        ('abonos_id', '=', descuento.descuento_fk.id),
                        ('permitir_borrar', '=', True)
                    ])
                    for d in descuento_obj:
                        d.write({'permitir_borrar': False})
                        d.unlink()
                rec.move_id.write({
                    'factura_encontrarecibo': False,
                    'contrarecibo_id': False
                })
                for viaje in rec.viaje_id:
                    viaje.with_context(validar_credito_cliente=False).write({
                        'en_contrarecibo': False,
                        'factura_proveedor_id': False,
                        'contrarecibo_id': False
                    })
            rec.viaje_id = [(5, 0, 0)]
            rec.fletes = 0
            rec.cargosadicionales_id = [(5, 0, 0)]
            rec.cargosadicionales_total = 0
            rec.move_id = False
            rec.folio_diferencia = False
            rec.write({'state': 'Cancelada'})

    @api.onchange('asociado_id')
    def _asociado(self):
        for rec in self:
            rec.descuento_id = []
            rec.comision_id = []
            if rec.asociado_id:
                obj = self.env['trafitec.descuentos'].search([
                    ('asociado_id', '=', rec.asociado_id.id),
                    ('saldo', '>', 0),
                    ('state', '=', 'activo')
                ])
                rd = []
                rc = []
                for descuento in obj:
                    folio = descuento.viaje_id.name
                    operador = descuento.operador_id.name
                    abono = descuento.saldo
                    if descuento.cobro_fijo:
                        if descuento.monto_cobro:
                            abono = descuento.monto_cobro
                        else:
                            abono = descuento.saldo
                    valores = {
                        'name': descuento.concepto.name,
                        'fecha': descuento.fecha,
                        'anticipo': descuento.monto,
                        'abonos': descuento.abono_total,
                        'saldo': descuento.saldo,
                        'abono': abono,
                        'folio_viaje': folio,
                        'operador': operador,
                        'comentarios': descuento.comentarios,
                        'descuento_fk': descuento.id,
                        'viaje_id': descuento.viaje_id
                    }
                    rd.append(valores)
                rec.descuento_id = rd
                obj_comi = self.env['trafitec.cargos'].search([
                    ('asociado_id', '=', rec.asociado_id.id),
                    ('tipo_cargo', '=', 'comision'),
                    ('saldo', '>', 0)
                ])
                rc = []
                for comision in obj_comi:
                    valores = {
                        'name': comision.viaje_id.name,
                        'fecha': comision.viaje_id.fecha_viaje,
                        'comision': comision.monto,
                        'abonos': comision.abonado,
                        'saldo': comision.saldo,
                        'asociado_id': comision.asociado_id,
                        'tipo_viaje': comision.viaje_id.tipo_viaje,
                        'cargo_id': comision.id,
                        'viaje_id': comision.viaje_id
                    }
                    rc.append(valores)
                rec.comision_id = rc

    @api.onchange('viaje_id', 'asociado_id', 'lineanegocio')
    def _onchange_maniobras(self):
        for rec in self:
            if rec.viaje_id and rec.move_id and len(rec.viaje_id) > 0:
                try:
                    viaje1 = rec.viaje_id[0]
                    cotizacion = viaje1.subpedido_id.linea_id.cotizacion_id
                    if cotizacion.asociado_plazo_pago_id:
                        pterm = cotizacion.asociado_plazo_pago_id
                        pterm_list = pterm.with_context(
                            currency_id=rec.company_id.currency_id.id
                        ).compute(value=1, date_ref=rec.fecha)[0]
                        fecha_vencimiento = max(
                            line[0] for line in pterm_list
                        )
                        rec.move_id.sudo().write({
                            'payment_term_id': (
                                cotizacion.asociado_plazo_pago_id.id
                            ),
                            'invoice_date_due': fecha_vencimiento
                        })
                except:
                    pass

    @api.depends('viaje_id', 'asociado_id', 'lineanegocio')
    def _compute_maniobras(self):
        for rec in self:
            maniobras = 0
            for v in rec.viaje_id:
                maniobras += v.maniobras
            rec.maniobras = maniobras

    @api.depends('total', 'total_g')
    def _compute_diferencia(self):
        for rec in self:
            rec.diferencia = 0
            if rec.total and rec.total_g:
                rec.diferencia = rec.total - rec.total_g

    @api.onchange(
        'mermas_des',
        'descuento_des',
        'comision_des',
        'prontopago_des'
    )
    def _onchange_notacargo(self):
        for rec in self:
            rec.notacargo = (
                rec.mermas_des
                + rec.descuento_des
                + rec.comision_des
                + rec.prontopago_des
            )

    @api.depends('diferencia')
    def _compute_notacargo(self):
        for rec in self:
            rec.notacargo = rec.diferencia

    @api.depends('descuento_id', 'descuento_bol')
    def _check_descuentos(self):
        for rec in self:
            rec.descuento_antes = 0
            rec.descuento_des = 0
            if rec.cobrar_descuentos:
                amount = 0
                saldo = 0
                abonos = 0
                if rec.cobrar_descuentos == 'No cobrar':
                    rec.descuento_antes = amount
                    rec.total_abono_des = abonos
                    rec.total_saldo_des = saldo
                if rec.cobrar_descuentos == 'Todos':
                    for descuento in rec.descuento_id:
                        amount += descuento.abono
                        abonos += descuento.abonos
                        saldo += descuento.saldo
                    rec.descuento_antes = amount
                    rec.total_abono_des = abonos
                    rec.total_saldo_des = saldo
                if rec.cobrar_descuentos == 'Viajes del contrarecibo':
                    for descuento in rec.descuento_id:
                        if descuento.viaje_id in rec.viaje_id:
                            amount += descuento.abono
                            abonos += descuento.abonos
                            saldo += descuento.saldo
                        rec.total_abono_des = abonos
                        rec.total_saldo_des = saldo
                    if not rec.descuento_bol:
                        rec.descuento_antes = amount
                        rec.descuento_des = 0
                    else:
                        rec.descuento_antes = 0
                        rec.descuento_des = amount
            else:
                rec.descuento_antes = 0
                rec.descuento_des = 0

    @api.onchange(
        'cobrar_descuentos',
        'descuento_id',
        'viaje_id',
        'descuento_bol'
    )
    def _onchange_descuentos(self):
        for rec in self:
            if rec.cobrar_descuentos:
                amount = 0
                saldo = 0
                abonos = 0
                if rec.cobrar_descuentos == 'No cobrar':
                    rec.descuento_antes = amount
                    rec.total_abono_des = abonos
                    rec.total_saldo_des = saldo
                if rec.cobrar_descuentos == 'Todos':
                    for descuento in rec.descuento_id:
                        amount += descuento.abono
                        abonos += descuento.abonos
                        saldo += descuento.saldo
                    rec.descuento_antes = amount
                    rec.total_abono_des = abonos
                    rec.total_saldo_des = saldo
                if rec.cobrar_descuentos == 'Viajes del contrarecibo':
                    for descuento in rec.descuento_id:
                        if descuento.viaje_id in rec.viaje_id:
                            amount += descuento.abono
                            abonos += descuento.abonos
                            saldo += descuento.saldo
                        rec.total_abono_des = abonos
                        rec.total_saldo_des = saldo
                    if not rec.descuento_bol:
                        rec.descuento_antes = amount
                        rec.descuento_des = 0
                    else:
                        rec.descuento_antes = 0
                        rec.descuento_des = amount
            else:
                rec.descuento_antes = 0
                rec.descuento_des = 0

    def TotalMermas(self):
        for rec in self:
            total = 0
            for v in rec.viaje_id:
                total += v.merma_cobrar_pesos
            return total

    @api.onchange('viaje_id', 'mermas_bol')
    def _onchange_mermas(self):
        for rec in self:
            total = 0
            rec.mermas_antes = 0
            for v in rec.viaje_id:
                total += v.merma_cobrar_pesos
            rec.mermas_antes = total

    @api.onchange('viaje_id', 'asociado_id')
    def _onchange_viaje_id(self):
        for rec in self:
            rec.cargosadicionales_id = [(5, 0, 0)]
            conceptos = []
            total = 0
            for v in rec.viaje_id:
                cargos = self.env['trafitec.viaje.cargos'].search([
                    ('line_cargo_id', '=', v.id),
                    ('tipo', 'in', (
                        'pagar_cr_cobrar_f', 'pagar_cr_nocobrar_f'
                    )),
                    ('valor', '>', 0)
                ])
                for c in cargos:
                    cargo = {
                        'viaje_id': c.line_cargo_id.id,
                        'contrarecibo_id': rec._origin.id,
                        'tipo_cargo_id': c.name.id,
                        'valor': c.valor
                    }
                    conceptos.append(cargo)
                    total += c.valor
            rec.cargosadicionales_id = conceptos

    @api.depends('cargosadicionales_id')
    def _compute_otros(self):
        for rec in self:
            total = 0
            rec.cargosadicionales_total = 0
            for c in rec.cargosadicionales_id:
                total += c.valor
            rec.cargosadicionales_total = total

    @api.depends('viaje_id', 'mermas_bol')
    def _compute_mermas_antes(self):
        for rec in self:
            total = 0
            rec.mermas_antes = 0
            for v in rec.viaje_id:
                total += v.merma_cobrar_pesos
            if not rec.mermas_bol:
                rec.mermas_antes = total

    @api.onchange('viaje_id', 'mermas_bol')
    def _onchange_mermas_antes(self):
        for rec in self:
            total = 0
            rec.mermas_antes = 0
            for v in rec.viaje_id:
                total += v.merma_cobrar_pesos
            if not rec.mermas_bol:
                rec.mermas_antes = total

    @api.depends('viaje_id', 'mermas_bol')
    def _compute_mermas_despues(self):
        for rec in self:
            total = 0
            rec.mermas_des = 0
            for v in rec.viaje_id:
                total += v.merma_cobrar_pesos
            if rec.mermas_bol:
                rec.mermas_des = total

    @api.depends('viaje_id', 'prontopago_bol')
    def _compute_prontopago(self):
        for rec in self:
            if rec.viaje_id:
                amount = 0
                parametros_obj = rec._get_parameter_company(rec)
                for viaje in rec.viaje_id:
                    if viaje.pronto_pago:
                        amount += viaje.flete_asociado * (
                            parametros_obj.pronto_pago / 100
                        )
                if rec.prontopago_bol:
                    rec.prontopago_des = amount
                    rec.prontopago_antes = 0
                else:
                    rec.prontopago_antes = amount
                    rec.prontopago_des = 0
            else:
                rec.prontopago_antes = 0
                rec.prontopago_des = 0

    @api.onchange('viaje_id', 'prontopago_bol')
    def _onchange_prontopago(self):
        for rec in self:
            if rec.viaje_id:
                amount = 0
                parametros_obj = rec._get_parameter_company(rec)
                for viaje in rec.viaje_id:
                    if viaje.pronto_pago:
                        amount += viaje.flete_asociado * (
                            parametros_obj.pronto_pago / 100
                        )
                if rec.prontopago_bol:
                    rec.prontopago_des = amount
                    rec.prontopago_antes = 0
                else:
                    rec.prontopago_antes = amount
                    rec.prontopago_des = 0

    @api.depends('viaje_id', 'comision_bol', 'cobrar_comisiones')
    def _check_comisiones(self):
        for rec in self:
            if rec.cobrar_comisiones:
                amount = 0
                saldo = 0
                abonos = 0
                if rec.cobrar_comisiones == 'No cobrar':
                    rec.comisiones_antes = amount
                    rec.total_saldo_coms = saldo
                    rec.total_abono_coms = abonos
                if rec.cobrar_comisiones == 'Todos los viajes':
                    for comisi in rec.comision_id:
                        amount += comisi.saldo
                        saldo += comisi.saldo
                        abonos += comisi.abonos
                    rec.comisiones_antes = amount
                    rec.total_saldo_coms = saldo
                    rec.total_abono_coms = abonos
                if rec.cobrar_comisiones == 'Viajes del contrarecibo':
                    for comisi in rec.comision_id:
                        if comisi.viaje_id in rec.viaje_id:
                            amount += comisi.saldo
                            saldo += comisi.saldo
                            abonos += comisi.abonos
                    rec.total_saldo_coms = saldo
                    rec.total_abono_coms = abonos
                if not rec.comision_bol:
                    rec.comisiones_antes = amount
                    rec.comision_des = 0
                else:
                    rec.comisiones_antes = 0
                    rec.comision_des = amount
            else:
                rec.comisiones_antes = 0
                rec.comision_des = 0

    @api.onchange(
        'cobrar_comisiones',
        'comision_id',
        'viaje_id',
        'comision_bol'
    )
    def _onchange_comisiones(self):
        for rec in self:
            if rec.cobrar_comisiones:
                amount = 0
                saldo = 0
                abonos = 0
                if rec.cobrar_comisiones == 'No cobrar':
                    rec.comisiones_antes = amount
                    rec.total_saldo_coms = saldo
                    rec.total_abono_coms = abonos
                if rec.cobrar_comisiones == 'Todos los viajes':
                    for comisi in rec.comision_id:
                        amount += comisi.saldo
                        saldo += comisi.saldo
                        abonos += comisi.abonos
                    rec.comisiones_antes = amount
                    rec.total_saldo_coms = saldo
                    rec.total_abono_coms = abonos
                if rec.cobrar_comisiones == 'Viajes del contrarecibo':
                    for comisi in rec.comision_id:
                        if comisi.viaje_id in rec.viaje_id:
                            amount += comisi.saldo
                            saldo += comisi.saldo
                            abonos += comisi.abonos
                    rec.total_saldo_coms = saldo
                    rec.total_abono_coms = abonos
                if not rec.comision_bol:
                    rec.comisiones_antes = amount
                    rec.comision_des = 0
                else:
                    rec.comisiones_antes = 0
                    rec.comision_des = amount
            else:
                rec.comisiones_antes = 0
                rec.comision_des = 0

    @api.depends('viaje_id', 'viaje_id.flete_asociado')
    def _compute_fletes(self):
        for rec in self:
            rec.fletes = 0
            for v in rec.viaje_id:
                rec.fletes += v.flete_asociado

    @api.depends(
        'fletes',
        'maniobras',
        'mermas_antes',
        'descuento_antes',
        'comisiones_antes',
        'prontopago_antes',
        'cargosadicionales_total'
    )
    def _compute_subtotal(self):
        for rec in self:
            x_mermas_antes = 0
            if not rec.mermas_bol:
                x_mermas_antes = rec.TotalMermas()
            rec.subtotal_g = (
                rec.fletes
                + rec.maniobras
                + rec.cargosadicionales_total
                - x_mermas_antes
                - rec.descuento_antes
                - rec.comisiones_antes
                - rec.prontopago_antes
            )

    @api.depends(
        'fletes',
        'mermas_antes',
        'descuento_antes',
        'comisiones_antes',
        'prontopago_antes',
        'cargosadicionales_total'
    )
    def _compute_subtotalSM(self):
        for rec in self:
            rec.subtotal_gSM = (
                rec.fletes
                + rec.cargosadicionales_total
                - rec.mermas_antes
                - rec.descuento_antes
                - rec.comisiones_antes
                - rec.prontopago_antes
            )

    @api.depends('subtotal_g', 'iva_option', 'fletes')
    def _compute_iva_g(self):
        for rec in self:
            rec.iva_g = 0
            if rec.iva_option == 'CIR' or rec.iva_option == 'CISR':
                rec.iva_g = rec.subtotal_g * 0.16

    @api.depends('subtotal_gSM', 'iva_option', 'fletes')
    def _compute_r_iva_g(self):
        for rec in self:
            rec.r_iva_g = 0
            if rec.iva_option == 'CIR':
                rec.r_iva_g = rec.subtotal_gSM * 0.04

    @api.depends('subtotal_g', 'iva_g', 'r_iva_g')
    def _compute_total_g(self):
        for rec in self:
            rec.total_g = rec.subtotal_g + rec.iva_g - rec.r_iva_g

    def _compute_iva_carta(self):
        for rec in self:
            if rec.move_id.invoice_line_ids:
                if rec.move_id.invoice_line_ids.tax_ids:
                    for tax in rec.move_id.invoice_line_idstax_ids:
                        if tax.tax_id:
                            if (
                                'IVA' in tax.tax_id.name
                                and 'RET' not in tax.tax_id.name
                            ):
                                rec.iva = tax.amount
                                break
                            else:
                                rec.iva = 0

    @api.onchange('move_id')
    def _onchange_r_iva_carta(self):
        for rec in self:
            if rec.move_id:
                if rec.move_id.invoice_line_ids.tax_ids:
                    for tax in rec.move_id.invoice_line_ids.tax_ids:
                        if tax:
                            if (
                                'IVA(16%) COMPRAS' in tax.name
                                and 'RET IVA FLETES 4%' in tax.name
                            ):
                                rec.r_iva = tax.amount
                                break
                            else:
                                rec.r_iva = 0

    def _compute_r_iva_carta(self):
        for rec in self:
            if rec.move_id:
                if rec.move_id.invoice_line_ids.tax_ids:
                    for tax in rec.move_id.invoice_line_ids.tax_ids:
                        if tax:
                            if (
                                'IVA(16%) COMPRAS' in tax.name
                                and 'RET IVA FLETES 4%' in tax.name
                            ):
                                rec.r_iva = tax.amount
                                break
                            else:
                                rec.r_iva = 0

    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            vals['name'] = self.env['ir.sequence'].with_context(
                force_company=vals['company_id']
            ).next_by_code('Trafitec.Contrarecibo') or ('Nuevo')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'Trafitec.Contrarecibo'
            ) or ('Nuevo')
        self._factura_relacionada(True, vals)
        cr = super(TrafitecContrarecibo, self).create(vals)
        return cr

    @api.constrains(
        'asociado_id',
        'move_id',
        'total_g',
        'subtotal_g',
        'iva_g',
        'r_iva_g',
        'viaje_id'
    )
    def _check_cartaporte(self):
        for rec in self:
            error = False
            errores = ''
            if rec.state == 'Cancelada':
                return
            if not rec.lineanegocio:
                error = True
                errores += 'Debe especificar la línea de negocio.\n'
            for v in rec.viaje_id:
                if v.flete_asociado <= 0:
                    error = True
                    errores += (
                        'El viaje con folio '
                        + v.name
                        + ' no tiene calculado el flete.\n'
                    )
                if not v.documentacion_completa:
                    error = True
                    errores += (
                        'El viaje con folio '
                        + v.name
                        + ' no tiene la documentación completa.\n'
                    )
                if rec.move_id:
                    if v.asociado_id.id != rec.move_id.partner_id.id:
                        error = True
                        errores += (
                            'El viaje con folio '
                            + v.name
                            + ' es de diferente asociado al del contra recibo'
                            + '.\n'
                        )
            if error:
                raise UserError(
                    ('Alerta..\n' + str(errores))
                )
