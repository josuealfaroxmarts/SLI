
from odoo import fields, models


class TrafitecUbicacion(models.Model):
    _inherit = "trafitec.ubicacion"
    
    id_fletex = fields.Integer()

    