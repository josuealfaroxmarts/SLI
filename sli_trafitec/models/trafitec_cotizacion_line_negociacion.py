# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools,_
from odoo.exceptions import UserError

class TrafitecCotizacionLineNegociacion(models.Model):
    _name = 'trafitec.cotizacion.linea.negociacion'
    _description='cotizacion linea negociacion'

    tipo = fields.Selection(
        string='Tipo',
        selection=[
            ('con_asociado', 'Con asociado'),
            ('con_tiporemolque', 'Con tipo de remolque'),
            ('con_asociado_tiporemolque', 'Con asociado y tipo de remolque')
        ],
        default='con_asociado',
        required=True
    )
    asociado_id = fields.Many2one(
        'res.partner', 
        domain=[
            ('asociado', '=', True)
        ], 
        string='Asociado'
    )
    tarifa = fields.Float(
        string='Tarifa para este asociado', 
        required=True, 
        index=True
    )
    tarifac = fields.Float(
        string='Tarifa para cliente', 
        required=True, 
        index=True
    )
    detalles = fields.Text(string='Detalles')
    linea_id = fields.Many2one('trafitec.cotizaciones.linea')
    tiporemolque_id = fields.Many2one(
        string='Tipo remolque', 
        comodel_name='trafitec.moviles'
    )
    state = fields.Selection(
        string='Estado', 
        selection=[
            ('noautorizado', 'No autorizado'), 
            ('autorizado', 'Autorizado')
        ], 
        default='noautorizado', 
        help='Estado de la negociación.'
    )

    @api.constrains('tarifa')
    def _check_tarifa(self):
        if self.tarifa <= 0:
            raise UserError(
                ('Error !\nLa tarifa debe ser un valor mayor 0')
            )


    @api.model
    def create(self, vals):
        '''
        obj_nego = self.env['trafitec.cotizacion.linea.negociacion'].search(
            [
                ('asociado_id', '=', vals['asociado_id']),
                ('tiporemolque_id', '=', vals['tiporemolque_id']),
                ('linea_id', '=', vals['linea_id'])
            ]
        )

        if len(obj_nego) > 0:
            raise UserError(_('Error !\nNo se permite registrar 2 o mas negociaones a un mismo asociado y mismo tipo de remolque.'))
        '''

        return super(trafitec_cotizacion_line_negociacion, self).create(vals)

    
    def write(self, vals):
        '''
        if 'asociado_id' in vals:
            asociado_id = vals['asociado_id']
            if asociado_id != self.asociado_id.id:
                obj_nego = self.env['trafitec.cotizacion.linea.negociacion'].search(
                    [
                    ('asociado_id', '=', asociado_id),
                    ('tiporemolque_id', '=', vals['tiporemolque_id']),
                    ('linea_id', '=', self.linea_id.id)
                    ]
                )
                if len(obj_nego) > 0:
                    raise UserError(_('Error !\nNo se permite registrar 2 o mas negociaones a un asociado'))
        '''

        return super(trafitec_cotizacion_line_negociacion, self).write(vals)
