# -*- encoding: utf-8 -*-
from openerp.exceptions import UserError, ValidationError
from openerp import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit ='product.template'
    
    @api.multi
    @api.depends('duration', 'child_ids')
    def _get_child_tasks_duration(self):
        for task in self:
            child_dur = 0.0
            for subtask in task.child_ids:
                child_dur += subtask.duration_total# + (subtask.duration_childs or 0.0)
            task.duration_childs = child_dur
            task.duration_total = child_dur + task.duration
        
    fleet_mro_task = fields.Boolean(string='Fleet MRO Task', track_visibility='onchange')
    sub_tasks      = fields.Boolean(string='Sub Tasks', default=False, track_visibility='onchange')
    child_ids      = fields.Many2many('product.product', 'fleet_mro_task_sub_tasks_rel',  'task_id', 'task_child_id',
                                      string='Child Tasks', ondelete='restrict', track_visibility='onchange')
    duration = fields.Float(string="Duration", required=False, help="Please set duration in Hours",
                                      default=1.0, track_visibility='onchange')
    duration_childs = fields.Float(string="Childs Duration", compute='_get_child_tasks_duration', store=True)
    duration_total  = fields.Float(string="Total Duration", compute='_get_child_tasks_duration', store=True)

    fleet_vehicle_model_ids      = fields.Many2many('fleet.vehicle.model', 'fleet_mro_vehicle_model_tasks_rel',  'task_id', 'fleet_vehicle_model_id',
                                      string='Vehicle Model Related', ondelete='restrict', track_visibility='onchange')

class FleetVehicleModel(models.Model):
    _inherit ='fleet.vehicle.model'

    task_ids = fields.Many2many('product.product', 'fleet_mro_vehicle_model_tasks_rel', 'fleet_vehicle_model_id', 'task_id', 
                                      string='MRO Tasks Related', ondelete='restrict')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
