# -*- coding: utf-8 -*-

import datetime

from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class trafitec_viaje_cancelar(models.TransientModel):
    _name = 'trafitec.viaje.cancelar.wizard'
    _description = 'viaje cancelar wizard'

    viaje_id = fields.Many2one('trafitec.viajes', default=_get_viajeid)
    motivo = fields.Text(string='Motivo')

    def _get_viajeid(self):
        viajes_obj = self.env['trafitec.viajes'].search([
                ('id', '=', self._context.get('active_id'))
            ],
            limit=1
        )
        if viajes_obj.en_contrarecibo:
            raise UserError(_(
                "El viaje seleccionado ya tiene contra recibo."
            ))
        if viajes_obj.en_factura:
            raise UserError(_("El viaje seleccionado ya tiene factura."))
        if viajes_obj.en_cp:
            raise UserError(_("El viaje seleccionado ya tiene carta porte."))
        return viajes_obj

    def cancelacion_button(self):
        self.ensure_one()
        for line in self:
            if line.viaje_id.state == 'Cancelado':
                raise UserError(
                    _(
                        'Aviso !\nNo se puede cancelar un viaje que ya esta '
                        + 'cancelado.'
                    )
                )
            if line.viaje_id.en_factura:
                raise UserError(_(
                    'Aviso !\nNo se puede cancelar un viaje con factura.'
                ))
            if line.viaje_id.en_contrarecibo:
                raise UserError(
                    _(
                        'Aviso !\nNo se puede cancelar un viaje con contra '
                        + 'recibo.'
                    )
                )
            descuento_obj = self.env['trafitec.descuentos'].search([
                ('viaje_id', '=', line.viaje_id.id),
                ('abono_total', '>', 0)
            ])
            if len(descuento_obj) > 0:
                raise UserError(
                    _(
                        'Aviso !\nNo se puede cancelar un viaje que tenga '
                        + 'descuentos relacionados.'
                    )
                )
            comision_obj = self.env['trafitec.cargos'].search([
                ('viaje_id', '=', line.viaje_id.id),
                ('tipo_cargo', '=', 'comision'),
                ('abonado', '>', 0)
            ])
            if len(comision_obj) > 0:
                raise UserError(
                    _(
                        'Aviso !\nNo se puede cancelar un viaje que tenga la '
                        + 'comisiones relacionadas.'
                    )
                )
            line.viaje_id.with_context(validar_credito_cliente=False).write({
                'motivo_cancelacion': line.motivo,
                'state': 'Cancelado',
                'fecha_cambio_estado': datetime.datetime.now()
            })