# -*- encoding: utf-8 -*-

from openerp import api, fields, models, _
from openerp.exceptions import UserError


## MRO Maintenance Programs
class fleet_mro_program(models.Model):
    _name='fleet.mro.program'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    code        = fields.Char(string='Code', index=True, track_visibility='onchange', required=True)
    name        = fields.Char(string='Name', size=64, index=True, track_visibility='onchange', required=True)
    active      = fields.Boolean(string='Active', default=True, track_visibility='onchange')
    cycle_ids   = fields.Many2many('fleet.mro.cycle',  'fleet_mro_program_cycle_rel', 'program_id', 'cycle_id',  
                                   string='MRO Cycles Included')
    notes       = fields.Text(string="Notes")

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                    default=lambda self: self.env['res.company']._company_default_get('account.account'))

    _sql_constraints = [('code_company_uniq', 'unique (code,company_id)', 'The code of the record must be unique per company !')]
    
    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for record in self:
            name = '[' + record.code + '] ' + record.name
            result.append((record.id, name))
        return result


    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        records = self.search(domain + args, limit=limit)
        return records.name_get()    
    
    
    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        default.setdefault('code', _("%s (copy)") % (self.code or ''))
        return super(fleet_mro_program, self).copy(default)
    
## MRO Types
class fleet_mro_type(models.Model):
    _name='fleet.mro.type'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    code        = fields.Char(string='Code', index=True, track_visibility='onchange', required=True)
    name       = fields.Char(string='Name', size=64, index=True, track_visibility='onchange', required=True)
    active     = fields.Boolean(string='Active', default=True, track_visibility='onchange')
    warehouse_id  = fields.Many2one('stock.warehouse', string='Warehouse', required=True, company_dependent=True)
    #stock_location_dest_id  = fields.Many2one('stock.location', string='Location Destiny', required=True, company_dependent=True, 
    #                                          domain=[('usage','in',('inventory','production'))],
    #                                          help='Destination Stock Location to use when opening a MRO Service Order.\nTake in mind that Stock Location Account will be used for Account Moves')
    preventive = fields.Boolean(string='Preventive Maintenance', 
                               help="""Check this if this MRO Type is a Preventive Maintenance.
                                    If this is checked then when opening new Maintenance Service Order
                                    'all Tasks related to Maintenance Cycle in Maintenance PRogram will be added automatically""")
    notes      = fields.Text(string="Notes")


    stock_picking_type    = fields.Many2one('stock.picking.type', string='Stock Operation Type', required=True, company_dependent=True)
    purchase_picking_type    = fields.Many2one('stock.picking.type', string='External Workshop Operation Type', company_dependent=True, 
                                                help="Stock Operation Type used in Purchase Orders for External Workshop",
                                                required=True)
    
    dropship_picking_type = fields.Many2one('stock.picking.type', string='Dropshipping Operation Type', required=True, company_dependent=True)

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                    default=lambda self: self.env['res.company']._company_default_get('account.account'))

    fleet_vehicle_model_ids      = fields.Many2many('fleet.vehicle.model', 'fleet_mro_vehicle_model_mro_type_rel',  'mro_type_id', 'fleet_vehicle_model_id',
                                      string='Vehicle Model Related', ondelete='restrict', track_visibility='onchange')

    _sql_constraints = [
        ('code_company_uniq', 'unique (code,company_id)', 'The code of the record must be unique per company !')
        ]
    
    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for record in self:
            name = '[' + record.code + '] ' + record.name
            result.append((record.id, name))
        return result    
    

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        records = self.search(domain + args, limit=limit)
        return records.name_get()    
    
    
    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        default.setdefault('code', _("%s (copy)") % (self.code or ''))
        return super(fleet_mro_type, self).copy(default)    


class FleetVehicleModel(models.Model):
    _inherit ='fleet.vehicle.model'

    mro_type_ids = fields.Many2many('fleet.mro.type', 'fleet_mro_vehicle_model_mro_type_rel', 'fleet_vehicle_model_id', 'mro_type_id', 
                                      string='MRO Types Related', ondelete='restrict')



