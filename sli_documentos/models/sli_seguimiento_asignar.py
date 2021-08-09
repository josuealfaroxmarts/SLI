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

class SliSeguimientoAsignar(models.TransientModel):
    _name = 'sli.seguimiento.asignar'
    _description ='Asignar seguimiento'

    para_usuario_id = fields.Many2one(
        string='Para', 
        comodel_name='res.users', 
        required=True, 
        help='Usuario al que se asigna el documento.'
    )
    viaje_id = fields.Many2one(
        string='Viaje', 
        comodel_name='trafitec.viajes', 
        help='Usuario al que se asigna el documento.'
    )
    contrarecibo_id = fields.Many2one(
        string='Contra recibo', 
        comodel_name='trafitec.contrarecibo', 
        help='Contrarecibo relacionado.'
    )
    factura_id = fields.Many2one(
        string='Factura', 
        comodel_name='account.move', 
        help='Factura relacionada.'
    )
    clasificacion_id = fields.Many2one(
        string='Motivo', 
        comodel_name='sli.seguimiento.clasificacion', 
        required=True, 
        help='Clasificación.'
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
    detalles = fields.Text(
        string='Detalles', 
        default='', 
        help='Detalles generales'
    )
    state = fields.Selection(
        string='Estado', 
        selection=[
            ('enespera', 'En espera'), 
            ('aceptado', 'Aceptado'), 
            ('rechazado', 'Rechazado')], 
        default='enespera', 
        help='Estado de la asignación'
    )

    def enviar_correo(self, asunto='', contenido='', para='', para2=''):
        valores = {
            'subject': asunto,
            'body_html': contenido,
            'email_to': para,
            'email_cc': para2,
            'email_from': 'info@sli.mx',
        }
        nuevo = self.env['mail.mail'].create(valores)

    def action_asignar(self):
        correo_titulo = 'Intento de asignación de documento'
        correo_mensaje = ''
        
        viajes_obj = self.env['trafitec.viajes']
        contrarecibos_obj = self.env['trafitec.contrarecibo']
        facturas_obj = self.env['account.move']
        
        registro_obj = self.env['sli.seguimiento.registro']
        
        nuevo = {
            'para_usuario_id': self.para_usuario_id.id,
            'viaje_id': (self.viaje_id.id or False),
            'contrarecibo_id': (self.contrarecibo_id.id or False),
            'factura_id': (self.factura_id.id or False),
            'clasificacion_id': self.clasificacion_id.id,
            'detalles': self.detalles,
            'tipo': self.tipo,
            'state': 'enespera'
        }
        nuevo = registro_obj.create(nuevo)
    
        if self.tipo == 'viaje':
            viaje_dat = viajes_obj.search([('id', '=', self.viaje_id.id)])    
            self.viaje_id.with_context(
                validar_credito_cliente=False, 
                validar_cliente_moroso=False).write({
                    'asignadoi_id': self.para_usuario_id.id, 
                    'asignacion_id': nuevo.id
                })
            correo_titulo += ' (Viaje {})'.format((viaje_dat.name or ''))
            correo_mensaje = 'Se le ha intentado asignar el viaje con folio: {} por el motivo: {} Detalles: {}.'.format((viaje_dat.name or ''), self.clasificacion_id.name, self.detalles)

        if self.tipo == 'contrarecibo':
            contrarecibos_dat = contrarecibos_obj.search([
                ('id', '=', self.contrarecibo_id.id)
            ])
            self.contrarecibo_id.with_context(
                validar_credito_cliente=False, 
                validar_cliente_moroso=False).write({
                    'asignadoi_id': self.para_usuario_id.id, 
                    'asignacion_id': nuevo.id
                })

            correo_titulo += ' (Contra recibo {})'.format((contrarecibos_dat.name or ''))
            correo_mensaje = 'Se le ha intentado asignar el contra recibo con folio: {} por el motivo: {} Detalles: {}.'.format((contrarecibos_dat.name or ''), self.clasificacion_id.name, self.detalles)

        if self.tipo == 'factura':
            facturas_dat = facturas_obj.search([('id', '=', self.factura_id.id)])
            self.factura_id.with_context(
                validar_credito_cliente=False, 
                validar_cliente_moroso=False).write({
                    'asignadoi_id': self.para_usuario_id.id, 
                    'asignacion_id': nuevo.id
                })
            correo_titulo += ' (Factura {})'.format((facturas_dat.number or facturas_dat.name or ''))
            correo_mensaje = 'Se le ha intentado asignar la factura con folio: {} por el motivo: {} Detalles: {}.'.format((facturas_dat.number or facturas_dat.name or ''), self.clasificacion_id.name, self.detalles)
        
        
        #Notificar.
        self.enviar_correo(
            asunto=correo_titulo, 
            contenido=correo_mensaje, 
            para=self.para_usuario_id.login
        )
        