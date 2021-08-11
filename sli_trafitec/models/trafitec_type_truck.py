# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools,_
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import datetime


class TrafitecTypeTruck(models.Model):
    _name = 'trafitec.type_truck'
    _description='type truck'

    tipo_camion = fields.Many2one(
        'trafitec.cotizacion', 
        string='Tipo camion'
    )
    type_truck = fields.Selection(
        [
            ('Jaula', 'Jaula'), 
            ('Caja seca', 'Caja seca'), 
            ('Portacontenedor', 'Portacontenedor'), 
            ('Tolva', 'Tolva'), 
            ('Plataforma', 'Plataforma'), 
            ('Gondola', 'Gondola'), 
            ('Torton', 'Torton'), 
            ('Rabon', 'Rabon'), 
            ('Chasis', 'Chasis'), 
            ('Thermo 48', 'Thermo 48'), 
            ('Thermo 53', 'Thermo 53')
        ], 
        string='Tipo Camion'
    )

# TODO HABLAR CON EL CONSULTOR LINEA 753
''' class trafitec_localidad_municipios_estado_pais(models.Model):
    _inherit = 'res.colonia.zip.sat.code'

    
    @api.depends('name')
    def name_get(self):
        result = []
        name = ''
        for rec in self:
            if rec.name:
                name = '[' + (rec.zip_sat_code.code or '') + '] ' + (rec.name  or '') + '/' + (rec.zip_sat_code.township_sat_code.name or '') + '/' + (rec.zip_sat_code.township_sat_code.state_sat_code.name or '') + '/' + (rec.zip_sat_code.township_sat_code.state_sat_code.country_sat_code.name or '')
                result.append((rec.id, name))
            else:
                result.append((rec.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=10):
        args = args or []
        domain = []
        if not (name == '' and operator == 'ilike'):
            args += ['|', '|', '|', ('name', 'ilike', name), ('zip_sat_code.township_sat_code.name', 'ilike', name),
                    ('zip_sat_code.township_sat_code.state_sat_code.name', 'ilike', name),
                    ('zip_sat_code.township_sat_code.state_sat_code.country_sat_code.name', 'ilike', name)]
        result = self.search(domain + args, limit=limit)
        res = result.name_get()
        return res '''


''' class trafitec_municipios_estado_pais(models.Model):
    _inherit = 'res.country.township.sat.code'

    
    @api.depends('name')
    def name_get(self):
        result = []
        name=''
        for rec in self:
            if rec.name:
                name = (rec.name or '') + '/' + (rec.state_sat_code.name or '') + '/' + (rec.state_sat_code.country_sat_code.name or '')
                result.append((rec.id, name))
            else:
                result.append((rec.id, name))
        return result
 '''
 