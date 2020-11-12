# -*- encoding: utf-8 -*-
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_is_zero, float_compare

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    
    @api.depends('order_line.price_subtotal')
    def _get_mro_cost(self):
        for order in self:
            amount_spare_parts, amount_manpower = 0.0, 0.0
            if order.state in ('purchase','done'):
                for line in order.order_line:
                    if line.product_id.type=='service':
                        amount_manpower += line.price_subtotal
                    else:
                        amount_spare_parts += line.price_subtotal
            order.update({
                'mro_spare_parts': amount_spare_parts,
                'mro_manpower': amount_manpower,
            })
    
    fleet_mro_related = fields.Boolean(string="Linked to Fleet MRO Service Order", default=False,
                        states={'purchase': [('readonly', True)],'done': [('readonly', True)],'cancel': [('readonly', True)],})
    mro_spare_parts = fields.Monetary(compute='_get_mro_cost', string='Spare Parts', readonly=1)
    mro_manpower    = fields.Monetary(compute='_get_mro_cost', string='ManPower', readonly=1)
    
    #mro_task_id     = fields.Many2one('fleet.mro.order.task', string='MRO Task', domain=[('state', '=', 'process')],
    #                    states={'purchase': [('readonly', True)],'done': [('readonly', True)],'cancel': [('readonly', True)],})
    mro_order_id    = fields.Many2one('fleet.mro.order', string='MRO Service Order', domain=[('state','in', ('open','released'))],
                        states={'purchase': [('readonly', True)],'done': [('readonly', True)],'cancel': [('readonly', True)],})
    vehicle_id      = fields.Many2one('fleet.vehicle', string='Vehicle', related="mro_order_id.vehicle_id",
                                      store=True, readonly=True)


    @api.multi
    def button_cancel(self):
        if any((order.state in ('purchase','done') and order.fleet_mro_related and \
                order.mro_order_id.state in ('cancel','done') ) for order in self):
            raise UserError(_('Warning!\nYou can not cancel Purchase Order for External Workshop because MRO Service Order is Done or Task is in Done State'))
        return super(PurchaseOrder,self).button_cancel()

class PurchaseOrderLine(models.Model):
    _inherit='purchase.order.line'

    mro_task_id       = fields.Many2one('fleet.mro.order.task', string='MRO Task', 
                                             store=True, readonly=False)
    mro_order_id      = fields.Many2one('fleet.mro.order', string='MRO Service Order', #related="mro_task_id.order_id", 
                                              store=True, readonly=False)

    vehicle_id      = fields.Many2one('fleet.vehicle', string='Vehicle', related="mro_order_id.vehicle_id",
                                      store=True, readonly=True)

    @api.multi
    def _create_stock_moves(self, picking):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            if line.product_id.type not in ['product', 'consu']:
                continue
            qty = 0.0
            price_unit = line._get_stock_move_price_unit()
            for move in line.move_ids.filtered(lambda x: x.state != 'cancel'):
                qty += move.product_qty
            template = {
                'name': line.name or '',
                'product_id': line.product_id.id,
                'product_uom': line.product_uom.id,
                'date': line.order_id.date_order,
                'date_expected': line.date_planned,
                'location_id': line.order_id.partner_id.property_stock_supplier.id,
                'location_dest_id': line.order_id._get_destination_location(),
                'picking_id': picking.id,
                'partner_id': line.order_id.dest_address_id.id,
                'move_dest_id': False,
                'state': 'draft',
                'purchase_line_id': line.id,
                'company_id': line.order_id.company_id.id,
                'price_unit': price_unit,
                'picking_type_id': line.order_id.picking_type_id.id,
                'group_id': line.order_id.group_id.id,
                'procurement_id': False,
                'origin': line.order_id.name,
                'route_ids': line.order_id.picking_type_id.warehouse_id and [(6, 0, [x.id for x in line.order_id.picking_type_id.warehouse_id.route_ids])] or [],
                'warehouse_id':line.order_id.picking_type_id.warehouse_id.id,
            }
            if line.mro_task_id:
                template.update({'mro_task_id':line.mro_task_id.id})
            # Fullfill all related procurements with this po line
            diff_quantity = line.product_qty - qty
            for procurement in line.procurement_ids:
                # If the procurement has some moves already, we should deduct their quantity
                sum_existing_moves = sum(x.product_qty for x in procurement.move_ids if x.state != 'cancel')
                existing_proc_qty = procurement.product_id.uom_id._compute_quantity(sum_existing_moves, procurement.product_uom)
                procurement_qty = procurement.product_uom._compute_quantity(procurement.product_qty, line.product_uom) - existing_proc_qty
                if float_compare(procurement_qty, 0.0, precision_rounding=procurement.product_uom.rounding) > 0 and float_compare(diff_quantity, 0.0, precision_rounding=line.product_uom.rounding) > 0:
                    tmp = template.copy()
                    tmp.update({
                        'product_uom_qty': min(procurement_qty, diff_quantity),
                        'move_dest_id': procurement.move_dest_id.id,  #move destination is same as procurement destination
                        'procurement_id': procurement.id,
                        'propagate': procurement.rule_id.propagate,
                    })
                    done += moves.create(tmp)
                    diff_quantity -= min(procurement_qty, diff_quantity)
            if float_compare(diff_quantity, 0.0, precision_rounding=line.product_uom.rounding) > 0:
                template['product_uom_qty'] = diff_quantity
                done += moves.create(template)
        return done


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
