# -*- coding: utf-8 -*-
from requests.sessions import default_headers
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

class FletexTrafitecCotizacion(models.Model):
    _inherit = 'trafitec.cotizacion'
    id_fletex = fields.Integer()
    send_to_api = fields.Boolean()

    
    def action_available(self):
        logging.debug('AY PAPA FUNCIONO :v !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        if self.state == "Enviada" :
            self.send_to_api = True
        super(FletexTrafitecCotizacion, self).action_available()