## MRO Cycles
class fleet_mro_cycle(models.Model):
    _name='fleet.mro.cycle'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    code       = fields.Char(string='Code', index=True, track_visibility='onchange', required=True)
    name       = fields.Char(string='Cycle', size=64, index=True, track_visibility='onchange', required=True)
    active     = fields.Boolean(string='Active', default=True, track_visibility='onchange')    
    frequency  = fields.Integer(string='Frequency', required=True,
                                help="Cycle frequency based on default vehicle/machine counter, it could be Hours / Distance (Kms / mi) / Other") # mro_frequency
    task_ids   = fields.Many2many('product.product',  'fleet_mro_cycle_task_rel', 'cycle_id', 'task_id',  string='Tasks')
    cycle_ids  = fields.Many2many('fleet.mro.cycle',  'fleet_mro_cycle_cycle_rel', 'cycle_id', 'child_cycle_id',  
                                  string='Cycles Included')
    notes      = fields.Text(string="Notes")
    
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                    default=lambda self: self.env['res.company']._company_default_get('account.account'))
    
    _sql_constraints = [
        ('code_company_uniq', 'unique (code,company_id)', 'The code of the record must be unique per company !')
        ]    
    
    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for record in self:
            name = '[' + record.code + '] ' + record.name
            result.append((record.id, name))
        return result    
    

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        records = self.search(domain + args, limit=limit)
        return records.name_get()    
    
    
    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        default.setdefault('code', _("%s (copy)") % (self.code or ''))
        return super(fleet_mro_cycle, self).copy(default)
    
"""
## TASKS
class fleet_mro_task(models.Model):
    _name='fleet.mro.task'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    @api.multi
    @api.depends('duration', 'child_ids')
    def _get_child_tasks_duration(self):
        for task in self:
            child_dur = 0.0
            for subtask in task.child_ids:
                child_dur += subtask.duration_total# + (subtask.duration_childs or 0.0)
            task.duration_childs = child_dur
            task.duration_total = child_dur + task.duration
            
        
    child_ids      = fields.Many2many('fleet.mro.task', 'fleet_mro_task_sub_tasks_rel',  'task_id', 'task_child_id',
                                      string='Child Tasks', ondelete='restrict')
    code           = fields.Char(string='Code', index=True, track_visibility='onchange', required=True)
    name           = fields.Char(string='Name', size=64, index=True, track_visibility='onchange',required=True)
    
    duration        = fields.Float(string="Duration", required=True, default=1.0, track_visibility='onchange')
    duration_childs = fields.Float(string="Childs Duration", compute='_get_child_tasks_duration', store=True)
    duration_total  = fields.Float(string="Total Duration", compute='_get_child_tasks_duration', store=True)
    
    active         = fields.Boolean(string='Active', default=True, track_visibility='onchange')
    sub_tasks      = fields.Boolean(string='Sub Tasks', default=False, track_visibility='onchange')
    
    external       = fields.Boolean(string='External', track_visibility='onchange')
    partner_id     = fields.Many2one('res.partner',string='Supplier',  domain=[('supplier','=',True)])
    categ_id       = fields.Many2one('product.category',string='Category', ondelete='restrict',  
                                     required=True, domain="[('type','=','normal')]",
                                     help="Select category for the current Task")

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get('account.account'))
    
    _sql_constraints = [
        ('code_company_uniq', 'unique (code,company_id)', 'The code of the record must be unique per company !')
        ]    
    
    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for record in self:
            name = '[' + record.code + '] ' + record.name
            result.append((record.id, name))
        return result    
    

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        records = self.search(domain + args, limit=limit)
        return records.name_get()    
    
    
    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        default.setdefault('code', _("%s (copy)") % (self.code or ''))
        return super(fleet_mro_task, self).copy(default)    
"""    
"""
    @api.multi
    def write(self, vals):
        if 'sub_tasks' in vals and not vals['sub_tasks']:
            for task in self:
                task.child_ids.unlink()
        return super(mro_task, self).write(vals)    
"""


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
