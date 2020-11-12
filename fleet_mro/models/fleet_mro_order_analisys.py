# -*- coding: utf-8 -*-
from openerp.exceptions import UserError
from openerp import api, fields, models, _, tools
import openerp.addons.decimal_precision as dp

class fleet_mro_order_analysis(models.Model):
    _name = 'fleet.mro.order.analysis'
    _description = "Fleet MRO Order Analisys"
    _auto = False

    name           = fields.Many2one('fleet.mro.order',string='Maint. Order')
    date           = fields.Datetime(string='Date Opened', readonly=True)
    date_start_real= fields.Datetime(string='Date Start')
    date_end_real  = fields.Datetime(string='Date End')
    mro_type_id    = fields.Many2one('fleet.mro.type',string='Service Type')
    supervisor_id  = fields.Many2one('hr.employee',string='Supervisor')
    vehicle_id     = fields.Many2one('fleet.vehicle',string='Vehicle')
    driver_id      = fields.Many2one('hr.employee',string='Driver')
    mro_cycle_id   = fields.Many2one('fleet.mro.cycle',string='Maint. Cycle')
    user_id        = fields.Many2one('res.users',string='User')
    team_id        = fields.Many2one('crm.team',string='Sales Team')
    
    partner_id     = fields.Many2one('res.partner', string='Partner')
    internal_repair= fields.Boolean(string='Internal')
    
    duration            = fields.Float(string='Scheduled Duration', digits=(18,6))
    duration_real       = fields.Float(string='Duration Real', digits=(18,6))
    duration_diff       = fields.Float(string='Duration Diff', digits=(18,6))
    manpower            = fields.Float(digits=dp.get_precision('Account'), string='Manpower')
    spare_parts         = fields.Float(digits=dp.get_precision('Account'), string='Spare Parts')
    manpower_external   = fields.Float(digits=dp.get_precision('Account'), string='External Manpower')
    spare_parts_external= fields.Float(digits=dp.get_precision('Account'), string='External Spare Parts')
    costs_internal      = fields.Float(digits=dp.get_precision('Account'), string='All Internal Costs')
    costs_external      = fields.Float(digits=dp.get_precision('Account'), string='All External Costs')
    costs_all           = fields.Float(digits=dp.get_precision('Account'), string='Total Costs')
    income_manpower     = fields.Float(digits=dp.get_precision('Account'), string='Income Manpower')
    income_spares       = fields.Float(digits=dp.get_precision('Account'), string='Income Spares')
    amount_untaxed      = fields.Float(digits=dp.get_precision('Account'), string='Total Income')
    amount_tax          = fields.Float(digits=dp.get_precision('Account'), string='Taxes')
    amount_total        = fields.Float(digits=dp.get_precision('Account'), string='Total')
    profit_or_loss      = fields.Float(digits=dp.get_precision('Account'), string='Profit/Loss')
    profit_or_loss_percent = fields.Float(digits=dp.get_precision('Account'), string='Profit/Loss %')
    
    
    
