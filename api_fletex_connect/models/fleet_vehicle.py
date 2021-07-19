# -*- coding: utf-8 -*-
from requests.sessions import default_headers
from openerp import models, fields, api, _
from openerp.exceptions import UserError

class FletexFleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    id_fletex_truck = fields.Integer()
    id_fletex_trailer = fields.Integer()
    send_to_api = fields.Boolean(default=False)
    status_vehicle = fields.Selection([('approved', 'Aprobado'), 
                                        ('rejected', 'Rechazado'), 
                                        ('onhold', 'En Espera')], 
                                        string='Status', 
                                        default='onhold')
    """ poliza_approved = fields.boolean(string="Poliza aprobada",default=False)
    circulacion_approved = fields.boolean(string="Tarjeta de circulacion aprobado",default=False) """

    @api.onchange('status_vehicle')
    def _change_send_to_api(self):
        self.send_to_api = True

