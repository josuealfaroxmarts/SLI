## -*- coding: utf-8 -*-
from openerp import models, fields, api, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError
import logging
_logger = logging.getLogger(__name__)


class trafitec_cargosx(models.Model):
    _name = 'trafitec.cargosx'

    @api.one
    @api.depends('total','abonos','saldo')
    def _compute_total_abonos(self):
        obj=self.env['trafitec.cargosx.abonos'].search([('cargosx_id','=',self.id)])
        suma = 0

        if obj:
          for a in obj:
            suma+=a.abono

        self.abonos=suma
        self.saldo=self.total-self.abonos

    total=fields.Float(string='Total',default=0,required=True,help='Total del cargo.')
    abonos=fields.Float(string='Abonos',default=0,required=True,compute='_compute_total_abonos',help='Total de abonos.',store=True)
    saldo=fields.Float(string='Saldo',default=0,required=True,compute='_compute_total_abonos',help='Saldo del cargo.',store=True)

    tipo=fields.Selection(selection=[('noespecificado','No especificado'),('merma','Merma'),('comision','Comisión'),('descuento','Descuento')],default='noespecificado')

    viaje_id=fields.Many2one(comodel_name='trafitec.viajes',string='Viaje',help='Viaje relacionado con el cargo.')
    asociado_id=fields.Many2one(comodel_name='res.partner',string='Asosciado',help='Asociado relacionado con el cargo.')
    proveedor_id=fields.Many2one(comodel_name='res.partner',string='Proveedor',help='Proveedor relacionadao con el cargo.')
    observaciones=fields.Text(string='Observaciones',default="",help='Observaciones del cargo')
    state=fields.Selection(selection=[('activo','Activo'),('cancelado','Cancelado')], default='activo')

class trafitec_cargosx_abonos(models.Model):
    _name='trafitec.cargosx.abonos'
    cargosx_id=fields.Many2one(comodel_name='trafitec.cargosx',string='Cargo',required=True)
    abono=fields.Float(string='Abono',default=0,required=True)
    generadoen=fields.Selection(string="Generado en",selection=[('sistema','Sistema'),('manual','Manual'),('contrarecibo','Contra recibo'),('factura','Factura')],default='sistema')
    observaciones=fields.Text(string='Observaciones',default='',required=True,help='Observaciones del abono.')

