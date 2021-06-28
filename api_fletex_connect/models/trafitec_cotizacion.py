# -*- coding: utf-8 -*-
from requests.sessions import default_headers
from openerp import models, fields, api, _
from openerp.exceptions import UserError
import logging

class FletexTrafitecCotizacion(models.Model):
    _inherit = 'trafitec.cotizacion'

    id_fletex = fields.Integer()
    send_to_api = fields.Boolean()

    @api.multi
    def action_available(self):
        logging.debug('AY PAPA FUNCIONO :v !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        if self.state == "Enviada" :
            self.send_to_api = True
        super(FletexTrafitecCotizacion, self).action_available()
