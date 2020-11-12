# -*- encoding: utf-8 -*-
from openerp import api, fields, models, _, tools
import time
from datetime import datetime, date

# Agregamos manejar una secuencia por cada tienda para controlar viajes 
class stock_move(models.Model):
    _inherit = "stock.move"
    
    #mro_order_task_product_id   = fields.Many2one('fleet.mro.order.task.product', string='Product Line', readonly=True, copy=False)
    mro_order_id                = fields.Many2one('fleet.mro.order',string='MRO Service Order')
    mro_order_state             = fields.Selection([('cancel','Cancelled'), 
                                                     ('draft','Draft'), 
                                                     ('open','Open'), 
                                                     ('released','Released'), 
                                                     ('done','Done')],
                                                   related='mro_order_id.state',string='MRO Order State',store=True,readonly=True)
    vehicle_id                  = fields.Many2one('fleet.vehicle', related='mro_order_id.vehicle_id',string='Vehicle',store=True,readonly=True)
    mro_task_id                 = fields.Many2one('fleet.mro.order.task', string='Task')
    mro_task_spare_id           = fields.Many2one('fleet.mro.order.task.spares_quotation', string='Task Spare Line')


    @api.multi
    def action_done(self):
        res = super(stock_move, self).action_done()
        mro_order_quot_obj = self.env['fleet.mro.order.task.spares_quotation']
        for mv in self.filtered(lambda move: move.state == 'done' and move.mro_order_id):
            # Recorrer las lineas cotizadas, si la tarea corresponde actualizar cantidad, si no corresponde agregarla.
            resx = mro_order_quot_obj.search([('order_id','=',mv.mro_order_id.id),
                                             ('task_id','=',mv.mro_task_id.id),
                                             ('product_id','=',mv.product_id.id)])
            if resx:
                resx.update({'qty_to_invoice' : resx.qty_to_invoice + ((mv.location_dest_id.usage in ('inventory','production','customer') and 1.0 or -1.0) * mv.product_qty)})
                mv.write({'mro_task_spare_id':resx.id})
            else:
                values = {'order_id'     : mv.mro_order_id.id,
                          'task_id'      : mv.mro_task_id.id,
                          'product_id'   : mv.product_id.id,
                          'product_uom'  : mv.product_uom.id,
                          'product_uom_qty' : 0.0,
                          'quoted'       : False,
                          'qty_to_invoice' : mv.product_qty,
                         }
                line = mro_order_quot_obj.new(values)                
                line.on_change_product_id()
                print "line: ", line
                for field in ['name','price_unit','tax_id']:
                    if field not in values:
                        values[field] = line._fields[field].convert_to_write(line[field], line)
                print "values: ", values
                line = mro_order_quot_obj.create(values)
                mv.write({'mro_task_spare_id':line.id})
        return res
    

    
    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        res = super(stock_move, self)._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
        print "self.mro_order_id: ", self.mro_order_id and self.mro_order_id.name or 'Sin Orden de Mantenimiento'
        if self.mro_order_id:
            print "self.mro_order_id.driver_id: ", self.mro_order_id.driver_id and self.mro_order_id.driver_id.name or 'Sin Driver'
            res[0][2].update({'vehicle_id': self.vehicle_id.id, 'operating_unit_id': self.mro_order_id.operating_unit_id.id, 'employee_id': self.mro_order_id.vehicle_id.employee_id.id if self.mro_order_id.vehicle_id.employee_id else False })
            res[1][2].update({'vehicle_id': self.vehicle_id.id, 'operating_unit_id': self.mro_order_id.operating_unit_id.id, 'employee_id': self.mro_order_id.vehicle_id.employee_id.id if self.mro_order_id.vehicle_id.employee_id else False })
        print "res: ", res
        return res        


class fleet_vehicle(models.Model):
    _inherit = 'fleet.vehicle'

    employee_id     = fields.Many2one('hr.employee', string='Driver', required=False, domain=[('tms_category', '=', 'driver')], help="This is used in TMS Module...")
