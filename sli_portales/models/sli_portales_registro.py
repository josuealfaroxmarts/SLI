from odoo import models, fields, api, exceptions, tools

class usuarios_log(models.Model):
    _name = 'sli.portales.registro'
    _description ='Registro'

    usuario_id = fields.Many2one(
        string='Usuario', 
        comodel_name='sli.portales.usuarios'
    )
    detalles = fields.Char(
        string='Detalles',
        default=''
    )
