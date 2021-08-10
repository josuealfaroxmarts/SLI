# -*- coding: utf-8 -*-
import datetime
import random

from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class trafitec_viajes(models.Model):
    _name = 'trafitec.viajes'
    _description = 'viajes'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    @api.model
    def get_empty_list_help(self, help):
        help = "No se encontraron viajes.."
        return help

    def export_data(self, fields_to_export, raw_data=False):
        """ Override to convert virtual ids to ids """

        if (
            ('tarifa_cliente' in fields_to_export)
            or ('flete_cliente' in fields_to_export)
        ):
            if not self.env.user.has_group('sli_trafitec.sli_trafitec_ver_tc'):
                grupo = self.env.ref('sli_trafitec.sli_trafitec_ver_tc')
                raise ValidationError(
                    'Solo usuarios en el grupo (%s) pueden ' % grupo.name
                    + 'exportar la tarifa cliente/flete cliente.'
                )
        nuevo = super(trafitec_viajes, self).export_data(
            fields_to_export,
            raw_data
        )
        return nuevo

    cliente_bloqueado = fields.Boolean(
        string='Cliente bloqueado',
        related='cliente_id.bloqueado_cliente_bloqueado',
        store=True,
        default=False,
        help='Indica si el cliente esta bloqueado.'
    )
    active = fields.Boolean(default=True)
    linea_id = fields.Many2one(
        'trafitec.cotizaciones.linea',
        string='Número de cotización',
        required=True,
        change_default=True,
        index=True,
        tracking=True
    )
    cotizacion_asegurado = fields.Boolean(
        string='Esta asegurado',
        related='linea_id.cotizacion_id.seguro_mercancia',
        readonly=True, store=True
    )
    vendedor_id = fields.Many2one(
        string='Vendedor',
        related='linea_id.cotizacion_id.create_uid',
        readonly=True,
        store=True
    )
    moneda = fields.Many2one(
        "res.currency",
        related='linea_id.cotizacion_id.currency_id',
        string="Moneda",
        store=True
    )
    cliente_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        domain=(
            "["
            + "('company_type','in',['company','person']),"
            "('customer','=',True)"
            + "]"
        )
    )
    referencia_cliente = fields.Char(string="Referencia Viaje Cliente")
    referencia_fletex = fields.Char(string="Referencia Viaje")
    referencia_asociado = fields.Char(string="Referencia Viaje Asociado")
    origen = fields.Many2one(
        related='linea_id.cotizacion_id.origen_id',
        string='Ubicación origen',
        store=True,
        required=True,
        readonly=True
    )
    destino = fields.Many2one(
        related='linea_id.cotizacion_id.destino_id',
        string='Ubicación destino',
        store=True,
        required=True,
        readonly=True
    )
    facturar = fields.Boolean(string='Facturar', readonly=True, store=True)
    psf = fields.Boolean(string='PSF', tracking=True)
    csf = fields.Boolean(string='CSF', tracking=True)
    tarifa_asociado = fields.Float(
        string='Tarifa asociado',
        default=0,
        tracking=True,
        related='linea_id.tarifa_asociado',
        required=True
    )
    tarifa_cliente = fields.Float(
        string='Tarifa cliente',
        default=0,
        required=True
    )
    tarifa_cliente_colaborador = fields.Float(
        string='Tarifa cliente colaborador',
        default=0,
        required=False
    )
    product = fields.Many2one(
        'product.product',
        string='Producto',
        related='linea_id.cotizacion_id.product',
        readonly=True, store=True
    )
    costo_producto = fields.Float(string='Costo del producto', tracking=True)

    lineanegocio = fields.Many2one(
        comodel_name='trafitec.lineanegocio',
        string='Linea de negocios',
        store=True
    )
    tipo_lineanegocio = fields.Char(
        'Tipo de linea de negocio',
        related='lineanegocio.name',
        store=True
    )

    comision_linea = fields.Float(
        string='Porcentaje linea negocio',
        related='lineanegocio.porcentaje',
        readonly=True,
        store=True
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env['res.company']._company_default_get(
            'trafitec.viajes'
        )
    )
    state = fields.Selection([
            ('Nueva', 'Nueva'),
            ('Siniestrado', 'Siniestrado'),
            ('Cancelado', 'Cancelado')
        ],
        string='Estado',
        default='Nueva',
        tracking=True
    )
    documentacion_completa = fields.Boolean(string='Documentanción completa')
    fecha_viaje = fields.Date(
        string='Fecha del viaje',
        readonly=False,
        index=True,
        copy=False,
        default=fields.Datetime.now,
        required=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='Usuario que genero viaje',
        index=True,
        tracking=True,
        default=lambda self: self.env.user
    )
    motivo_siniestrado = fields.Text(
        string='Motivo siniestrado',
        tracking=True
    )
    motivo_cancelacion = fields.Text(
        string='Motivo cancelacion',
        tracking=True
    )
    fecha_cambio_estado = fields.Datetime(string='Fecha de cambio')
    en_contrarecibo = fields.Boolean(
        string="Viaje en contra recibo",
        default=False
    )
    contrarecibo_id = fields.Many2one(
        string="Contra recibo",
        comodel_name='trafitec.contrarecibo'
    )
    contrarecibo_fecha = fields.Date(
        string="Fecha contra recibo",
        related='contrarecibo_id.fecha',
        store=True
    )
    x_folio_trafitecw = fields.Char(
        string='Folio Trafitec Windows',
        help="Folio de la orden de carga en Trafitec para windows."
    )
    sucursal_id = fields.Many2one(
        'trafitec.sucursal',
        string='Sucursal',
        store=True
    )
    cargo_id = fields.One2many('trafitec.viaje.cargos', 'line_cargo_id')
    cargo_total = fields.Float(
        string='Total cargos',
        compute='compute_cargo_total',
        store=True
    )
    en_factura = fields.Boolean(
        string="Viaje con factura cliente",
        default=False
    )
    factura_cliente_id = fields.Many2one(
        string='Factura cliente',
        comodel_name='account.move')
    factura_cliente_folio = fields.Char(
        string='Folio de factura cliente',
        related='factura_cliente_id.name',
        store=True
    )
    factura_cliente_fecha = fields.Date(
        string='Fecha de factura cliente',
        related='factura_cliente_id.date',
        store=True
    )
    en_cp = fields.Boolean(
        string="Viaje con carta porte",
        default=False,
        help='Indica si el viaje esta relacionado con una carta porte.'
    )
    factura_proveedor_id = fields.Many2one(
        string='Factura proveedor',
        comodel_name='account.move'
    )
    factura_proveedor_folio = fields.Char(
        string='Folio de factura proveedor',
        related='factura_proveedor_id.name',
        store=True
    )
    factura_proveedor_fecha = fields.Date(
        string='Fecha de factura proveedor',
        related='factura_proveedor_id.date',
        store=True
    )
    asignadoa_id = fields.Many2one(
        string='Asignado a',
        comodel_name='res.users',
        tracking=True
    )
    estado_viaje = fields.Selection([
            ('noespecificado', '(No especificado)'),
            ('enespera', '(En espera)'),
            ('enproceso', 'En proceso'),
            ('finalizado', 'Finalizado'),
            ('cancelador', 'Cancelado'),
            ('cerrado', 'Cerrado'),
            ('siniestrado', 'Siniestrado')
        ],
        string='Estado del viaje',
        default='enespera',
        tracking=True
    )
    proyecto_referenciado = fields.Char(
        string='Proyecto referenciado',
        readonly=True,
        related='linea_id.cotizacion_id.nombre'
    )
    calificaiones = fields.One2many(
        string='Calificaciones',
        inverse_name='viaje_id',
        comodel_name='trafitec.clasificacionesgxviaje',
        tracking=True
    )
    crm_trafico_registro_id = fields.Many2one(
        string='Registro CRM Tráfico',
        comodel_name='trafitec.crm.trafico.registro'
    )
    cantidad = fields.Char(string='cantidad', default="0")
    cliente_etiquetas = fields.Many2many(
        string='Etiqueta del cliente',
        comodel_name='res.partner.category',
        related='cliente_id.category_id'
    )
    name = fields.Char(
        string="Folio",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('New')
    )
    router = fields.Char(
        string='Ruta (Google Maps)',
    )

    @api.onchange('referencia_asociado')
    def gelocalization(self):
        for rec in self:
            domain = [('shipment_id_fletex', '=', rec.referencia_asociado)]
            for geo in self.env['trafitec.routers'].search(domain):
                rec.router = geo.google_maps

    @api.onchange('seguro_total', 'seguro_entarifa')
    def onchange_seguro(self):
        for rec in self:
            original = {}
            originales = []
            final = {}
            finales = []
            total = 0
            existe = False
            tfinal = {}
            tfinales = []
            cfg_obj = self.env['trafitec.parametros']
            cfg_dat = cfg_obj.search([
                    ('company_id', '=', self.env.user.company_id.id)
                ],
                limit=1
            )
            for cargo in rec.cargo_id:
                original = {
                    'id': cargo.id,
                    'line_cargo_id': cargo.line_cargo_id,
                    'sistema': cargo.sistema,
                    'validar_en_cr': cargo.validar_en_cr,
                    'name': cargo.name,
                    'valor': cargo.valor
                }
                originales.append(original)
            valor = 0
            xid = -1
            for original in originales:
                xid = original.get('id')
                valor = original.get('valor', 0)
                if valor <= 0:
                    continue
                if original.get(
                    'name'
                ).id == cfg_dat.seguro_cargo_adicional_id.id:
                    if rec.seguro_entarifa:
                        continue
                    if not isinstance(xid, models.NewId):
                        valor = rec.seguro_total
                        existe = True
                    else:
                        continue
                final = {
                    'accion': 'actualizar',
                    'id': original.get('id'),
                    'registro': {
                        'name': original.get('name'),
                        'valor': valor,
                        'line_cargo_id': original.get('line_cargo_id'),
                        'sistema': original.get('sistema'),
                        'validar_en_cr': original.get('validar_en_cr')
                    }
                }
                finales.append(final)
            if (
                not existe
                and not rec.seguro_entarifa
                and rec.seguro_total > 0
            ):
                producto_seguro = self.env[
                    'trafitec.tipocargosadicionales'
                ].search([('name', '=', 'Seguro')])
                seguro = {'accion': 'crear', 'id': -1, 'registro': {
                    'name': producto_seguro.id,
                    'valor': rec.seguro_total,
                    'line_cargo_id': rec.id,
                    'sistema': True,
                    'validar_en_cr': False,
                    'tipo': 'pagar_cr_cobrar_f'
                    }
                }
                finales.append(seguro)
            for f in finales:
                if f.get('accion') == 'crear':
                    tfinal = (0, 0, f.get('registro'))
                if f.get('accion') == 'actualizar':
                    tfinal = (1, f.get('id'), f.get('registro'))
                tfinales += [tfinal]
            self.update({'cargo_id': tfinales})

    @api.depends(
        'seguro_pcliente',
        'costo_producto',
        'peso_origen_total',
        'seguro_id'
    )
    def copute_seguro_total(self):
        for rec in self:
            total = 0
            total = (
                rec.peso_origen_total
                * rec.costo_producto
                * rec.seguro_pcliente
            )
            rec.seguro_total = total

    seguro_id = fields.Many2one(
        string='Poliza de seguro',
        comodel_name='trafitec.polizas',
        related='linea_id.cotizacion_id.polizas_seguro'
    )
    seguro = fields.Boolean(
        string="Seguro",
        related='linea_id.cotizacion_id.seguro_mercancia'
    )
    seguro_pcliente = fields.Float(
        string='Factor del seguro',
        default=0,
        help='Factor del seguro.',
        digits=(16, 3),
        related='linea_id.cotizacion_id.factor_seguro'
    )
    seguro_total = fields.Float(
        string='Total del seguro',
        compute=copute_seguro_total,
        default=0,
        store=True
    )
    seguro_entarifa = fields.Boolean(
        string='Seguro incluido en tarifa',
        default=False,
        help='Indica si el seguro esta incluido en la tarifa.',
        related='linea_id.cotizacion_id.seguro_entarifa'
    )
    descuento_combustible_id = fields.Many2one(
        string='Vale de combustible',
        comodel_name='trafitec.descuentos',
        help='Descuento de vale de combustible.'
    )

    def action_descuento_combustible(self):
        self.ensure_one()
        viaje = self
        error = False
        errores = ""
        if viaje.descuento_combustible_id:
            error = True
            errores += (
                "El viaje ya tiene relacionado un vale de combustible.\n"
            )
        if viaje.state != 'Nueva':
            error = True
            errores += "El viaje debe estar activo.\n"
        if viaje.en_contrarecibo:
            error = True
            errores += "El viaje ya esta en contra recibo.\n"
        if viaje.en_factura:
            error = True
            errores += "El viaje ya esta en factura.\n"
        if not viaje.asociado_id.combustible_convenio_st:
            error = True
            errores += (
                'El asociado {} no tiene convenio de combustible.\n'.format(
                    viaje.asociado_id.name or ''
                )
            )
        if error:
            raise UserError(errores)
        descuentos_obj = self.env["trafitec.descuentos"]
        cfg_obj = self.env['trafitec.parametros']
        cfg = cfg_obj.search([
            ('company_id', '=', self.env.user.company_id.id)
            ],
            limit=1
        )
        pfactor = (cfg.descuento_combustible_pfactor or 0) / 100
        pcomision = (cfg.descuento_combustible_pcomision or 0) / 100
        litros = 0
        costoporlt = (cfg.descuento_combustible_externo_id.list_price or 0)
        flete = 0
        if viaje.flete_asociado > 0:
            flete = viaje.flete_asociado
        else:
            flete = (viaje.peso_autorizado / 1000) * viaje.tarifa_asociado
        total = flete * pfactor
        comision = total * pcomision
        totalvale = total + comision
        if costoporlt != 0:
            litros = total / costoporlt
        proveedor_id = (cfg.descuento_combustible_proveedor_id.id or False)
        concepto_id = (cfg.descuento_concepto_id.id or False)
        if not proveedor_id or not concepto_id:
            return
        if totalvale <= 0:
            raise UserError('El total del desucuento debe ser mayor a cero.')
        valores = {
            'proveedor': proveedor_id,
            'monto': totalvale,
            'abono_total': 0,
            'operador_id': viaje.operador_id.id,
            'cobro_fijo': False,
            'fecha': False,
            'state': 'borrador',
            'asociado_id': viaje.asociado_id.id,
            'saldo': totalvale,
            'viaje_id': viaje.id,
            'monto_cobro': totalvale,
            'concepto': concepto_id,
            'comentarios': (
                'Generado desde el viaje {0} con flete de {3:,.2f}'.format(
                    viaje.name, litros
                )
                + ' para {1:,.2f} litros de combustible con un costo'.format(
                    costoporlt
                )
                + ' por litro de {2:,.2f}.'.format(flete)
            ),
            'es_combustible': True,
            'folio_nota': '',
            'es_combustible_litros': litros,
            'es_combustible_costoxlt': costoporlt,
            'es_combustible_total': total,
            'es_combustible_pcomision': pcomision*100,
            'es_combustible_comision': comision,
            'es_combustible_totalcomision': totalvale
        }
        nuevo = descuentos_obj.create(valores)
        viaje.write({'descuento_combustible_id': nuevo.id})

    @api.depends('cargo_id')
    def compute_cargo_total(self):
        for rec in self:
            total = 0
            for cargo in rec.cargo_id:
                total += cargo.valor
            rec.cargo_total = total

    def action_nueva(self):
        self.ensure_one()
        self.state = 'Nueva'

    def action_scan(self):
        self.ensure_one()
        obj = self.env['trafitec.viajes.scan'].search([])
        if len(obj) == 'started':
            if obj.viaje_id and self.id:
                if obj.viaje_id.id != self.id and obj.st == 'started':
                    raise UserError(_(
                        'Alerta..\nEl proceso de Scan esta '
                        + 'activo en otro viaje: '+str(obj.viaje_id.name)
                    ))
            if obj.st == 'started':
                obj.st = 'not_started'
                return self.Mensaje("Scan terminado.")
            else:
                obj.st = 'started'
                obj.viaje_id = self.id
                return self.Mensaje("Scan iniciado.")
        else:
            if self.id:
                nuevo = {'viaje_id': self.id, 'st': 'started'}
                obj.create(nuevo)
                return self.Mensaje("Scan iniciado.")

    def Mensaje(self, mensaje):
        return {
            'name': 'Alerta..',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'custom.pop.message',
            'target': 'new',
            'context': {'default_name': mensaje}
        }

    def viajes_conteo(self):
        return 23

    @api.model
    def default_get(self, fields):
        rec = super(trafitec_viajes, self).default_get(fields)
        return rec

    def total_viajes(self, creando=False):
        for rec in self:
            total = 0.00
            totalesteviaje = 0.00
            viajes = self.env['trafitec.viajes'].search([
                ('linea_id', '=', rec.id),
                ('state', '=', 'Nueva')
            ])
            for viaje in viajes:
                if viaje.peso_origen_total <= 0:
                    total = total + viaje.peso_autorizado
                else:
                    total = total + viaje.peso_origen_total / 1000.00
            total = total + totalesteviaje
            return total

    def unlink(self):
        raise UserError(_('Alerta..\nNo esta permitido borrar viajes.'))

    @api.constrains(
        'cliente_id',
        'lineanegocio',
        'asociado_id',
        'operador_id',
        'placas_id',
        'peso_origen_remolque_1',
        'peso_origen_remolque_2',
        'peso_destino_remolque_1',
        'peso_destino_remolque_2',
        'peso_convenido_remolque_1',
        'peso_convenido_remolque_2',
        'peso_origen_total',
        'peso_destino_total',
        'peso_autorizado',
        'seguro_id',
        'costo_producto',
        'seguro_pcliente',
        'seguro_total',
        'seguro_entarifa'
        'cargo_id',
        'flete_cliente'
    )
    def _valida(self):
        for rec in self:
            if not rec.cliente_id:
                raise UserError(_('Alerta !\n--Debe especificar el cliente.'))
            if not rec.lineanegocio:
                raise UserError(
                    _('Alerta !\nDebe especificar la línea de negocio.')
                )
            if not rec.asociado_id:
                raise UserError(_('Alerta !\nDebe especificar el asociado.'))
            if not rec.operador_id:
                raise UserError(_('Alerta !\nDebe especificar el operador.'))
            if not rec.placas_id:
                raise UserError(_('Alerta !\nDebe especificar el vehículo.'))
            if not rec.asociado_id:
                raise UserError(_('Alerta !\nDebe especificar el asociado.'))
            if not rec.operador_id:
                raise UserError(_('Alerta !\nDebe especificar el operador.'))
            if rec.flete_cliente > 0:
                if rec.seguro_id:
                    if not rec.seguro_entarifa:
                        if rec.costo_producto <= 0:
                            raise UserError(_(
                                'Alerta..\nEste viaje esta asegurado, debe '
                                + 'especificar el costo del producto por kg.'
                            ))
                        if rec.seguro_pcliente <= 0:
                            raise UserError(_(
                                'Alerta..\nEste viaje esta asegurado, debe '
                                + 'especificar el porcentaje de seguro.'
                            ))
                        if rec.seguro_total <= 0:
                            raise UserError(_(
                                'Alerta..\nEste viaje esta asegurado, el '
                                + 'total del seguro debe ser mayor a cero.'
                            ))
            total_viajes = rec.total_viajes()
            total_subpedido = rec.cantidad
            if (
                total_viajes > 0
                and total_subpedido > 0
                and total_viajes > total_subpedido
            ):
                raise UserError(_(
                    'Alerta..\nCon el viaje actual se excede el peso de lo '
                    + 'especificado en la cotización ({}/{}).'.format(
                        total_viajes, total_subpedido
                    )
                ))
            if rec.lineanegocio.id == 1:
                if (
                    rec.peso_origen_remolque_1 > 0
                    and (rec.peso_origen_remolque_1 > 150000)
                ):
                    raise UserError(_(
                        'Alerta !\nEl peso origen del remolque 1 debe estar '
                        + 'entre 1 y 150,000.'
                    ))
                if (
                    rec.peso_origen_remolque_2 > 0
                    and (rec.peso_origen_remolque_2 > 150000)
                ):
                    raise UserError(_(
                        'Alerta !\nEl peso origen del remolque 2 debe estar '
                        + 'entre 1 y 150,000.'
                    ))
                if (
                    rec.peso_destino_remolque_1 > 0
                    and (rec.peso_destino_remolque_1 > 150000)
                ):
                    raise UserError(_(
                        'Alerta !\nEl peso destino del remolque 1 debe estar '
                        + 'entre 1 y 150,000.'
                    ))
                if (
                    rec.peso_destino_remolque_2 > 0
                    and (rec.peso_destino_remolque_2 > 150000)
                ):
                    raise UserError(_(
                        'Alerta !\nEl peso destino del remolque 2 debe estar '
                        + 'entre 1 y 150,000.'
                    ))
                if (
                    rec.peso_convenido_remolque_1 > 0
                    and (rec.peso_convenido_remolque_1 > 150000)
                ):
                    raise UserError(_(
                        'Alerta !\nEl peso convenido del remolque 1 debe '
                        + 'estar entre 1 y 150,000.'
                    ))
                if (
                    rec.peso_convenido_remolque_2 > 0
                    and (rec.peso_convenido_remolque_2 > 150000)
                ):
                    raise UserError(_(
                        'Alerta !\nEl peso convenido del remolque 2 debe '
                        + 'estar entre 1 y 150,000.'
                    ))
                if (
                    (rec.peso_autorizado <= 0)
                    or (rec.peso_autorizado > 150000)
                ):
                    raise UserWarning(_(
                        'Alerta !\nEl peso autorizado debe estar entre 1 y '
                        + '150,000 toneladas.'
                    ))

    @api.constrains('tarifa_asociado')
    def _check_tarifa_asociado(self):
        for rec in self:
            if rec.tarifa_asociado <= 0:
                raise UserError(_(
                    'Aviso !\nLa tarifa asociado debe ser mayor a 0'
                ))
            obj = self.env['trafitec.cotizacion.linea.negociacion'].search([
                ('linea_id', '=', rec.linea_id.id),
                ('asociado_id', '=', rec.asociado_id.id),
                ('state', '=', 'autorizado')
            ])
            if len(obj) > 0:
                for nego in obj:
                    if rec.tarifa_asociado > nego.tarifa:
                        raise UserError(_(
                            'Aviso !\nLa tarifa asociado no puede ser mayor a'
                            + ' la tarifa asociado de la negociación.'
                        ))
            elif rec.tarifa_asociado > rec.linea_id.tarifa_asociado:
                raise UserError(_(
                    'Aviso !\nLa tarifa asociado no puede ser mayor a la '
                    + 'tarifa asociado de la cotización.'
                ))

    @api.constrains('tarifa_cliente', 'tarifa_asociado')
    def _check_tarifa_cliente(self):
        for rec in self:
            context = rec._context
            if context.get('validar_tc', True):
                if rec.tarifa_cliente <= 0:
                    raise UserError(_(
                        'Aviso !\nLa tarifa cliente debe ser mayor a 0'
                    ))
                if rec.tarifa_cliente < rec.linea_id.tarifa_cliente:
                    raise UserError(_(
                        'Aviso !\nLa tarifa cliente no puede ser menor a la '
                        + 'tarifa cliente de la cotizacion'
                    ))
                infocliente = self.env['res.partner'].search([
                    ('id', '=', rec.cliente_id.id)
                ])
                if (
                    (not infocliente.permitir_ta_mayor_tc)
                    and rec.tarifa_asociado > rec.tarifa_cliente
                ):
                    raise UserError(_(
                        'Alerta..\nLa tarifa asociado no puede ser mayor a la'
                        + ' tarifa cliente'
                    ))

    @api.depends(
        'facturar_con',
        'facturar_con_cliente',
        'peso_destino_remolque_1',
        'peso_destino_remolque_2',
        'peso_convenido_remolque_1',
        'peso_convenido_remolque_2',
        'peso_origen_remolque_1',
        'peso_origen_remolque_2',
        'tarifa_asociado',
        'tarifa_cliente'
    )
    def _compute_flete(self):
        for reg in self:
            if reg.facturar_con:
                if reg.facturar_con == 'Peso convenido':
                    reg.flete_asociado = (
                        (reg.peso_convenido_total / 1000)
                        * reg.tarifa_asociado
                    )
                elif reg.facturar_con == 'Peso origen':
                    reg.flete_asociado = (
                        (reg.peso_origen_total / 1000)
                        * reg.tarifa_asociado
                    )
                elif reg.facturar_con == 'Peso destino':
                    reg.flete_asociado = (
                        (reg.peso_destino_total / 1000)
                        * reg.tarifa_asociado
                    )
            else:
                reg.flete_asociado = 0
            if reg.facturar_con_cliente:
                if reg.facturar_con_cliente == 'Peso convenido':
                    reg.flete_cliente = (
                        (reg.peso_convenido_total / 1000)
                        * reg.tarifa_cliente
                    )
                elif reg.facturar_con_cliente == 'Peso origen':
                    reg.flete_cliente = (
                        (reg.peso_origen_total / 1000)
                        * reg.tarifa_cliente
                    )
                elif reg.facturar_con_cliente == 'Peso destino':
                    reg.flete_cliente = (
                        (reg.peso_destino_total / 1000)
                        * reg.tarifa_cliente
                    )
            else:
                reg.flete_cliente = 0
    flete_cliente = fields.Float(
        string='Flete cliente',
        store=True,
        readonly=True,
        compute='_compute_flete'
    )
    flete_asociado = fields.Float(
        string='Flete asociado',
        store=True,
        readonly=True,
        compute='_compute_flete'
    )
    pronto_pago = fields.Boolean(string='Pronto pago', default=False)
    flete_diferencia = fields.Float(
        'Dieferencia en flete',
        compute='_compute_flete_diferencia',
        store=True
    )

    @api.depends('flete_cliente', 'flete_asociado')
    def _compute_flete_diferencia(self):
        for rec in self:
            rec.flete_diferencia = rec.flete_cliente - rec.flete_asociado

    @api.onchange('linea_id')
    def _onchange_subpedido(self):
        for rec in self:
            if rec.linea_id:
                rec.tarifa_cliente = rec.linea_id.tarifa_cliente
                rec.facturar_con = (
                    rec.linea_id.cotizacion_id.cliente.facturar_con
                )
                rec.facturar_con_cliente = (
                    rec.linea_id.cotizacion_id.cliente.facturar_con
                )
                rec.excedente_merma = (
                    rec.linea_id.cotizacion_id.cliente.excedente_merma
                )
                rec.lineanegocio = rec.linea_id.cotizacion_id.lineanegocio
                rec.cliente_id = rec.linea_id.cotizacion_id.cliente
                rec.origen = rec.origen
                rec.destino = rec.destino
                if rec.linea_id.name:
                    rec.folio_cliente = rec.linea_id.name
                rec.costo_producto = rec.linea_id.cotizacion_id.costo_producto
                if rec.linea_id.cotizacion_id.polizas_seguro:
                    if not rec.seguro_id:
                        rec.seguro_id = (
                            rec.linea_id.cotizacion_id.polizas_seguro
                        )
                        rec.costo_producto = (
                            rec.linea_id.cotizacion_id.costo_producto
                        )
                        rec.seguro_pcliente = (
                            rec.linea_id.cotizacion_id.porcen_seguro
                        )
                        rec.seguro_entarifa = (
                            rec.linea_id.cotizacion_id.seguro_entarifa
                        )

    @api.onchange('seguro_id')
    def _onchange_seguro(self):
        for rec in self:
            if rec.seguro_id:
                rec.seguro_pcliente = rec.linea_id.cotizacion_id.porcen_seguro
            else:
                rec.seguro_pcliente = 0
                rec.seguro_total = 0

    @api.onchange('lineanegocio')
    def _onchange_lineanegocio(self):
        for rec in self:
            if rec.lineanegocio:
                if rec.lineanegocio.id == 3:
                    if rec.tipo_remolque.tipo == 'sencillo':
                        rec.peso_origen_remolque_1 = 1000
                        rec.peso_origen_remolque_2 = 0
                        rec.peso_destino_remolque_1 = 1000
                        rec.peso_destino_remolque_2 = 0
                    else:
                        rec.peso_origen_remolque_1 = 500
                        rec.peso_origen_remolque_2 = 500
                        rec.peso_destino_remolque_1 = 500
                        rec.peso_destino_remolque_2 = 500
                else:
                    rec.peso_origen_remolque_1 = 0
                    rec.peso_origen_remolque_2 = 0
                    rec.peso_destino_remolque_1 = 0
                    rec.peso_destino_remolque_2 = 0

    @api.onchange('linea_id', 'asociado_id')
    def _onchange_tarifa(self):
        for rec in self:
            if rec.linea_id and rec.asociado_id:
                obj_nego = self.env[
                    'trafitec.cotizacion.linea.negociacion'
                ].search([
                    ('linea_id', '=', rec.linea_id.id),
                    ('asociado_id', '=', rec.asociado_id.id)
                ])
                if len(obj_nego) > 0:
                    rec.tarifa_asociado = obj_nego.tarifa
                else:
                    rec.tarifa_asociado = rec.linea_id.tarifa_asociado

    def traduce_account_invoice_state(self, state):
        valores = {
            'draft': _('Borrador'),
            'proforma': _('Proforma'),
            'proforma2': _('Proforma2'),
            'open': _('Abierto'),
            'paid': _('Pagado'),
            'cancel': _('Cancelado')
        }
        return valores.get(state, '')

    @api.depends(
        "contrarecibo_id",
        "contrarecibo_id.state",
        "en_contrarecibo",
        "factura_cliente_id",
        "factura_cliente_id.state",
        "en_factura"
    )
    def _compute_info(self):
        for rec in self:
            info = ""
            cr = rec.contrarecibo_id
            cp = cr.move_id
            f = rec.factura_cliente_id
            info += (
                "CR: "
                + (cr.name or "")
                + " "
                + (cr.fecha or "")
                + " "
                + (cr.state or "")
                + "  "
            )
            info += (
                "CP: "
                + (cp.name or "")
                + " "
                + (cp.ref or "")
                + " "
                + (cp.date or "")
                + " "
                + (rec.traduce_account_invoice_state(cp.state) or "")
                + "  "
            )
            info += (
                "F:  "
                + (f.name or "")
                + " "
                + (f.date or "")
                + " "
                + (rec.traduce_account_invoice_state(f.state) or "")
                + "  "
            )
        rec.info = info

    placas_id = fields.Many2one(
        'fleet.vehicle',
        string='Placas',
        required=True
    )
    vehiculo = fields.Char(string='Vehiculo', readonly=True, tracking=True)
    asociado_id = fields.Many2one(
        related='placas_id.asociado_id',
        string='Asociado',
        store=True
    )
    porcentaje_comision = fields.Float(
        string='Porcentaje de comisión',
        readonly=True
    )
    usar_porcentaje = fields.Boolean(
        string='Usar porcentaje de línea de negocio',
        readonly=True
    )
    creditocomision = fields.Boolean(
        string='Crédito de comisión',
        readonly=True
    )
    operador_id = fields.Many2one(
        'res.partner',
        string="Operador",
        required=True,
        domain="[('operador','=',True)]"
    )
    no_economico = fields.Char(
        string='No. economico',
        readonly=True,
        related='placas_id.numero_economico'
    )
    celular_asociado = fields.Char(string='Celular asociado', required=True)
    tipo_camion = fields.Selection([
            ("Jaula", "Jaula"),
            ("Caja Seca", "Caja Seca"),
            ("Portacontenedor", "Portacontenedor"),
            ("Tolva", "Tolva"),
            ("Plataforma", "Plataforma"),
            ("Gondola", "Gondola"),
            ("Torton", "Torton"),
            ("Rabon", "Rabon"),
            ("Chasis", "Chasis"),
            ("Thermo 48", "Thermo 48"),
            ("Thermo 53", "Thermo 53")
        ],
        string='Tipo remolque'
    )
    tipo_remolque = fields.Many2one(
        'trafitec.moviles',
        string='Tipo de remolque',
        domain=(
            "["
            + "'|',"
            + "('lineanegocio','=',lineanegocio),"
            + "('lineanegocio','=',False)"
            + "]"
        )
    )
    nombre_remolque = fields.Selection(
        string="Nombre remolque",
        related='tipo_remolque.tipo'
    )
    capacidad = fields.Float(
        string="Capacidad",
        related='tipo_remolque.capacidad',
        readonly=True,
        store=True
    )
    tipo = fields.Selection(
        string="Tipo",
        related='tipo_remolque.tipo',
        readonly=True,
        store=True,
        tracking=True
    )
    celular_operador = fields.Char(string='Celular operador', required=True)
    info = fields.Text(
        string='Información',
        compute='_compute_info',
        store=False
    )
    costo_km_vacio = fields.Float(
        string='Costo por km vacío',
        default=0,
        help='Costo por kilómetro vacío.'
    )
    costo_km_cargado = fields.Float(
        string='Costo por km cargado',
        default=0,
        help='Costo por kilómetro cargado.'
    )

    @api.depends('flete_cliente', 'flete_asociado')
    def _compute_utilidad_txt(self):
        for rec in self:
            if rec.flete_cliente <= 0 and rec.flete_asociado <= 0:
                rec.utilidad_txt = "--"
                return
            utilidad = rec.flete_cliente-rec.flete_asociado
            cantidad = rec.flete_cliente*0.05
            if utilidad >= cantidad:
                rec.utilidad_txt = "si"
            else:
                rec.utilidad_txt = "no"

    utilidad_txt = fields.Selection(
        string='Utilidad',
        compute='_compute_utilidad_txt',
        selection=[('no', 'NO'), ('si', 'SI'), ('--', '--')],
        default='--',
        store=True
    )
    slitrack_gps_latitud = fields.Float(
        string='Latitud slitrack',
        default=0,
        digits=(10, 10)
    )
    slitrack_gps_longitud = fields.Float(
        string='Longitud slitrack',
        default=0,
        digits=(10, 10)
    )
    slitrack_gps_velocidad = fields.Float(
        string='Velocidad slitrack',
        default=0
    )
    slitrack_gps_fechahorar = fields.Datetime(string='Fecha y hora slitrack')
    slitrack_comentarios = fields.Text(
        string='Comentarios slitrack',
        default=''
    )
    slitrack_estado = fields.Selection([
            ('noiniciado', '(No iniciado)'),
            ('iniciado', 'Iniciado'),
            ('terminado', 'Terminado')
        ],
        string='Estado slitrack',
        default='noiniciado')
    slitrack_codigo = fields.Char(string='Código slitrack', default='')
    slitrack_gps_contador = fields.Integer(
        string='Contador slitrack',
        default=0
    )
    slitrack_st = fields.Selection(
        string='Activo slitrack',
        selection=[('inactivo', 'Inactivo'), ('activo', 'Activo')],
        default='inactivo'
    )
    slitrack_registro = fields.One2many(
        string='Registro slitrack',
        comodel_name='trafitec.slitrack.registro',
        inverse_name='viaje_id'
    )
    slitrack_proveedor = fields.Selection([
            ('slitrack', 'SLI Track'),
            ('geotab', 'GeoTab'),
            ('manual', 'Manual')
        ],
        string="Tip slitrack",
        default='manual'
    )

    def action_slitrack_codigo(self):
        for rec in self:
            codigo = str(rec.id)+str(random.randrange(10000, 99999))
            rec.with_context(validar_credito_cliente=False).write({
                'slitrack_codigo': codigo
            })

    def action_slitrack_activa(self):
        for rec in self:
            rec.action_slitrack_codigo()
            rec.slitrack_estado = 'noiniciado'
            rec.slitrack_st = 'activo'

    @api.onchange('asociado_id')
    def _onchange_asociado(self):
        for rec in self:
            if rec.asociado_id:
                if rec.asociado_id.mobile:
                    rec.celular_asociado = rec.asociado_id.mobile
                elif rec.asociado_id.phone:
                    rec.celular_asociado = rec.asociado_id.phone

    @api.onchange('operador_id')
    def _onchange_operador(self):
        for rec in self:
            if rec.operador_id:
                if rec.operador_id.mobile:
                    rec.celular_operador = rec.operador_id.mobile
                elif rec.operador_id.phone:
                    rec.celular_operador = rec.operador_id.phone

    @api.onchange('placas_id')
    def _vehiculo_(self):
        for rec in self:
            if rec.placas_id:
                rec.asociado_id = rec.placas_id.asociado_id
                rec.porcentaje_comision = (
                    rec.placas_id.asociado_id.porcentaje_comision
                )
                rec.usar_porcentaje = (
                    rec.placas_id.asociado_id.usar_porcentaje
                )
                rec.creditocomision = (
                    rec.placas_id.asociado_id.creditocomision
                )
                rec.operador_id = rec.placas_id.operador_id
                rec.no_economico = rec.placas_id.no_economico
                marca = rec.placas_id.name
                if rec.placas_id.modelo:
                    modelo = rec.placas_id.modelo
                else:
                    modelo = ''
                if rec.placas_id.color:
                    color = rec.placas_id.color
                else:
                    color = ''
                str_vehiculo = '{}, {}, {}'.format(marca, modelo, color)
                rec.vehiculo = str_vehiculo

    regla_comision = fields.Selection([
            ('No cobrar', 'No cobrar'),
            (
                'Con % linea transportista y peso origen',
                'Con % linea transportista y peso origen'
            ),
            (
                'Con % linea transportista y peso destino',
                'Con % linea transportista y peso destino'
            ),
            (
                'Con % linea transportista y peso convenido',
                'Con % linea transportista y peso convenido'
            ),
            (
                'Con % linea transportista y capacidad de remolque',
                'Con % linea transportista y capacidad de remolque'
            ),
            (
                'Con % especifico y peso origen',
                'Con % especifico y peso origen'
            ),
            (
                'Con % especifico y peso destino',
                'Con % especifico y peso destino'
            ),
            (
                'Con % especifico y peso convenido',
                'Con % especifico y peso convenido'
            ),
            (
                'Con % especifico y capacidad de remolque',
                'Con % especifico y capacidad de remolque'
            ),
            ('Cobrar cantidad especifica', 'Cobrar cantidad específica')
        ],
        string='Regla de Comisión',
        default='Con % linea transportista y peso origen',
        required=True,
        tracking=True
    )
    comision = fields.Selection([
            ('No cobrar', 'No cobrar'),
            ('Cobrar en contra-recibo', 'Cobrar en contra-recibo'),
            (
                'Cobrar en contra recibo-porcentaje especifico',
                'Cobrar en contra recibo-porcentaje específico'
            ),
            ('Cobrar cantidad especifica', 'Cobrar cantidad específica')
        ],
        string='Comisión',
        default='Cobrar en contra-recibo',
        required=True,
        tracking=True
    )
    motivo = fields.Text(string='Motivo sin comisión', tracking=True)
    porcent_comision = fields.Float(string='Porcentaje comisión')
    cant_especifica = fields.Float(string='Cobrar cantidad específica')
    peso_autorizado = fields.Float(
        string='Peso autorizado (Kg)',
        required=True,
        help='Peso autorizado en toneladas.'
    )
    tipo_viaje = fields.Selection([
            ('Normal', 'Normal'),
            ('Directo', 'Directo'),
            ('Cobro destino', 'Cobro destino')
        ],
        string='Tipo de viaje',
        default='Normal',
        required=True
    )
    maniobras = fields.Float(string='Maniobras')
    regla_maniobra = fields.Selection([
            (
                'Pagar en contrarecibo y cobrar en factura',
                'Pagar en contrarecibo y cobrar en factura'
            ),
            (
                'Pagar en contrarecibo y no cobrar en factura',
                'Pagar en contrarecibo y no cobrar en factura'
            ),
            (
                'No pagar en contrarecibo y cobrar en factura',
                'No pagar en contrarecibo y cobrar en factura'
            ),
            (
                'No pagar en contrarecibo y no cobrar en factura',
                'No pagar en contrarecibo y no cobrar en factura'
            )
        ],
        string='Regla de maniobra',
        default='Pagar en contrarecibo y cobrar en factura',
        required=True,
        tracking=True
    )

    @api.onchange(
        'regla_comision',
        'cant_especifica',
        'facturar_con',
        'regla_comision'
    )
    def _onchange_comision_calculada(self):
        for rec in self:
            if rec.regla_comision == 'No cobrar':
                rec.comision_calculada = 0
            elif rec.regla_comision == 'Cobrar cantidad especifica':
                rec.comision_calculada = rec.cant_especifica
            else:
                peso = 0
                if rec.facturar_con == 'Peso convenido':
                    peso = rec.peso_convenido_total
                elif rec.facturar_con == 'Peso origen':
                    peso = rec.peso_origen_total
                elif rec.facturar_con == 'Peso destino':
                    peso = rec.peso_destino_total
                if rec.usar_porcentaje:
                    linea_tran = (rec.comision_linea / 100)
                else:
                    linea_tran = (rec.porcentaje_comision / 100)
                if peso:
                    pesototal_asociado = (peso / 1000) * rec.tarifa_asociado
                    if (
                        rec.regla_comision == (
                            'Con % linea transportista y peso origen'
                        )
                        or rec.regla_comision == (
                            'Con % linea transportista y peso destino'
                        )
                        or rec.regla_comision == (
                            'Con % linea transportista y peso convenido'
                        )
                    ):
                        rec.comision_calculada = (
                            pesototal_asociado
                            * linea_tran
                        )
                    if rec.regla_comision == (
                        'Con % linea transportista y capacidad de remolque'
                    ):
                        rec.comision_calculada = (
                            (rec.capacidad / 1000)
                            * rec.tarifa_asociado
                            * linea_tran
                        )
                    if (
                        rec.regla_comision == (
                            'Con % especifico y peso origen'
                        )
                        or rec.regla_comision == (
                            'Con % especifico y peso destino'
                        )
                        or rec.regla_comision == (
                            'Con % especifico y peso convenido'
                        )
                    ):
                        rec.comision_calculada = (
                            pesototal_asociado
                            * (rec.porcent_comision / 100)
                        )
                    if rec.regla_comision == (
                        'Con % especifico y capacidad de remolque'
                    ):
                        rec.comision_calculada = (
                            (rec.capacidad / 1000)
                            * rec.tarifa_asociado
                            * (rec.porcent_comision / 100)
                        )

    def _compute_comision_calculada(self):
        for rec in self:
            if rec.regla_comision == 'No cobrar':
                rec.comision_calculada = 0
            elif rec.regla_comision == 'Cobrar cantidad especifica':
                rec.comision_calculada = rec.cant_especifica
            else:
                peso = 0
                if rec.facturar_con == 'Peso convenido':
                    peso = rec.peso_convenido_total
                elif rec.facturar_con == 'Peso origen':
                    peso = rec.peso_origen_total
                elif rec.facturar_con == 'Peso destino':
                    peso = rec.peso_destino_total
                if rec.usar_porcentaje:
                    linea_tran = (rec.comision_linea / 100)
                else:
                    linea_tran = (rec.porcentaje_comision / 100)
                if peso:
                    pesototal_asociado = (peso / 1000) * rec.tarifa_asociado
                    if (
                        rec.regla_comision == (
                            'Con % linea transportista y peso origen'
                        )
                        or rec.regla_comision == (
                            'Con % linea transportista y peso destino'
                        )
                        or rec.regla_comision == (
                            'Con % linea transportista y peso convenido'
                        )
                    ):
                        rec.comision_calculada = (
                            pesototal_asociado * linea_tran
                        )
                    if rec.regla_comision == (
                        'Con % linea transportista y capacidad de remolque'
                    ):
                        rec.comision_calculada = (
                            (rec.capacidad / 1000)
                            * rec.tarifa_asociado
                            * linea_tran
                        )
                    if (
                        rec.regla_comision == 'Con % especifico y peso origen'
                        or rec.regla_comision == (
                            'Con % especifico y peso destino'
                        )
                        or rec.regla_comision == (
                            'Con % especifico y peso convenido'
                        )
                    ):
                        rec.comision_calculada = (
                            pesototal_asociado
                            * (rec.porcent_comision / 100)
                        )
                    if rec.regla_comision == (
                        'Con % especifico y capacidad de remolque'
                    ):
                        rec.comision_calculada = (
                            (rec.capacidad / 1000)
                            * rec.tarifa_asociado
                            * (rec.porcent_comision / 100)
                        )
            if rec.comision_calculada > 0:
                valores = {
                    'viaje_id': rec.id,
                    'monto': rec.comision_calculada,
                    'tipo_cargo': 'comision',
                    'asociado_id': rec.asociado_id.id
                }
                obc_cargos = rec.env['trafitec.cargos'].search([
                    '&',
                    ('viaje_id', '=', rec.id),
                    ('tipo_cargo', '=', 'comision')
                ])
                if len(obc_cargos) == 0:
                    rec.env['trafitec.cargos'].create(valores)
                else:
                    obc_cargos.write(valores)

    comision_calculada = fields.Float(
        string='Comisión calculada',
        compute='_compute_comision_calculada',
        readonly=True
    )
    detalle_asociado = fields.Text(
        string='Detalle Origen',
        related='linea_id.detalle_asociado',
        store=True
    )
    detalle_destino = fields.Text(
        string='Detalle Destino',
        related='linea_id.detalle_destino',
        store=True
    )
    fecha_hora_carga = fields.Datetime(string='Fecha y hora carga')
    fecha_hora_descarga = fields.Datetime(string='Fecha y hora descarga')
    detalles_cita = fields.Text(string='Detalles cita')
    observaciones = fields.Text(string='Observaciones', tracking=True)
    especificaciones = fields.Text(string='Especificaciones', tracking=True)
    folio_cliente = fields.Char(string='Folio del cliente', tracking=True)
    suger_pago = fields.Boolean(string='Sugerir pago inmediato', tracking=True)
    no_pedimento = fields.Char(string='No. de pedimento')
    tipo_mov = fields.Selection([
            ('No especificado', 'No especificado'),
            ('Importación', 'Importación'),
            ('Exportación', 'Exportación')
        ],
        string='Tipo de movimiento'
    )
    no_contenedor_uno = fields.Char(string='No de contenedor 1')
    no_sello_uno = fields.Char(string='No. Sello 1')
    tipo_contenedor_uno = fields.Selection([
            ('No especificado', 'No especificado'),
            ('Seco', 'Seco'),
            ('Refrigerado', 'Refrigerado')
        ],
        string='Tipo de contenedor 1'
    )
    tamano_contenedor_uno = fields.Selection([
            ('No especificado', 'No especificado'),
            ('40 pies', '40 pies'),
            ('40 pies HC', '40 pies HC'),
            ('20 pies', '20 pies'),
            ('20 pies HC', '20 pies HC')
        ],
        string='Tamaño de contenedor 1'
    )
    no_contenedor_dos = fields.Char(string='No de contenedor 2')
    no_sello_dos = fields.Char(string='No. Sello 2')
    tipo_contenedor_dos = fields.Selection([
            ('No especificado', 'No especificado'),
            ('Seco', 'Seco'),
            ('Refrigerado', 'Refrigerado')
        ],
        string='Tipo de contenedor 2'
    )
    tamano_contenedor_dos = fields.Selection([
            ('No especificado', 'No especificado'),
            ('40 pies', '40 pies'),
            ('40 pies HC', '40 pies HC'),
            ('20 pies', '20 pies'),
            ('20 pies HC', '20 pies HC')
        ],
        string='Tamaño de contenedor 2'
    )

    @api.onchange('tipo_remolque', 'lineanegocio')
    def _onchange_pesos_(self):
        for rec in self:
            if rec.lineanegocio.id == 1:
                rec.peso_origen_remolque_1 = 0
                rec.peso_origen_remolque_2 = 0
                rec.peso_destino_remolque_1 = 0
                rec.peso_destino_remolque_2 = 0
                rec.peso_convenido_remolque_1 = 0
                rec.peso_convenido_remolque_2 = 0
            if rec.lineanegocio.id == 2 or rec.lineanegocio.id == 3:
                if rec.tipo_remolque.tipo == 'sencillo':
                    rec.peso_origen_remolque_1 = 1000
                    rec.peso_origen_remolque_2 = 0
                    rec.peso_destino_remolque_1 = 1000
                    rec.peso_destino_remolque_2 = 0
                    rec.peso_convenido_remolque_1 = 1000
                    rec.peso_convenido_remolque_2 = 0
                else:
                    rec.peso_origen_remolque_1 = 500
                    rec.peso_origen_remolque_2 = 500
                    rec.peso_destino_remolque_1 = 500
                    rec.peso_destino_remolque_2 = 500
                    rec.peso_convenido_remolque_1 = 500
                    rec.peso_convenido_remolque_2 = 500

    peso_origen_remolque_1 = fields.Float(
        string='Peso remolque origen 1 Kg',
        help='Peso origen del remolque 1 en kilogramos.',
        tracking=True
    )
    peso_origen_remolque_2 = fields.Float(
        string='Peso remolque origen 2 Kg',
        help='Peso origen del remolque 2 en kilogramos.',
        tracking=True
    )
    peso_destino_remolque_1 = fields.Float(
        string='Peso remolque destino 1 Kg',
        help='Peso destino del remolque 1 en kilogramos.',
        tracking=True
    )
    peso_destino_remolque_2 = fields.Float(
        string='Peso remolque destino 2 Kg',
        help='Peso destino del remolque 2 en kilogramos.',
        tracking=True
    )
    peso_convenido_remolque_1 = fields.Float(
        string='Peso remolque convenido 1 Kg',
        help='Peso convenido del remolque 1 en kilogramos.',
        tracking=True
    )
    peso_convenido_remolque_2 = fields.Float(
        string='Peso remolque convenido 2 Kg',
        help='Peso convenido del remolque 2 en kilogramos.',
        tracking=True
    )
    peso_origen_remolque_1_ver = fields.Float(
        string='Peso origen remolque 1 Kg',
        related='peso_origen_remolque_1',
        readonly=True
    )
    peso_origen_remolque_2_ver = fields.Float(
        string='Peso origen remolque 2 Kg',
        related='peso_origen_remolque_2',
        readonly=True
    )
    peso_destino_remolque_1_ver = fields.Float(
        string='Peso destino remolque 1 Kg',
        related='peso_destino_remolque_1',
        readonly=True
    )
    peso_destino_remolque_2_ver = fields.Float(
        string='Peso destino remolque 2 Kg',
        related='peso_destino_remolque_2',
        readonly=True
    )
    peso_convenido_remolque_1_ver = fields.Float(
        string='Peso convenidoremolque 1 Kg',
        related='peso_convenido_remolque_1',
        readonly=True
    )
    peso_convenido_remolque_2_ver = fields.Float(
        string='Peso convenido remolque 2 Kg',
        related='peso_convenido_remolque_2',
        readonly=True
    )

    @api.depends('peso_origen_remolque_1', 'peso_origen_remolque_2')
    def _compute_pesos_origen_total(self):
        for rec in self:
            rec.peso_origen_total = (
                rec.peso_origen_remolque_1
                + rec.peso_origen_remolque_2
            )

    @api.depends('peso_destino_remolque_1', 'peso_destino_remolque_2')
    def _compute_pesos_destino_total(self):
        for rec in self:
            rec.peso_destino_total = (
                rec.peso_destino_remolque_1
                + rec.peso_destino_remolque_2
            )

    @api.depends('peso_convenido_remolque_1', 'peso_convenido_remolque_2')
    def _compute_pesos_convenido_total(self):
        for rec in self:
            rec.peso_convenido_total = (
                rec.peso_convenido_remolque_1
                + rec.peso_convenido_remolque_2
            )

    peso_origen_total = fields.Float(
        string='Peso origen total Kg',
        compute='_compute_pesos_origen_total',
        store=True
    )
    peso_destino_total = fields.Float(
        string='Peso destino total Kg',
        compute='_compute_pesos_destino_total',
        store=True
    )
    peso_convenido_total = fields.Float(
        string='Peso convenido total Kg',
        compute='_compute_pesos_convenido_total',
        store=True
    )
    facturar_con = fields.Selection([
            ('Peso convenido', 'Peso convenido'),
            ('Peso origen', 'Peso origen'),
            ('Peso destino', 'Peso destino')
        ],
        string='Facturar con (Asociado)',
        required=True,
        default='Peso origen',
        tracking=True
    )
    facturar_con_cliente = fields.Selection([
            ('Peso convenido', 'Peso convenido'),
            ('Peso origen', 'Peso origen'),
            ('Peso destino', 'Peso destino')
        ],
        string='Facturar con (Cliente)',
        required=True,
        default='Peso origen',
        tracking=True
    )
    excedente_merma = fields.Selection([
            ('No cobrar', 'No cobrar'),
            (
                'Porcentaje: Cobrar diferencia',
                'Porcentaje: Cobrar diferencia'
            ),
            ('Porcentaje: Cobrar todo', 'Porcentaje: Cobrar todo'),
            ('Kg: Cobrar diferencia', 'Kg: Cobrar diferencia'),
            ('Kg: Cobrar todo', 'Kg: Cobrar todo'),
            ('Cobrar todo', 'Cobrar todo')
        ],
        string='Si la merma excede lo permitido',
        required=True,
        default='Porcentaje: Cobrar diferencia'
    )

    @api.onchange('peso_origen_total', 'peso_destino_total')
    def _onchange_merma_kg_(self):
        for rec in self:
            rec.merma_kg = 0
            if rec.peso_origen_total and rec.peso_destino_total:
                if rec.peso_destino_total > rec.peso_origen_total:
                    rec.merma_kg = 0
                else:
                    rec.merma_kg = (
                        rec.peso_origen_total
                        - rec.peso_destino_total
                    )
            else:
                rec.merma_kg = 0

    def _compute_merma_kg_(self):
        for rec in self:
            rec.merma_kg = 0
            if rec.peso_origen_total and rec.peso_destino_total:
                if rec.peso_destino_total > rec.peso_origen_total:
                    rec.merma_kg = 0
                else:
                    rec.merma_kg = (
                        rec.peso_origen_total
                        - rec.peso_destino_total
                    )
            else:
                rec.merma_kg = 0

    merma_kg = fields.Float(
        string='Merma Kg',
        compute='_compute_merma_kg_',
        readonly=True
    )

    @api.onchange('peso_origen_total', 'peso_destino_total', 'tipo_remolque')
    def _onchange_merma_pesos(self):
        for rec in self:
            if rec.peso_origen_total and rec.peso_destino_total:
                if rec.lineanegocio.id == 3:
                    rec.merma_pesos = 0
                else:
                    rec.merma_pesos = (rec.merma_kg) * rec.costo_producto
            else:
                rec.merma_pesos = 0

    @api.depends('merma_kg')
    def _compute_merma_pesos(self):
        for rec in self:
            if rec.peso_origen_total and rec.peso_destino_total:
                if rec.lineanegocio.id == 3:
                    rec.merma_pesos = 0
                else:
                    rec.merma_pesos = (
                        (rec.merma_kg / 1000)
                        * rec.costo_producto
                    )
            else:
                rec.merma_pesos = 0

    merma_pesos = fields.Float(
        string='Merma $',
        compute='_compute_merma_pesos',
        readonly=True
    )

    @api.onchange(
        'excedente_merma',
        'peso_origen_total',
        'peso_destino_total'
    )
    def _onchange_merma_permitida_kg(self):
        for rec in self:
            if rec.peso_origen_total and rec.peso_destino_total:
                if rec.excedente_merma:
                    if rec.excedente_merma == 'No cobrar':
                        rec.merma_permitida_kg = 0
                    else:
                        if rec.cliente_id.merma_permitida_por:
                            if rec.peso_origen_total > rec.peso_destino_total:
                                rec.merma_permitida_kg = (
                                    rec.cliente_id.merma_permitida_por
                                    * (rec.peso_origen_total / 100)
                                )
                            else:
                                rec.merma_permitida_kg = 0
            else:
                rec.merma_permitida_kg = 0

    def _compute_merma_permitida_kg(self):
        for rec in self:
            rec.merma_permitida_kg = 0
            if rec.peso_origen_total and rec.peso_destino_total:
                if rec.excedente_merma:
                    if rec.excedente_merma == 'No cobrar':
                        rec.merma_permitida_kg = 0
                    else:
                        if rec.cliente_id.merma_permitida_por:
                            if rec.peso_origen_total > rec.peso_destino_total:
                                rec.merma_permitida_kg = (
                                    rec.cliente_id.merma_permitida_por
                                    * (rec.peso_origen_total / 100)
                                )
                            else:
                                rec.merma_permitida_kg = 0
                        else:
                            rec.merma_permitida_kg = 0
                else:
                    rec.merma_permitida_kg = 0
            else:
                rec.merma_permitida_kg = 0

    merma_permitida_kg = fields.Float(
        string='Merma permitida Kg',
        compute='_compute_merma_permitida_kg',
        eadonly=True
    )

    @api.onchange('merma_permitida_kg', 'costo_producto')
    def _onchange_merma_permitida_pesos(self):
        for rec in self:
            if rec.peso_origen_total and rec.peso_destino_total:
                if rec.merma_permitida_kg:
                    rec.merma_permitida_pesos = (
                        rec.merma_permitida_kg
                        * rec.costo_producto
                    )
                else:
                    rec.merma_permitida_pesos = 0
            else:
                rec.merma_permitida_pesos = 0

    def _compute_merma_permitida_pesos(self):
        for rec in self:
            if rec.peso_origen_total and rec.peso_destino_total:
                if rec.merma_permitida_kg:
                    rec.merma_permitida_pesos = (
                        rec.merma_permitida_kg
                        * rec.costo_producto
                    )
                else:
                    rec.merma_permitida_pesos = 0
            else:
                rec.merma_permitida_pesos = 0

    merma_permitida_pesos = fields.Float(
        string='Merma permitida $',
        compute='_compute_merma_permitida_pesos',
        readonly=True
    )

    @api.onchange(
        'peso_origen_remolque_1',
        'peso_origen_remolque_2',
        'peso_destino_remolque_1',
        'peso_destino_remolque_2'
    )
    def _onchange_merma_total(self):
        for rec in self:
            if rec.peso_origen_remolque_1 > rec.peso_destino_remolque_1:
                merma_origen = (
                    rec.peso_origen_remolque_1
                    - rec.peso_destino_remolque_1
                )
            else:
                merma_origen = 0
            if rec.peso_origen_remolque_2 > rec.peso_destino_remolque_2:
                merma_destino = (
                    rec.peso_origen_remolque_2
                    - rec.peso_destino_remolque_2
                )
            else:
                merma_destino = 0
            rec.merma_total = merma_origen + merma_destino

    def _compute_merma_total(self):
        for rec in self:
            if rec.peso_origen_remolque_1 > rec.peso_destino_remolque_1:
                merma_origen = (
                    rec.peso_origen_remolque_1
                    - rec.peso_destino_remolque_1
                )
            else:
                merma_origen = 0
            if rec.peso_origen_remolque_2 > rec.peso_destino_remolque_2:
                merma_destino = (
                    rec.peso_origen_remolque_2
                    - rec.peso_destino_remolque_2
                )
            else:
                merma_destino = 0
            rec.merma_total = merma_origen + merma_destino

    merma_total = fields.Float(
        string='Merma total kg',
        compute='_compute_merma_total',
        readonly=True
    )

    @api.onchange('merma_kg', 'merma_permitida_kg')
    def _onchange_diferencia_porcentaje(self):
        for rec in self:
            if rec.merma_kg > rec.merma_permitida_kg:
                rec.diferencia_porcentaje = (
                    rec.merma_kg
                    - rec.merma_permitida_kg
                )
            else:
                rec.diferencia_porcentaje = 0

    def _compute_diferencia_porcentaje(self):
        for rec in self:
            if rec.merma_kg > rec.merma_permitida_kg:
                rec.diferencia_porcentaje = (
                    rec.merma_kg
                    - rec.merma_permitida_kg
                )
            else:
                rec.diferencia_porcentaje = 0

    diferencia_porcentaje = fields.Float(
        string='diferencia_porcentaje',
        compute='_compute_diferencia_porcentaje',
        readonly=True
    )

    @api.onchange('merma_kg', 'cliente_id')
    def _onchange_diferencia_kg(self):
        for rec in self:
            if rec.merma_kg > rec.cliente_id.merma_permitida_kg:
                rec.diferencia_kg = (
                    rec.merma_kg
                    - rec.cliente_id.merma_permitida_kg
                )
            else:
                rec.diferencia_kg = 0

    def _compute_diferencia_kg(self):
        for rec in self:
            if rec.merma_kg > rec.cliente_id.merma_permitida_kg:
                rec.diferencia_kg = (
                    rec.merma_kg
                    - rec.cliente_id.merma_permitida_kg
                )
            else:
                rec.diferencia_kg = 0

    diferencia_kg = fields.Float(
        string='diferencia_porcentaje kg',
        compute='_compute_diferencia_kg',
        readonly=True
    )

    @api.onchange(
        'excedente_merma',
        'merma_permitida_kg',
        'diferencia_porcentaje',
        'diferencia_kg',
        'peso_origen_total',
        'peso_destino_total'
    )
    def _onchange_merma_cobrar_kg(self):
        for rec in self:
            if rec.peso_origen_total > rec.peso_destino_total:
                if rec.excedente_merma:
                    if rec.excedente_merma == 'No cobrar':
                        rec.merma_cobrar_kg = 0
                    if rec.excedente_merma == 'Porcentaje: Cobrar diferencia':
                        if rec.merma_kg > rec.cliente_id.merma_permitida_kg:
                            rec.merma_cobrar_kg = (
                                (rec.merma_kg / 1000)
                                - rec.merma_permitida_kg
                            )
                            rec.merma_permitida_kg = (
                                rec.peso_origen_total
                                * (rec.cliente_id.merma_permitida_por) / 100
                            )
                        else:
                            rec.merma_cobrar_kg = 0
                    if rec.excedente_merma == 'Porcentaje: Cobrar todo':
                        if rec.merma_kg > rec.cliente_id.merma_permitida_kg:
                            rec.merma_cobrar_kg = (rec.merma_kg / 1000)
                            rec.merma_permitida_kg = (
                                rec.peso_origen_total
                                * rec.cliente_id.merma_permitida_por
                            ) / 100
                        else:
                            rec.merma_cobrar_kg = 0
                    if rec.excedente_merma == 'Kg: Cobrar diferencia':
                        if rec.merma_kg > rec.cliente_id.merma_permitida_kg:
                            rec.merma_cobrar_kg = (
                                (rec.merma_kg / 1000)
                                - rec.cliente_id.merma_permitida_kg
                            )
                            rec.merma_permitida_kg = (
                                rec.cliente_id.merma_permitida_kg
                            )
                        else:
                            rec.merma_cobrar_kg = 0
                            rec.merma_permitida_kg = (
                                rec.cliente_id.merma_permitida_kg
                            )
                    if rec.excedente_merma == 'Kg: Cobrar todo':
                        if rec.merma_kg > rec.cliente_id.merma_permitida_kg:
                            rec.merma_cobrar_kg = (rec.merma_kg / 1000)
                            rec.merma_permitida_kg = (
                                rec.cliente_id.merma_permitida_kg
                            )
                        else:
                            rec.merma_cobrar_kg = 0
                            rec.merma_permitida_kg = (
                                rec.cliente_id.merma_permitida_kg
                            )
                    if rec.excedente_merma == 'Cobrar todo':
                        rec.merma_cobrar_kg = (rec.merma_kg / 1000)
                        rec.merma_permitida_kg = (
                            rec.cliente_id.merma_permitida_kg
                        )
            else:
                rec.merma_cobrar_kg = 0
                rec.merma_permitida_kg = rec.cliente_id.merma_permitida_kg

    @api.depends(
        'peso_origen_total',
        'peso_destino_total',
        'merma_kg',
        'merma_permitida_kg',
        'diferencia_porcentaje',
        'diferencia_kg'
    )
    def _compute_merma_cobrar_kg(self):
        for rec in self:
            if rec.peso_origen_total > rec.peso_destino_total:
                if rec.excedente_merma:
                    if rec.excedente_merma == 'No cobrar':
                        rec.merma_cobrar_kg = 0
                    if rec.excedente_merma == 'Porcentaje: Cobrar diferencia':
                        if rec.merma_kg > rec.cliente_id.merma_permitida_kg:
                            rec.merma_cobrar_kg = (
                                rec.merma_kg
                                - rec.merma_permitida_kg
                            )
                            rec.merma_permitida_kg = (
                                rec.peso_origen_total
                                * rec.cliente_id.merma_permitida_por
                            ) / 100
                        else:
                            rec.merma_cobrar_kg = 0
                            rec.merma_permitida_kg = (
                                rec.peso_origen_total
                                * rec.cliente_id.merma_permitida_por
                            ) / 100
                    if rec.excedente_merma == 'Porcentaje: Cobrar todo':
                        if rec.merma_kg > rec.cliente_id.merma_permitida_kg:
                            rec.merma_cobrar_kg = rec.merma_kg
                            rec.merma_permitida_kg = (
                                rec.peso_origen_total
                                * rec.cliente_id.merma_permitida_por
                            ) / 100
                        else:
                            rec.merma_cobrar_kg = 0
                            rec.merma_permitida_kg = (
                                rec.peso_origen_total
                                * rec.cliente_id.merma_permitida_por
                            ) / 100
                    if rec.excedente_merma == 'Kg: Cobrar diferencia':
                        if rec.merma_kg > rec.cliente_id.merma_permitida_kg:
                            rec.merma_cobrar_kg = (
                                rec.merma_kg
                                - rec.cliente_id.merma_permitida_kg
                            )
                        else:
                            rec.merma_cobrar_kg = 0
                    if rec.excedente_merma == 'Kg: Cobrar todo':
                        if rec.merma_kg > rec.cliente_id.merma_permitida_kg:
                            rec.merma_cobrar_kg = rec.merma_kg
                        else:
                            rec.merma_cobrar_kg = 0
                    if rec.excedente_merma == 'Cobrar todo':
                        rec.merma_cobrar_kg = rec.merma_kg
            else:
                rec.merma_cobrar_kg = 0

    merma_cobrar_kg = fields.Float(
        string='Merma cobrar kg',
        compute='_compute_merma_cobrar_kg',
        readonly=True
    )

    @api.onchange('merma_cobrar_kg', 'costo_producto')
    def _onchange_merma_cobrar_pesos(self):
        for rec in self:
            if rec.merma_cobrar_kg > 0:
                rec.merma_cobrar_pesos = (
                    rec.merma_cobrar_kg
                    * rec.costo_producto
                )
            else:
                rec.merma_cobrar_pesos = 0

    @api.depends('merma_cobrar_kg', 'costo_producto')
    def _compute_merma_cobrar_pesos(self):
        for rec in self:
            if rec.merma_cobrar_kg > 0:
                rec.merma_cobrar_pesos = (
                    rec.merma_cobrar_kg
                    * rec.costo_producto
                )
                valores = {
                    'viaje_id': rec.id,
                    'monto': rec.merma_cobrar_pesos,
                    'tipo_cargo': 'merma',
                    'asociado_id': rec.asociado_id.id
                }
                obc_cargos = self.env['trafitec.cargos'].search([
                    '&',
                    ('viaje_id', '=', rec.id),
                    ('tipo_cargo', '=', 'merma')
                ])
                if len(obc_cargos) == 0:
                    self.env['trafitec.cargos'].create(valores)
                else:
                    obc_cargos.write(valores)
            else:
                rec.merma_cobrar_pesos = 0

    merma_cobrar_pesos = fields.Float(
        string='Merma cobrar $',
        compute='_compute_merma_cobrar_pesos',
        readonly=True
    )
    boletas_id = fields.One2many(
        comodel_name="trafitec.viajes.boletas",
        inverse_name="linea_id",
        tracking=True
    )
    evidencia_id = fields.One2many(
        string="Evidencias",
        comodel_name="trafitec.viajes.evidencias",
        inverse_name="linea_id",
        tracking=True
    )

    @api.constrains('evidencia_id', 'documentacion_completa', 'name')
    def _check_evidencia(self):
        if self.documentacion_completa:
            obj_eviden = self.env['trafitec.viajes.evidencias'].search([
                ('linea_id', '=', self.id),
                ('name', '=', 'Evidencia de viaje')
            ])
            if len(obj_eviden) == 0:
                raise UserError(_(
                    'Aviso !\nNo puede aplicar como documentación completa,'
                    + ' si no tiene ninguna evidencia de viaje'
                ))

    @api.constrains(
        'regla_comision',
        'motivo',
        'porcent_comision',
        'cant_especifica'
    )
    def _check_comision_motivo(self):
        for rec in self:
            if rec.regla_comision == 'No cobrar':
                if not rec.motivo:
                    raise UserError(_(
                        'Aviso !\nDebe capturar el motivo por el cual no se '
                        + 'cobra comisión'
                    ))
            if 'Con % especifico' in rec.regla_comision:
                if rec.porcent_comision == 0 or rec.porcent_comision == 0.00:
                    raise UserError(_(
                        'Aviso !\nDebe capturar el porcentaje de la comisión'
                    ))
            if rec.regla_comision == 'Cobrar cantidad especifica':
                if rec.cant_especifica == 0 or rec.cant_especifica == 0.00:
                    raise UserError(
                        _('Aviso !\nDebe capturar la cantidad especifica'))

    conteo = fields.Char(
        string="Conteo",
        compute="_compute_conteo",
        default="0"
    )

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'trafitec.viajes'
            ) or _('New')
        cliente_obj = None
        cliente_dat = None
        error = False
        errores = ""
        if self._context.get('validar_credito_cliente', True):
            self._valida_credito(vals, 1)
        if self._context.get('validar_cliente_moroso', True):
            self._valida_moroso(vals)
        cliente_obj = self.env['res.partner']
        cliente_dat = cliente_obj.browse([vals.get('cliente_id')])
        if cliente_dat:
            if cliente_dat.bloqueado_cliente_bloqueado:
                raise UserError(_(
                    'El cliente esta bloqueado, motivo: '
                    + (
                        cliente_dat.bloqueado_cliente_clasificacion_id.name
                        or ''
                    )
                ))
        error = False
        errores = ""
        placas_id = self.env['fleet.vehicle'].search([
            ('id', '=', vals['placas_id'])
        ])
        vals['asociado_id'] = placas_id.asociado_id.id
        vals['porcentaje_comision'] = (
            placas_id.asociado_id.porcentaje_comision
        )
        vals['usar_porcentaje'] = placas_id.asociado_id.usar_porcentaje
        vals['creditocomision'] = placas_id.asociado_id.creditocomision
        vals['operador_id'] = placas_id.operador_id.id
        vals['no_economico'] = placas_id.no_economico
        marca = placas_id.name
        if placas_id.es_flotilla:
            vals.update(
                {
                    'estado_viaje': 'iniciado',
                    'slitrack_proveedor': 'geotab',
                    'slitrack_estado': 'iniciado'
                }
            )
            viajes_dat = self.env['trafitec.viajes'].search([
                ('placas_id', '=', placas_id.id),
                ('estado_viaje', '=', 'iniciado')
            ])
            for v in viajes_dat:
                v.with_context(validar_credito_cliente=False).write(
                    {
                        'estado_viaje': 'terminado',
                        'slitrack_estado': 'terminado'
                    }
                )
        if placas_id.modelo:
            modelo = placas_id.modelo
        else:
            modelo = ''

        if placas_id.color:
            color = placas_id.color
        else:
            color = ''
        str_vehiculo = '{}, {}, {}'.format(marca, modelo, color)
        vals['vehiculo'] = str_vehiculo
        if 'tipo_remolque' in vals:
            tipo_remol = self.env['trafitec.moviles'].search([
                ('id', '=', vals['tipo_remolque'])
            ])
            if vals['lineanegocio'] == 3 or vals['lineanegocio'] == 2:
                vals['peso_origen_total'] = 1000
                vals['peso_destino_total'] = 1000
                vals['peso_convenido_total'] = 1000
                if tipo_remol.tipo == 'sencillo':
                    vals['peso_origen_remolque_1'] = 1000
                    vals['peso_origen_remolque_2'] = 0
                    vals['peso_destino_remolque_1'] = 1000
                    vals['peso_destino_remolque_2'] = 0
                    vals['peso_convenido_remolque_1'] = 1000
                    vals['peso_convenido_remolque_2'] = 0
                else:
                    vals['peso_origen_remolque_1'] = 500
                    vals['peso_origen_remolque_2'] = 500
                    vals['peso_destino_remolque_1'] = 500
                    vals['peso_destino_remolque_2'] = 500
                    vals['peso_convenido_remolque_1'] = 500
                    vals['peso_convenido_remolque_2'] = 500
        viaje_nuevo = super(trafitec_viajes, self).create(vals)
        return viaje_nuevo

    def write(self, vals):
        if self._context.get('validar_credito_cliente', True):
            self._valida_credito(vals, 2)
        error_titulo = "Hay descuentos con abonos:"
        error = False
        errores = ""
        if 'asociado_id' in vals:
            descuentos_obj = self.env['trafitec.descuentos']
            descuentos_dat = descuentos_obj.search([
                ('viaje_id', '=', self.id)
            ])
            for d in descuentos_dat:
                if d.abono_total > 0:
                    error = True
                    errores += "Descuento {} total: {:20,.2f}\n".format(
                        d.id,
                        d.monto
                    )
            if not error:
                for d in descuentos_dat:
                    d.asociado_id = vals['asociado_id']
        if error:
            raise UserError(_(error_titulo+"\n"+errores))
        if 'placas_id' in vals:
            placas_id = self.env['fleet.vehicle'].search([
                ('id', '=', vals['placas_id'])
            ])
            vals['asociado_id'] = placas_id.asociado_id.id
            vals['porcentaje_comision'] = (
                placas_id.asociado_id.porcentaje_comision
            )
            vals['usar_porcentaje'] = placas_id.asociado_id.usar_porcentaje
            vals['creditocomision'] = placas_id.asociado_id.creditocomision
            vals['operador_id'] = placas_id.operador_id.id
            vals['no_economico'] = placas_id.no_economico
            marca = placas_id.name
            if placas_id.modelo:
                modelo = placas_id.modelo
            else:
                modelo = ''
            if placas_id.color:
                color = placas_id.color
            else:
                color = ''
            str_vehiculo = '{}, {}, {}'.format(marca, modelo, color)
            vals['vehiculo'] = str_vehiculo
        if 'tipo_remolque' in vals:
            tipo_remolque = vals['tipo_remolque']
        else:
            tipo_remolque = self.tipo_remolque.id
        return super(trafitec_viajes, self).write(vals)

    def copy(self):
        raise UserError(_('Alerta..\nNo esta permitido duplicar viajes.'))

    def _valida_moroso(self, vals=None):
        for rec in self:
            if vals is None:
                return
            persona_id = (
                ('cliente_id' in vals)
                and vals['cliente_id']
                or rec.cliente_id.id
            )
            saldo = 0.00
            es_moroso = False
            persona_obj = self.env['res.partner']
            saldo = persona_obj.saldo_vencido(persona_id)
            es_moroso = persona_obj.es_moroso(persona_id)
            if es_moroso:
                raise UserError(
                    _(
                        "El cliente tiene facturas vencidas por: "
                        + "{:20,.2f}.".format(saldo)
                    )
                )

    def _valida_credito(self, vals, tipo=1):
        for rec in self:
            if not self._context.get('validar_credito_cliente', True):
                return
            error = False
            errores = ""
            viaje_obj = self.env['trafitec.viajes']
            persona_id = (
                ('cliente_id' in vals)
                and vals['cliente_id']
                or rec.cliente_id.id
            )
            tiporemolque_id = (
                ('tipo_remolque' in vals)
                and vals['tipo_remolque']
                or rec.tipo_remolque.id
            )
            peso_origen_remolque_1 = (
                'peso_origen_remolque_1' in vals
                and vals['peso_origen_remolque_1']
                or rec.peso_origen_remolque_1
            )
            peso_origen_remolque_2 = (
                'peso_origen_remolque_2' in vals
                and vals['peso_origen_remolque_2']
                or rec.peso_origen_remolque_2
            )
            tarifa_cliente = (
                'tarifa_cliente' in vals
                and vals['tarifa_cliente']
                or rec.tarifa_cliente
            )
            peso_autorizado = (
                'peso_autorizado' in vals
                and vals['peso_autorizado']
                or rec.peso_autorizado
            )
            persona_obj = self.env['res.partner']
            tiporemolque_obj = self.env['trafitec.moviles']
            tiporemolque_dat = tiporemolque_obj.search([
                ('id', '=', tiporemolque_id)
            ])
            capacidad = peso_autorizado
            flete_cliente = (
                tarifa_cliente
                * (
                    peso_origen_remolque_1
                    + peso_origen_remolque_2
                ) / 1000
            )
            if flete_cliente <= 0:
                flete_cliente = tarifa_cliente * (capacidad / 1000)

            persona_datos = persona_obj.search([('id', '=', persona_id)])
            cliente_nombre = persona_datos.name
            cliente_saldo = persona_obj.cliente_saldo_total(
                persona_id,
                (rec.id and rec.id or None)
            ) + flete_cliente
            cliente_limite_credito = persona_datos.limite_credito
            if error:
                raise UserError(_(errores))