# -*- encoding: utf-8 -*-

from openerp import api, fields, models, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError

## Heredamos el objeto stock_picking
class stock_picking(models.Model):
    _inherit = "stock.picking"
    
    mro_order_id   = fields.Many2one('fleet.mro.order', 'MRO Service Order')
    mro_order_state= fields.Selection([('cancel','Cancelled'), 
                                             ('draft','Draft'),
                                             ('scheduled','Scheduled'),
                                             ('check_in','Check In'),
                                             ('revision','Revision'),
                                             ('waiting_approval','Waiting Approval'),
                                             ('open','Open'), 
                                             ('released','Released'),
                                             ('done','Done')], related='mro_order_id.state', store=True, readonly=True)
    vehicle_id     = fields.Many2one(related='mro_order_id.vehicle_id',type='many2one',relation='fleet.vehicle',string='Vehicle',store=True,readonly=True)
    for_fleet_mro_order = fields.Boolean('For MRO Service Order')
    mechanic_id    = fields.Many2one('hr.employee', 'Supervisor', readonly=False, domain=[('fleet_mro_mechanic', '=', True)])


    @api.onchange('mro_order_id')
    def on_change_fleet_mro_order(self):
        if self.mro_order_id:
            self.picking_type_id = self.mro_order_id.mro_type_id.stock_picking_type.id

stock_picking()


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'
    
    
    @api.multi
    def create_returns(self):
        picking = self.env['stock.picking'].browse(self.env.context['active_id'])
        if picking.mro_order_id and picking.mro_order_id.state in ('done'):
            raise UserError(_('Warning !!!\nYou canno create Return Picking if the MRO Service Order related to this Picking is in Done State.\nIf you need to return this Producto you have to create it manually.'))

        return super(ReturnPicking, self).create_returns()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
