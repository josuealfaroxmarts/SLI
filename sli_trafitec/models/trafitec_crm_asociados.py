# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime
from datetime import timedelta


class TrafitecCrmTraficoAsociados(models.Model):
    _name = 'trafitec.crm.asociados'
    _description ='crm asociados'
    _rec_name = 'id'

    buscar_nombre = fields.Char(string="Nombre", help='Nombre del asociado.')
    buscar_tiporemolque = fields.Many2one(string="Tipo remolque", comodel_name='trafitec.moviles', help='Tipo de remolque que tiene el asociado.')
    buscar_estado = fields.Many2one(string="Estado", comodel_name='res.country.state', help='Estado del país donde radica el asociado.')

    asociado_id = fields.Many2many(string='Asociados', comodel_name='res.partner', help='Asociados.')
    asociado_nombre = fields.Char(string='Asociado', related='asociado_id.name', help='Asociado.')
    cotizacion_id = fields.Many2one(string='Cotización', comodel_name='trafitec.cotizacion', help='Cotización.')
    linea_id = fields.Many2one(string='Origen destino', comodel_name='trafitec.cotizaciones.linea', help='Cotización.')
    tipo_recomendacion = fields.Selection(string='Tipo', selection=[('porviajes', 'Por viajes'), ('porusuario', 'Por usuario')], default='porusuario')

    @api.model
    def get_empty_list_help(self, help):
        help = "No se encontraron asociados recomendados por usuarios."
        return help

    
    def action_quitar_asociados(self):
        #Limpia la lista.
        self.asociado_id = None

    
    def action_buscar_asociados(self):
        self.asociado_id = None
        lista = []
        filtro = []

        #Solo asociados.
        filtro.append(('asociado', '=', True))
        if self.buscar_nombre:
            filtro.append(('name', 'ilike', '%'+str(self.buscar_nombre or '')+'%'))

        if self.buscar_tiporemolque:
            filtro.append(('trafitec_unidades_id.movil', '=', self.buscar_tiporemolque.id))

        if self.buscar_estado:
            filtro.append(('state_id', '=', self.buscar_estado.id))

        asociados = self.env['res.partner'].search(filtro, limit=100)
        #_logger.info(str(asociados))
        for a in asociados:
            lista.append(a.id)
        self.asociado_id = None
        self.asociado_id = lista
        #return {}

    def action_recomendar(self, cotizacion_id, linea_id):
        view_id = self.env.ref('sli_trafitec.trafitec_crm_recomendar_form').id
        return {'name': 'Recomendar asociados',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'trafitec.crm.asociados',
                'views': [(view_id, 'form')],
                # 'form_view_ref': 'base.res_partner_kanban_view',
                # 'tree_view_ref': 'trafitec_crm_trafico_asociados_kanban',
                # 'kanban_view_ref': 'trafitec_crm_trafico_asociados_kanban',
                # 'tree_view_ref':'',
                'view_id': view_id,  # 'view_ref': 'trafitec_crm_trafico_asociados_kanban',
                'target': 'current',  #current, new, main 'res_id': self.ids[0],
                'context': {
                    'default_cotizacion_id': cotizacion_id,
                    'default_linea_id': linea_id
                }
        }

    
    def action_crear(self, vals):
        return super(trafitec_crm_trafico_asociados, self).create(vals)

    
    def action_cerrar(self):
        return {}