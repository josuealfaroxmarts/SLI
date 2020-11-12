# -*- encoding: utf-8 -*-
from openerp import api, fields, models, _, tools
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
import time

class hr_employee_mro_productive(models.Model):
    _name = 'hr.employee.mro_productive'
    _description = 'Task Control Time'
    _rec_name='type'


    @api.multi
    @api.depends('date_start', 'date_end')
    def _get_event_duration(self):
        for rec in self:
            duration = 0.0
            if rec.date_start and rec.date_end:
                duration = datetime.strptime(rec.date_end, '%Y-%m-%d %H:%M:%S') - datetime.strptime(rec.date_start, '%Y-%m-%d %H:%M:%S')
                rec.complete = True
            rec.duration = ((duration.days * 24.0*60.0*60.0) + duration.seconds) / 3600.0 if duration else 0.0

    date_start      = fields.Datetime(string='Date Start')
    date_end        = fields.Datetime(string='Date End')
    duration        = fields.Float(string="Duration (Hrs)", compute="_get_event_duration", store=True)
    type            = fields.Many2one('hr.employee.mro_productive.type', string="Event Type", required=True)
    productivity_type= fields.Selection([('busy', 'Busy'), ('not_busy', 'Not Busy')],
                                        string="Type", store=True,
                                        related="type.type")
    control_time_id = fields.Many2one('fleet.mro.order.task.time', string='Event Record')
    employee_id  = fields.Many2one('hr.employee', string='Mechanic', store=True, readonly=True, ondelete='restrict')
    task_id         = fields.Many2one('fleet.mro.order.task', string='Task', store=True)
    order_id        = fields.Many2one('fleet.mro.order', string='MRO Service Order', store=True)
    complete        = fields.Boolean(string="Complete", compute="_get_event_duration", store=True)
    note            = fields.Text(string="Notes")


    @api.multi
    def complete_time_rec(self):
        for rec in self:
            if rec.complete:
                continue
            rec.write({'date_end':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        return

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
