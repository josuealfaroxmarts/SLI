from odoo import models, fields


class TrafitecFactAutCargo(models.Model):
    _name = 'trafitec.fact.aut.cargo'
    _description ='factura aut cargo'

    name = fields.Many2one(
        'trafitec.tipocargosadicionales', 
        string='Producto', 
        required=True, 
        readonly=True
    )
    valor = fields.Float(
        string='Total', 
        required=True, 
        readonly=True
    )
    line_cargo_id = fields.Many2one(
        'trafitec.facturas.automaticas', 
        string='Id factura automatica'
    )
