from odoo import  fields, models, _


class TrafitecCotizacion(models.Model):
    _inherit = "trafitec.cotizacion"

    id_fletex = fields.Integer()
    send_to_api = fields.Boolean()

    def action_available(self):
        for cot in self:
            if cot.state == "Enviada":
                cot.send_to_api = True
        super(TrafitecCotizacion, self).action_available()
