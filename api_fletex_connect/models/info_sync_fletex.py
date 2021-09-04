from odoo import fields, models


class InfoSyncFletex(models.Model):
    _name = "info.sync.fletex"

    date = fields.Date(string="Fecha")
    record_type = fields.Char(String="Tipo de registro")
    result = fields.Char(string="Resultado")
    description = fields.Text(string="Descripción")   