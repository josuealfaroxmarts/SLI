from odoo import fields, models


class SliPortalesRegistro(models.Model):
    _name = 'sli.portales.registro'
    _description = 'Registro'

    usuario_id = fields.Many2one(
        string='Usuario', 
        comodel_name='sli.portales.usuarios'
    )
    detalles = fields.Char(string='Detalles')
