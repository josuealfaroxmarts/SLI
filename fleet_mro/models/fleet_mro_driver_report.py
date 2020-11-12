# -*- encoding: utf-8 -*-
from openerp import api, fields, models, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time
from datetime import datetime, date


class fleet_mro_driver_report(models.Model):
    _name ='fleet.mro.driver_report'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Driver Report of Vehicle Failure'

    @api.multi
    @api.depends('order_id.state')
    def _solved(self):
        for record in self:
            record.solved = bool(record.order_id and record.order_id.state in ('released','done'))


    
    name          = fields.Char(string='Report', size=64, required=False, index=True)
    state         = fields.Selection([('draft','Draft'), 
                                      ('confirmed','Confirmed'), 
                                      ('closed','Closed'), 
                                      ('cancel','Cancelled')], 
                                     index=True, track_visibility='onchange', default='draft',
                                     string='State', readonly=True)
    date          = fields.Date(string='Date', default=fields.Date.context_today, track_visibility='onchange',
                                states={'cancel':[('readonly',True)], 'confirmed':[('readonly',True)],'closed':[('readonly',True)]}, required=True)
    operating_unit_id     = fields.Many2one('operating.unit', string='Maintenance Workshop', track_visibility='onchange',
                                    states={'cancel':[('readonly',True)], 'confirmed':[('readonly',True)],'closed':[('readonly',True)]}, required=True)
    vehicle_id    = fields.Many2one('fleet.vehicle', string='Vehicle', help='Tractor, Trailer, Camion, Van, Cargo Unit, etc...',
                                    index=True, track_visibility='onchange',
                                    # states={'cancel':[('readonly',True)], 'confirmed':[('readonly',True)],'closed':[('readonly',True)]}, 
                                    # required=True
                                    )
    employee_id   = fields.Many2one('res.partner', string='Driver', track_visibility='onchange',
                                    states={'cancel':[('readonly',True)], 'confirmed':[('readonly',True)],'closed':[('readonly',True)]}, required=True)
    notes         = fields.Text(string='Notes', copy=False,
                                states={'cancel':[('readonly',True)], 'confirmed':[('readonly',True)],'closed':[('readonly',True)]}, required=True)
    order_id  = fields.Many2one('fleet.mro.order', string='MRO Service Order', track_visibility='onchange',
                                    ondelete='restrict', required=False, readonly=True, states={'cancel':[('readonly',True)], 'confirmed':[('readonly',True)], 'closed':[('readonly',True)]})
    date_end_real = fields.Datetime(related='order_id.date_end_real', string='Date Solved', readonly=True)

    solved        = fields.Boolean(compute='_solved', string='Solved', track_visibility='onchange', store=True)
    
    
    _sql_constraints = [('name_uniq', 'unique(name, operating_unit_id)', 'Driver Report number must be unique per Operating Unit !'),
                       ]
    _order = "name desc, date desc"


    @api.model
    def create(self, vals):
        operating_unit = self.env['operating.unit'].browse([vals['operating_unit_id']])
        if operating_unit.fleet_mro_driver_report_seq:
            vals['name'] = operating_unit.fleet_mro_driver_report_seq.next_by_id()
        else:
            raise UserError(_('Driver Failure Report Error !'), _('You have not defined Driver Failure Report Sequence for Operating Unit ' + operating_unit.name))
        return super(fleet_mro_driver_report, self).create(vals)

    @api.multi
    def action_cancel_draft(self):
        self.write({'state':'draft'})
        return True
    
    @api.multi
    def action_cancel(self):
        for record in self:
            if record.state != 'closed' and record.order_id.id:
                raise UserError( _('Warning !!!\nCould not cancel Report ! This Driver Report of Vehicle''s Failure is already linked to MRO Service Order'))
        self.write({'state':'cancel'})
        return True

    @api.multi
    def action_confirm(self):
        self.write({'state':'confirmed'})
        return True


class fleet_mro_order(models.Model):
    _inherit="fleet.mro.order"    

    @api.multi
    def write(self, vals):
        if 'fleet_mro_driver_report_ids' in vals or ('state' in vals and vals['state']=='done'):
            report_ids = self.env['fleet.mro.driver_report'].search([('order_id','in',tuple(self._ids,))])
            report_ids.write({'order_id':False, 'state': 'confirmed'})
        res = super(fleet_mro_order, self).write(vals)
        if 'state' in vals and vals['state']=='done':
            for order in self:
                order.fleet_mro_driver_report_ids.write({'order_id':order.id, 'state': 'closed'}) # 'order_id':order.id,
        return res                

    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

