from odoo import models, fields, api, exceptions, tools

from datetime import datetime, date, time, timedelta
import tempfile
import base64
import os

import random

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError, RedirectWarning

import ast
import re
from datetime import datetime, date


class SliSeguimientoRegistro(models.Model):
    _name = 'sli.seguimiento.registro'
    _description ='registro seguimiento'
    _order = 'id desc'
    
    @api.depends('para_usuario_id', 'viaje_id', 'contrarecibo_id', 'factura_id')
    def compute_nombre(self):
        self.name = (self.para_usuario_id.login or '') + '-' + (self.viaje_id.name or self.contrarecibo_id.name or self.factura_id.name or self.factura_id.number or '')
    
    _rec_name = 'id'
    para_usuario_id = fields.Many2one(
        string='Para', 
        comodel_name='res.users', 
        required=True, 
        help='Usuario al que se asigna el documento.'
    )
    viaje_id = fields.Many2one(
        string='Viaje', 
        comodel_name='trafitec.viajes', 
        help='Viaje relacionado.'
    )
    contrarecibo_id = fields.Many2one(
        string='Contra recibo', 
        comodel_name='trafitec.contrarecibo', 
        help='Contra recibo relacionado.'
    )
    factura_id = fields.Many2one(
        string='Factura', 
        comodel_name='account.move', 
        help='Factura relacionada.'
    )
    tipo = fields.Selection(
        string='Tipo', 
        selection=[
            ('viaje', 'Viaje'), 
            ('contrarecibo', 'Contra recibo'), 
            ('factura', 'Factura')], 
        default='viaje', 
        required=True
    )
    clasificacion_id = fields.Many2one(
        string='Clasificación', 
        comodel_name='sli.seguimiento.clasificacion', 
        help='Clasificación.'
    )
    detalles = fields.Text(
        string='Detalles', 
        default='', 
        help='Detalles generales'
    )
    fechahora_ar = fields.Datetime(
        string='Fecha y hora', 
        help='Fecha y hora de aceptación o rechazo de la asignación.'
    )
    state = fields.Selection(
        string='Estado', 
        selection=[
            ('enespera', 'En espera'), 
            ('aceptado', 'Aceptado'), 
            ('rechazado', 'Rechazado'), 
            ('descartado', 'Descartado')], 
        default='enespera', 
        help='Estado de la asignación'
    )
    
    def action_asignar(self):
        #sli_seguimeinto_asignar_viaje_form
        view_id = self.env.ref('sli_documentos.sli_seguimeinto_asignar_viaje_form').id
        return {
            'name': _('Asignar'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sli.seguimiento.asignar',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'context': {}
        }
    
    
    def action_aceptar(self):
        if self.para_usuario_id.id != self.env.user.id:
            raise UserError(_("Para poder aceptar la asignación debe ser el usuario al que se asigno."))
        self.write({'fechahora_ar': datetime.now(), 'state': 'aceptado'})
        
        if self.tipo == 'viaje':
            self.viaje_id.with_context(
                validar_credito_cliente=False, 
                validar_cliente_moroso=False).sudo().write({
                    'asignadoa_id': self.para_usuario_id.id,
                    'asignadoi_id': False
                })

        if self.tipo == 'contrarecibo':
            self.contrarecibo_id.with_context(
                validar_credito_cliente=False, 
                validar_cliente_moroso=False).sudo().write({
                    'asignadoa_id': self.para_usuario_id.id,
                    'asignadoi_id': False
                })

        if self.tipo == 'factura':
            self.factura_id.with_context(
                validar_credito_cliente=False, 
                validar_cliente_moroso=False).sudo().write({
                    'asignadoa_id': self.para_usuario_id.id,
                    'asignadoi_id': False
                })

    
    def action_rechazar(self):
        if self.para_usuario_id.id != self.env.user.id:
            raise UserError(_("Para poder rechazar la asignación debe ser el usuario al que se asigno."))
            
        self.write({'fechahora_ar': datetime.now(), 'state': 'rechazado'})
    
        if self.tipo == 'viaje':
            self.viaje_id.with_context(
                validar_credito_cliente=False, 
                validar_cliente_moroso=False).sudo().write({
                    'asignadoi_id': False,
                    'asignacion_id': False
                })
    
        if self.tipo == 'contrarecibo':
            self.contrarecibo_id.with_context(
                validar_credito_cliente=False, 
                validar_cliente_moroso=False).sudo().write({
                    'asignadoi_id': False,
                    'asignacion_id': False
                })

    
        if self.tipo == 'factura':
            self.factura_id.asignadoi_id = False
            self.factura_id.asignacion_id = False
            self.factura_id.with_context(
                validar_credito_cliente=False, 
                validar_cliente_moroso=False).sudo().write({
                    'asignadoi_id': False,
                    'asignacion_id': False
                })