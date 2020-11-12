# -*- encoding: utf-8 -*-
from openerp import api, fields, models, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError
import openerp.addons.decimal_precision as dp
from datetime import datetime
from pytz import timezone
import pytz
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time

class fleet_mro_order_task_time(models.Model):
    _name = 'fleet.mro.order.task.time'
    _description = 'Fleet MRO Service Order Task Control Time'
    _rec_name='task_id'

    
    @api.one
    @api.depends('task_time_time_ids.duration')
    def _get_hours_duration(self):
        sum_productive, sum_no_productive = 0.0, 0.0        
        for xtime in self.task_time_time_ids.filtered(lambda r: r.complete):            
            sum_productive += xtime.productivity_type == 'busy' and xtime.duration or 0.0
            sum_no_productive += xtime.productivity_type == 'not_busy' and xtime.duration or 0.0
        self.hours_mechanic = sum_productive
        self.amount = sum_productive * self.price_unit
        self.total_duration = sum_productive + sum_no_productive


    state           = fields.Selection([('draft','Pending'), 
                                        ('process','Working on it'), 
                                        ('pause','Paused'), 
                                        ('done','Done'), 
                                        ('cancel','Cancel')], string='State', default='draft')

    task_time_time_ids    = fields.One2many('hr.employee.mro_productive','control_time_id', readonly=True)

    #uid = fields.Char(string='User', readonly=True)

    date_start      = fields.Datetime(string='Start', readonly=True)
    date_end        = fields.Datetime(string='End', readonly=True)

    ######## Many2One ###########

    task_id         = fields.Many2one('fleet.mro.order.task', string='Task', readonly=True, ondelete='restrict')
    hr_employee_id  = fields.Many2one('hr.employee', string='Mechanic', ondelete='restrict')
    hr_employee_user_id = fields.Many2one('res.users', string='User',readonly=True, ondelete='restrict')
    price_unit      = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)
    ## Float
    hours_mechanic  = fields.Float(compute='_get_hours_duration', string='Hours Work', readonly=True, store=True)
    total_duration  = fields.Float(compute='_get_hours_duration', string='Total Duration', readonly=True, store=True)
    amount          = fields.Float(compute='_get_hours_duration', string='Amount', readonly=True, store=True)
    ######## Related ###########
    order_id        = fields.Many2one('fleet.mro.order', related='task_id.order_id', string='Order', readonly=True, store=True)
    date_order      = fields.Datetime(related='order_id.date', string='Date', readonly=True, store=True)
    operating_unit_id       = fields.Many2one('operating.unit', related='order_id.operating_unit_id', string='Operating Unit', store=True, readonly=True)
    vehicle_id      = fields.Many2one('fleet.vehicle', related='order_id.vehicle_id', string='Vehicle', store=True, readonly=True)

    _order = 'task_id'
########################### Metodos ####################################################################################


    @api.multi
    def create_time_rec(self):
        default_busy = self.env['hr.employee.mro_productive.type'].search([('default_for_busy','=',True)], limit=1)
        if not default_busy:
            raise UserError(_('Warning !!!\n\nCould not find any Task Productivity Type marked as Default for Busy'))
        time_obj = self.env['hr.employee.mro_productive']
        for rec in self:
            time_id  = time_obj.create({'control_time_id' : rec.id,
                                        'type'            : default_busy.id,
                                        'date_start'      : time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                        'order_id'        : rec.order_id.id,
                                        'task_id'         : rec.task_id.id,
                                        'employee_id'     : rec.hr_employee_id.id,
                                        'price_unit'      : rec.hr_employee_id.wage_per_hour,
                                        })
        return True


    @api.multi
    def action_start(self):
        self.ensure_one()
        self.write({'state'     :'process', 
                    'date_start':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'price_unit': self.hr_employee_id.wage_per_hour,})
        self.task_id.write({'date_start_real':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        return self.create_time_rec()


    @api.multi
    def action_done(self):
        self.ensure_one()
        self.write({'state':'done',
                    'date_end'  : time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'price_unit': self.hr_employee_id.wage_per_hour})
        self.task_time_time_ids.complete_time_rec()
        self.task_id.write({'date_end_real':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                            'date_most_recent_end_mechanic_task':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        self.task_id.set_task_as_done_if_posible()
        return True


    @api.multi
    def action_process(self):
        self.ensure_one()
        self.task_time_time_ids.complete_time_rec()
        self.write({'state':'process','price_unit' : self.hr_employee_id.wage_per_hour})
        return self.create_time_rec()


    @api.multi
    def action_cancel(self):
        self.write({'state':'cancel'})
        return True   



class hr_employee_mro_productive_wizard(models.TransientModel):
    _name = 'hr.employee.mro_productive.wizard'
    _description = 'Task Time Sheet Pauses'

    type            = fields.Many2one('hr.employee.mro_productive.type', string="Event Type", required=True)
    control_time_id = fields.Many2one('fleet.mro.order.task.time', string='Task TimeSheet', required=True)
    task_id         = fields.Many2one('fleet.mro.order.task', related="control_time_id.task_id", string='Task')
    order_id        = fields.Many2one('fleet.mro.order', related="task_id.order_id", string='MRO Service Order')
    note            = fields.Text(string="Notes")
    
    @api.multi
    def pause_task(self):
        rec_ids =  self._context.get('active_ids',[])
        time_obj = self.env['hr.employee.mro_productive']
        self.control_time_id.task_time_time_ids.complete_time_rec()
        time_id  = time_obj.create({'control_time_id' : self.control_time_id.id,
                                    'type'            : self.type.id,
                                    'date_start'      : time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                    'note'            : self.note,
                                    'order_id'        : self.order_id.id,
                                    'task_id'         : self.task_id.id,
                                    'employee_id'     : self.control_time_id.hr_employee_id.id,
                                    })
        self.control_time_id.write({'state':'pause'})
        return {'type': 'ir.actions.act_window_close'}




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
