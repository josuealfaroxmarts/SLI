# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class TrafitecCargos(models.Model):
    _name = 'trafitec.cargos'
    _order = 'id desc'
    _description = 'Cargos'

    viaje_id = fields.Many2one(
        'trafitec.viajes',
        string='Viajes ID',
        ondelete='cascade',
        readonly=False
    )
    saldo = fields.Float(
        compute='_compute_saldo',
        string='Saldo',
        store=True
    )
    monto = fields.Float(
        string='Monto',
        readonly=False
    )
    tipo_cargo = fields.Selection(
        string='Tipo de cargo',
        selection=[
            ('comision', 'comision'),
            ('merma', 'merma'),
            ('descuentos', 'descuentos')
        ]
    )
    asociado_id = fields.Many2one(
        'res.partner',
        domain=[('asociado', '=', True)],
        string='Asociado',
        required=True,
        readonly=False
    )
    descuento_id = fields.Many2one(
        'trafitec.descuentos',
        string='ID descuentos',
        ondelete='cascade'
    )
    abono_id = fields.One2many(
        'trafitec.comisiones.abono',
        'abonos_id'
    )
    valor = fields.Char(string='valor')
    abonado = fields.Float(
        compute='_compute_abonado',
        string='Abonado',
        store=True
    )

    def unlink(self):
        if len(self) > 1:
            raise UserError((
                'Alerta..\nNo se puede eliminar mas de una comisión a la vez.'
            ))
        if self.tipo_cargo == 'comision':
            if self.viaje_id.id:
                raise UserError((
                    'Aviso !\nNo se puede eliminar una comision que tenga '
                    + 'viajes.'
                ))
            if self.abonado > 0:
                raise UserError((
                    'Aviso !\nNo se puede eliminar una comision que tenga '
                    + 'abonos.'
                ))
        return super(TrafitecCargos, self).unlink()

    def name_get(self):
        result = []
        name = ''
        for rec in self:
            if rec.id:
                name = str(rec.id) + ' '
                result.append((rec.id, name))
            else:
                result.append((rec.id, name))
        return result

    @api.depends('abono_id.name')
    def _compute_abonado(self):
        for cargo in self:
            cargo.abonado = sum(line.name for line in cargo.abono_id)

    @api.depends('abono_id', 'monto', 'abonado')
    def _compute_saldo(self):
        for cargo in self:
            cargo.saldo = cargo.monto - cargo.abonado