########################### Metodos ####################################################################################

    @api.model_cr
    def init(self):
        # self._table = fleet_mro_order_analysis
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""        
create or replace view fleet_mro_order_analysis as (

select 
row_number() OVER() as id, 
o.id as name, o.mro_type_id, o.supervisor_id, o.mro_cycle_id, o.driver_id,
o.team_id, o.partner_invoice_id partner_id, o.internal_repair,
o.user_id, o.vehicle_id, o.date,
o.date_start_real, o.date_end_real, 
o.duration, o.duration_real, 
o.duration -o.duration_real duration_diff, 
o.manpower * -1.0 as manpower,
o.spare_parts * -1.0 as spare_parts,
o.manpower_external * -1.0 as manpower_external,
o.spare_parts_external * -1.0 as spare_parts_external,
o.costs_internal * -1.0 as costs_internal,
o.costs_external * -1.0 as costs_external,
o.costs_all * -1.0 as costs_all,
case when o.internal_repair or not o.invoiced then 0.0 else o.income_manpower end income_manpower,
case when o.internal_repair or not o.invoiced then 0.0 else o.income_spares end income_spares,
case when o.internal_repair or not o.invoiced then 0.0 else o.amount_untaxed end amount_untaxed,
case when o.internal_repair or not o.invoiced then 0.0 else o.amount_tax end amount_tax,
case when o.internal_repair or not o.invoiced then 0.0 else o.amount_total end amount_total,
case when o.internal_repair or not o.invoiced then 0.0 else o.profit_or_loss end profit_or_loss,
case when o.internal_repair or not o.invoiced then 0.0 else o.profit_or_loss_percent end profit_or_loss_percent

from fleet_mro_order as o
where o.state = 'done'


);
  
        """)
    

    
class fleet_mro_order_task_analysis(models.Model):
    _name = 'fleet.mro.order.task.analysis'
    _description = "Fleet MRO Order Task Analisys"
    _auto = False

    name           = fields.Many2one('fleet.mro.order',string='MRO Order')    
    mro_type_id    = fields.Many2one('fleet.mro.type',string='Service Type')
    supervisor_id  = fields.Many2one('hr.employee',string='Supervisor')
    vehicle_id     = fields.Many2one('fleet.vehicle',string='Vehicle')
    driver_id      = fields.Many2one('hr.employee',string='Driver')
    mro_cycle_id   = fields.Many2one('fleet.mro.cycle',string='Maint. Cycle')
    user_id        = fields.Many2one('res.users',string='User')
    partner_id     = fields.Many2one('res.partner',string='Partner')
    internal_repair= fields.Boolean(string='Internal')
    task_id        = fields.Many2one('product.product',string='Task')
    date           = fields.Datetime('Date')
    date_start_real= fields.Datetime('Date Start')
    date_end_real  = fields.Datetime('Date End')
    income_manpower= fields.Float(string='Income Manpower', readonly=True)
    income_spares  = fields.Float(string='Income Spares', readonly=True)
    income_all     = fields.Float(string='Total Income Task', readonly=True)
    
    hours_estimated = fields.Float(string='Hours Est.', readonly=True)
    hours_real      = fields.Float(string='Hours Real', readonly=True, store=True)

    parts_cost      = fields.Float(string='Spare Parts', store=True, digits=dp.get_precision('Product Price'))
    cost_service    = fields.Float(string='Manpower', store=True, digits=dp.get_precision('Product Price'))
    cost_service_external = fields.Float(string='Service Cost External', store=True, digits=dp.get_precision('Product Price'))
    parts_cost_external   = fields.Float(string='Spare Parts External', store=True, digits=dp.get_precision('Product Price'))
    cost_internal   = fields.Float(string='Cost Internal', store=True, digits=dp.get_precision('Product Price'))
    cost_external   = fields.Float(string='Cost External', store=True, digits=dp.get_precision('Product Price'))
    cost_all        = fields.Float(string='All Costs', store=True, digits=dp.get_precision('Product Price'))
    profit_loss     = fields.Float(string='Profit/Loss', store=True, digits=dp.get_precision('Product Price'))
    
########################### Metodos ####################################################################################

    @api.model_cr
    def init(self):
        # self._table = fleet_mro_order_analysis_spare_parts
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
        
create or replace view fleet_mro_order_task_analysis as (
select 
row_number() OVER() as id, 
o.name order_name, --o.invoiced,
o.id as name, o.mro_type_id, o.supervisor_id, o.mro_cycle_id, o.driver_id,
o.team_id, o.partner_invoice_id, o.internal_repair,
o.user_id, o.vehicle_id, o.date,
task.task_id,
o.partner_invoice_id partner_id,
task.date_start_real, task.date_end_real,
case when o.invoiced then coalesce(task.price_subtotal, 0.0) else 0.0 end income_manpower,
case when o.invoiced then coalesce(task.income_spares, 0.0) else 0.0 end income_spares,
case when o.invoiced then (coalesce(task.price_subtotal, 0.0) + coalesce(task.income_spares, 0.0)) else 0.0 end income_all,
task.parts_cost * -1.0 parts_cost,
task.cost_service * -1.0 cost_service,
task.cost_service_external * -1.0 cost_service_external,
task.parts_cost_external * -1.0 parts_cost_external,
task.cost_internal * -1.0 cost_internal,
task.cost_external * -1.0 cost_external,
task.cost_all * -1.0 cost_all,
task.hours_estimated ,
task.hours_real ,
task.profit_loss
from fleet_mro_order as o
    inner join fleet_mro_order_task task on task.order_id = o.id and task.state='done'
where o.state ='done'
);   
        """)    
    
    
    
    

class fleet_mro_order_analysis_spare_parts(models.Model):
    _name = 'fleet.mro.order.analysis.spare_parts'
    _description = "Fleet MRO Order Analisys Spare Parts"
    _auto = False

    name           = fields.Many2one('fleet.mro.order',string='MRO Order')    
    mro_type_id    = fields.Many2one('fleet.mro.type',string='Service Type')
    supervisor_id  = fields.Many2one('hr.employee',string='Supervisor')
    partner_id     = fields.Many2one('res.partner',string='Partner')
    vehicle_id     = fields.Many2one('fleet.vehicle',string='Vehicle')
    driver_id      = fields.Many2one('hr.employee',string='Driver')
    mro_cycle_id   = fields.Many2one('fleet.mro.cycle',string='Maint. Cycle')
    user_id        = fields.Many2one('res.users',string='User')
    internal_repair= fields.Boolean(string='Internal')
    task_id        = fields.Many2one('product.product',string='Task')    
    date_start_real= fields.Datetime('Date Start')
    date_end_real  = fields.Datetime('Date End')
    spare_part_id  = fields.Many2one('product.product',string='Spare Part')    
    categ_id       = fields.Many2one('product.category',string='Spare Part Category')    
    date           = fields.Datetime(string='Date', readonly=True)
    product_uom_id = fields.Many2one('product.uom',string='UoM')
    quantity       = fields.Float(string='Quantity')
    price_unit     = fields.Float(string='Price Unit', digits=(18,4))
    cost_per_unit  = fields.Float(string='Cost per Unit', digits=(18,4))
    income_amount  = fields.Float(string='Income Amount', digits=dp.get_precision('Account'))
    expense_amount = fields.Float(string='Expense Amount', digits=dp.get_precision('Account'))

    
