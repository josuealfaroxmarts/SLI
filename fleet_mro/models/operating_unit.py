# -*- encoding: utf-8 -*-
##############################################################################

from openerp import api, fields, models, _

# Agregamos manejar una secuencia por cada tienda para controlar viajes 
class operating_unit(models.Model):
    _inherit = "operating.unit"
    
    fleet_mro_service_order_seq = fields.Many2one('ir.sequence', string='Maintenance Order Sequence')
    fleet_mro_driver_report_seq = fields.Many2one('ir.sequence', string='Driver Report of Failure Sequence')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
