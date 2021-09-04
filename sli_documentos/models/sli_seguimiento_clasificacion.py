from odoo import fields, models


class SliSeguimientoClasificacion(models.Model):
    _name = 'sli.seguimiento.clasificacion'
    _description ='clasificacion seguimiento'
    
    name = fields.Char(
        string='Nombre', 
        help='Nombre de la clasificación.'
    )
    aplica = fields.Selection(
        string='Aplica a', 
        selection=[
            ('viaje', 'Viaje'), 
            ('contrarecibo', 'Contra recibo'), 
            ('factura', 'Factura')], 
        default='viaje', 
        help='Indica para que asignación aplica.'
    )
