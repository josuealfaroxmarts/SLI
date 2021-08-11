# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class TrafitecViajesBoletas(models.Model):
    _name = 'trafitec.viajes.boletas'
    _description = 'viajes boletas'

    name = fields.Char(string='Folio de boleta', required=True, tracking=True)
    tipo_boleta = fields.Selection(
        string="Tipo de boleta",
        selection=[('Origen', 'Origen'), ('Destino', 'Destino')],
        required=True,
        tracking=True
    )
    linea_id = fields.Many2one(
        comodel_name="trafitec.viajes",
        string="Folio de viaje",
        ondelete='cascade'
    )

    fecha = fields.Date(
        related='linea_id.fecha_viaje',
        string='Fecha',
        store=True
    )
    cliente = fields.Many2one(
        related='linea_id.cliente_id',
        string='Cliente',
        store=True
    )
    origen = fields.Many2one(
        related='linea_id.origen',
        string='Origen',
        store=True
    )
    destino = fields.Many2one(
        related='linea_id.destino',
        string='Destino',
        store=True
    )
    tipo_viaje = fields.Selection(
        related='linea_id.tipo_viaje',
        string='Tipo de viaje',
        store=True
    )
    factura_id = fields.Many2one(
        related='linea_id.factura_cliente_id',
        string='Factura cliente',
        store=True
    )
    state = fields.Selection(
        related='linea_id.state',
        string='Estado',
        store=True
    )

    @api.model
    def create(self, vals):
        object_boletas = self.env['trafitec.viajes.boletas'].search([
            ('name', '=ilike', vals['name'])
        ])
        object_viaje = self.env['trafitec.viajes'].search([
            ('id', '=', vals['linea_id'])
        ])
        for object_bolets in object_boletas:
            if vals['tipo_boleta'] == 'Origen':
                if (
                    object_viaje.origen.id == object_bolets.linea_id.origen.id
                    and object_viaje.cliente_id.id == (
                        object_bolets.linea_id.cliente_id.id
                    )
                    and object_bolets.tipo_boleta == 'Origen'
                ):
                    raise UserError(
                        _(
                            'Alerta..\nYa existe un folio para este cliente y'
                            + ' bodega de origen.'
                        )
                    )
            else:
                if (
                    object_viaje.destino.id == (
                        object_bolets.linea_id.destino.id
                    )
                    and object_viaje.cliente_id.id == (
                        object_bolets.linea_id.cliente_id.id
                    )
                    and object_bolets.tipo_boleta == 'Destino'
                ):
                    raise UserError(
                        _(
                            'Alerta..\nYa existe un folio para este cliente y'
                            + ' bodega de destino.'
                        )
                    )

        return super(TrafitecViajesBoletas, self).create(vals)

    def write(self, vals):
        if 'name' in vals:
            name = vals['name']
        else:
            name = self.name
        if 'tipo_boleta' in vals:
            tipo_boleta = vals['tipo_boleta']
        else:
            tipo_boleta = self.tipo_boleta
        object_boletas = self.env['trafitec.viajes.boletas'].search([
            ('name', '=ilike', name)
        ])
        object_viaje = self.env['trafitec.viajes'].search([
            ('id', '=', self.linea_id.id)
        ])
        for object_bolets in object_boletas:
            if tipo_boleta == 'Origen':
                if (
                    object_viaje.origen.id == object_bolets.linea_id.origen.id
                    and object_viaje.cliente_id.id == (
                        object_bolets.linea_id.cliente_id.id
                    )
                    and object_bolets.tipo_boleta == 'Origen'
                ):
                    raise UserError(
                        _(
                            'Aviso !\nYa existe un folio para este cliente y '
                            + 'bodega de origen.'
                        )
                    )
            else:
                if (
                    object_viaje.destino.id == (
                        object_bolets.linea_id.destino.id
                    )
                    and object_viaje.cliente_id.id == (
                        object_bolets.linea_id.cliente_id.id
                    )
                    and object_bolets.tipo_boleta == 'Destino'
                ):
                    raise UserError(
                        _(
                            'Aviso !\nYa existe un folio para este cliente y '
                            + 'bodega de destino.'
                        )
                    )

        return super(TrafitecViajesBoletas, self).write(vals)