########################### Metodos ####################################################################################

    @api.model_cr
    def init(self):
        # self._table = fleet_mro_order_analysis_spare_parts
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
        
create or replace view fleet_mro_order_analysis_spare_parts as (
select 
sm.id, o.id as name, o.mro_type_id,  o.internal_repair,
o.supervisor_id, o.mro_cycle_id, o.driver_id,
o.partner_invoice_id partner_id,
o.user_id, o.vehicle_id, 
task.task_id, 
tmplt.categ_id,
task.date_start_real, task.date_end_real,
spare_part.product_id spare_part_id,
sm.date, sm.product_uom product_uom_id, 

case when location_dest.usage in ('inventory','production','customer') then 1.0 else -1.0 end * sm.product_uom_qty quantity,

case when location_dest.usage in ('inventory','production','customer') then 1.0 else -1.0 end * sm.product_uom_qty * spare_part.price_unit income_amount,
case when location_dest.usage in ('inventory','production','customer') then -1.0 else 1.0 end * sm.product_uom_qty * sm.price_unit expense_amount,
spare_part.price_unit price_unit,
sm.price_unit cost_per_unit,


spare_part.price_subtotal_2_invoice amount
from stock_move sm
    inner join product_product prod on prod.id=sm.product_id
    inner join product_template tmplt on tmplt.id=prod.product_tmpl_id
    inner join stock_location location_origin on location_origin.id=sm.location_dest_id
    inner join stock_location location_dest on location_dest.id=sm.location_dest_id
    inner join fleet_mro_order_task_spares_quotation spare_part on sm.mro_task_spare_id=spare_part.id
    inner join fleet_mro_order_task task on task.id = spare_part.task_id and task.state='done'
    inner join fleet_mro_order o on spare_part.order_id = o.id and o.state='done'
    
where sm.state ='done'
);    
        """)
        
    

class fleet_mro_order_productivity_analysis(models.Model):
    _name = 'fleet.mro.order.productivity.analysis'
    _description = "Fleet MRO Order Productivity Analisys"
    _auto = False

    name            = fields.Many2one('fleet.mro.order',string='MRO Order')    
    mro_type_id     = fields.Many2one('fleet.mro.type',string='Service Type')
    supervisor_id   = fields.Many2one('hr.employee',string='Supervisor')
    vehicle_id      = fields.Many2one('fleet.vehicle',string='Vehicle')
    driver_id       = fields.Many2one('hr.employee',string='Driver')
    partner_id      = fields.Many2one('res.partner',string='Partner')
    mro_cycle_id    = fields.Many2one('fleet.mro.cycle',string='Maint. Cycle')
    internal_repair = fields.Boolean(string='Internal')
    
    #task_id = fields.Many2one('product.product',string='Task Rec')
    task_id = fields.Many2one('product.product',string='Task')
    task_duration_est = fields.Float(string="Est. Task Duration")
    task_duration_real= fields.Float(string="Real Task Duration")
    task_duration_diff= fields.Float(string="Duration Diff")
    
    employee_id     = fields.Many2one('hr.employee',string='Mechanic')
    type            = fields.Many2one('hr.employee.mro_productive.type', string="Event Type")
    productivity_type= fields.Selection([('busy', 'Busy'), ('not_busy', 'Not Busy')],
                                        string="Type", related="type.type")
    
    date           = fields.Datetime(string='Task End Date', readonly=True)

    
########################### Metodos ####################################################################################

    @api.model_cr
    def init(self):
        # self._table = fleet_mro_order_analysis_times
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""        
create or replace view fleet_mro_order_productivity_analysis as (
select prod.id, 
o.id as name, o.mro_type_id, 
o.supervisor_id, o.mro_cycle_id, o.driver_id,
o.partner_invoice_id partner_id, o.internal_repair,
o.vehicle_id,  
task.task_id task_id, 
COALESCE(task.date_end_real, prod.date_end) date,
template.duration task_duration_est,
prod.duration task_duration_real,
prod.duration - template.duration task_duration_diff,
prod.employee_id,
prod.type,
prod.productivity_type
from hr_employee_mro_productive prod
    inner join fleet_mro_order as o on o.id=prod.order_id and o.state in ('released','done')
    inner join fleet_mro_order_task task on task.id=prod.task_id and task.state='done'
    inner join hr_employee_mro_productive_type prod_type on prod_type.id=prod.type
    inner join product_product producto on producto.id=task.task_id
    inner join product_template template on template.id=producto.product_tmpl_id
where prod.complete
);  
        """)    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

