from odoo import fields, models


class TrafitecViajes(models.Model):
    _inherit = "trafitec.viajes"
    
    id_fletex = fields.Integer()