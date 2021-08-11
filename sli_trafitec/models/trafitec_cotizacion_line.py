# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class TrafitecCotizacionLine(models.Model):
    _name = 'trafitec.cotizaciones.linea'
    _description = 'cotizaciones linea'

    name = fields.Char(string='Folio de cliente')
    municipio_origen_id = fields.Char(
        string='Municipio Origen',
        required=True
    )
    municipio_destino_id = fields.Char(
        string='Municipio Destino',
        required=True
    )
    distancia = fields.Float(
        string='Distancia',
        required=True
    )
    km_vacio = fields.Float(string='Km. vacio')
    km_cargado = fields.Float(string='Km. Cargado')
    ritmo_carga = fields.Float(string='Ritmo de carga')
    tarifa_asociado = fields.Float(
        string='Tarifa asociado',
        required=True
    )
    tarifa_cliente = fields.Float(
        string='Tarifa cliente',
        required=True
    )
    cantidad = fields.Integer(
        string='Cantidad',
        required=True
    )
    product_uom = fields.Many2one(
        'uom.uom',
        string='Unidad de medida',
        required=True,
        domain=[
            ('trafitec', '=', True)
        ]
    )
    detalle_asociado = fields.Text(string='Detalle Origen')
    detalle_destino = fields.Text(string='Detalle Destino')
    cotizacion_id = fields.Many2one(
        'trafitec.cotizacion',
        string='Cotizacion',
        ondelete='cascade'
    )
    nombre_cotizacion = fields.Char(
        related='cotizacion_id.nombre',
        string='Nombre de cotizacion'
    )
    cliente_cotizacion = fields.Many2one(
        related='cotizacion_id.cliente',
        string='Cliente'
    )
    origen_ubicacion = fields.Many2one(
        related='cotizacion_id.origen_id',
        string='Ubicacion origen'
    )
    destino_ubicacion = fields.Many2one(
        related='cotizacion_id.destino_id',
        string='Ubicacion destino'
    )
    cargos_id = fields.One2many(
        'trafitec.cotizaciones.linea.cargos',
        'linea_id'
    )
    origen_id = fields.One2many(
        'trafitec.cotizaciones.linea.origen',
        'linea_id'
    )
    negociacion_id = fields.One2many(
        'trafitec.cotizacion.linea.negociacion',
        'linea_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='cotizacion_id.lista_precio.currency_id',
        string='Currency',
        readonly=True,
        required=True
    )
    state = fields.Selection(
        string='Estado',
        related='cotizacion_id.state',
        store=True,
        readonly=True
    )
    permitir_ta_mayor_tc = fields.Boolean(
        string='Ta>tc',
        default=False,
        help='Pertimir ta mayor a tc.'
    )
    total_movimientos = fields.Monetary(
        string='Total movimientos',
        readonly=True,
        compute='_total_mov',
        tracking=True
    )
    total_cargos = fields.Monetary(
        string='Total cargos',
        readonly=True,
        compute='_total_cargos',
        tracking=True
    )
    subtotal = fields.Monetary(
        string='Subtotal',
        readonly=True,
        compute='_subtotal',
        tracking=True
    )

    @api.constrains('negociacion_id')
    def _check_negociaciones(self):
        for rec in self:
            error = False
            errores = ''
            tiene_asociado = False
            tiene_tiporemolque = False
            for n in rec.negociacion_id:
                tiene_asociado = False
                tiene_tiporemolque = False
                if n.asociado_id:
                    tiene_asociado = True
                if n.tiporemolque_id:
                    tiene_tiporemolque = True
                if not tiene_asociado and not tiene_tiporemolque:
                    error = True
                    errores += (
                        'Debe especificar el asociado o el tipo de remolque '
                        + 'en cada negociación.\n'
                    )
                if tiene_asociado and tiene_tiporemolque:
                    for n2 in rec.negociacion_id:
                        if (
                            n.id == n2.id
                            or n.asociado_id.id != n2.asociado_id.id
                        ):
                            continue
                        if n.tiporemolque_id.id == n2.tiporemolque_id.id:
                            raise UserError(
                                'El asociado {} ya tiene registro con'.format(
                                    n.asociado_id.name
                                )
                                + ' tipo de remolque {}'.format(
                                    n.tiporemolque_id.name
                                )
                            )
            if error:
                raise UserError(errores)

    @api.constrains('cantidad')
    def _check_cantidad(self):
        for rec in self:
            if rec.cantidad <= 0:
                raise UserError(
                    ('Error !\nEn la cantidad debe ser un valor mayor 0')
                )

    @api.constrains('distancia')
    def _check_distancia(self):
        for rec in self:
            if rec.distancia < 0:
                raise UserError(
                    'Error !\nNo se permite valores negativos en la distancia'
                )

    @api.constrains('km_vacio')
    def _check_km_vacio(self):
        for rec in self:
            if rec.km_vacio < 0:
                raise UserError(
                    'Error !\nNo se permite valores negativos en el Km. Vacio'
                )

    @api.constrains('km_cargado')
    def _check_km_cargado(self):
        for rec in self:
            if rec.km_cargado < 0:
                raise UserError(
                    'Error !\nNo se permite valores negativos en el Km. '
                    + 'Cargado'
                )

    @api.constrains('tarifa_asociado')
    def _check_tarifa_asociado(self):
        for rec in self:
            if rec.tarifa_asociado <= 0:
                raise UserError(
                    'Error !\nNo se permite valores negativos o en 0 en la '
                    + 'tarifa asociado'
                )

    @api.constrains('tarifa_cliente')
    def _check_tarifa_cliente(self):
        for rec in self:
            if rec.tarifa_cliente <= 0:
                raise UserError(
                    'Error !\nNo se permite valores negativos o en 0 en la '
                    + 'tarifa cliente'
                )

    @api.constrains('ritmo_carga')
    def _check_ritmo_carga(self):
        for rec in self:
            if rec.ritmo_carga < 0:
                raise UserError(
                    'Error !\nNo se permite valores negativos o en 0 en el '
                    + 'ritmo de carga'
                )

    @api.constrains('tarifa_cliente', 'tarifa_asociado')
    def _check_tarifas_mayor(self):
        for rec in self:
            if rec.tarifa_asociado > rec.tarifa_cliente:
                if not rec.permitir_ta_mayor_tc:
                    raise UserError(
                        'Error !\nLa tarifa asociado no puede ser mayor a la '
                        + 'tarifa cliente.'
                    )

    def _total_mov(self):
        for rec in self:
            if rec.tarifa_cliente and rec.cantidad:
                rec.total_movimientos = rec.cantidad * rec.tarifa_cliente
            else:
                rec.total_movimientos = 0

    @api.onchange('cantidad')
    def total_mov(self):
        for rec in self:
            if rec.tarifa_cliente and rec.cantidad:
                rec.total_movimientos = rec.cantidad * rec.tarifa_cliente

    @api.onchange('tarifa_asociado', 'tarifa_cliente')
    def _onchange_tarifa(self):
        for rec in self:
            if rec.tarifa_cliente > 0 and rec.tarifa_asociado > 0:
                if (
                    rec.tarifa_asociado > rec.tarifa_cliente
                    and not rec.permitir_ta_mayor_tc
                ):
                    raise UserError(
                        'Error !\n La tarifa asociado no puede ser mayor a '
                        + 'la tarifa cliente.'
                    )

    @api.depends('cargos_id.total')
    def _total_cargos(self):
        for cargos in self:
            monto = 0
            for line in cargos.cargos_id:
                if monto == 0:
                    monto = line.total
                else:
                    monto += line.total

            cargos.update({
                'total_cargos': monto
            })

    def _subtotal(self):
        for rec in self:
            rec.subtotal = rec.total_cargos + rec.total_movimientos

    def explict_subscription(self):
        for rec in self:
            action_ctx = dict(rec.env.context)
            view_id = self.env.ref('sli_trafitec.linea_Cargos_form_inherit').id
            return {
                'name': _('Cargos adicionales'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'trafitec.cotizaciones.linea',
                'views': [(view_id, 'form')],
                'view_id': view_id,
                'target': 'new',
                'res_id': rec.ids[0],
                'context': action_ctx
            }

    def explict_origen_dest(self):
        for rec in self:
            action_ctx = dict(self.env.context)
            action_ctx.update({
                'municipio_origen': rec.municipio_origen_id.id,
                'municipio_destino': rec.municipio_destino_id.id
            })
            view_id = self.env.ref(
                'sli_trafitec.linea_origenes_form_inherit'
            ).id
            return {
                'name': _('Origenes y destinos'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'trafitec.cotizaciones.linea',
                'views': [(view_id, 'form')],
                'view_id': view_id,
                'target': 'new',
                'res_id': rec.ids[0],
                'context': action_ctx
            }

    def explict_negociacion(self):
        for rec in self:
            action_ctx = dict(rec.env.context)
            view_id = self.env.ref(
                'sli_trafitec.linea_negociancion_form_inherit'
            ).id
            return {
                'name': _('Negociaciones'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'trafitec.cotizaciones.linea',
                'views': [(view_id, 'form')],
                'view_id': view_id,
                'target': 'new',
                'res_id': rec.ids[0],
                'context': action_ctx
            }
