# -*- encoding: utf-8 -*-
from openerp import api, fields, models, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError
import openerp.addons.decimal_precision as dp
import datetime
from datetime import timedelta
from pytz import timezone
import pytz
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import time



# Modificamos el objeto Vehiculo para agregar los campos requeridos para MRO
class fleet_vehicle(models.Model):
    _inherit = 'fleet.vehicle'

    @api.multi
    def _get_current_odometer(self):
        odom_obj = self.env['fleet.vehicle.odometer.device']
        for record in self:
            result = odom_obj.search([('vehicle_id', '=', record.id),('state', '=', 'active')], limit=1)
            if result and result[0].id:
                record.active_odometer_id = result[0].id
            else:
                record.active_odometer_id = False


    @api.depends('model_id', 'license_plate', 'name2')
    def _compute_vehicle_name(self):
        for record in self:
            record.name = record.name2 # + ' (' + record.license_plate + ')'

    
    _order= 'name2 asc'
        
    name2           = fields.Char(string='Vehicle', size=64, required=True, readonly=False, index=True)
    
    operating_unit_id = fields.Many2one('operating.unit', string='Operating Unit', required=False, readonly=False)    
    
    
    
    tires_number               = fields.Integer(string='Number of Tires')
    tires_extra                = fields.Integer(string='Number of Extra Tires')
    mro_program_id             = fields.Many2one('fleet.mro.program', 'Maintenance Program', required=False)
    mro_cycle_ids              = fields.One2many('fleet.vehicle.mro_program', 'vehicle_id', 'MRP Program')

    last_preventive_service    = fields.Many2one('fleet.mro.order', 'Last Maintenance Service')
    main_odometer_last_service = fields.Float(related='last_preventive_service.accumulated_odometer', string="Last Serv. Odometer", store=True, readonly=True)
    odometer_last_service      = fields.Float(related='last_preventive_service.current_odometer', string="Last Serv. Active Odometer", store=True, readonly=True)
    date_last_service          = fields.Datetime(related='last_preventive_service.date', string="Date Last Serv.", store=True, readonly=True)
    sequence_last_service      = fields.Integer(related='last_preventive_service.program_sequence', string="Program Seq. Last Serv.", store=True, readonly=True)
    cycle_last_service         = fields.Many2one('fleet.mro.cycle', related='last_preventive_service.mro_cycle_id', string='Cycle Last Serv.', store=True, readonly=True)

    main_odometer_next_service = fields.Float(string='Odometer Next Serv.')
    odometer_next_service      = fields.Float(string='Active Odometer Next Serv.')
    date_next_service          = fields.Date(string='Date Next Serv.')
    sequence_next_service      = fields.Integer(string='Cycle Seq. Next Serv.')
    cycle_next_service         = fields.Many2one('fleet.mro.cycle', 'Next Maintenance Service') #, domain=[('tms_category','=','maint_service_cycle')]) # PENDIENTE TMS_AND_MRO

    avg_odometer_uom_per_day   = fields.Float(string='Active Odometer Next Serv.', default=0.0)
    active_odometer            = fields.Float(string='Odometer', required=False, digits=(20,10), help='Odometer')
    active_odometer_id         = fields.Many2one('fleet.vehicle.odometer.device', compute='_get_current_odometer', string="Active Odometer")
    current_odometer_read      = fields.Float(related='active_odometer_id.odometer_end', string='Last Odometer Read', readonly=True)
    odometer_uom               = fields.Selection([('distance','Distance (mi./km)'),
                                                   ('hours','Time (Hours)'),
                                                   ('days','Time (Days)')], 
                                                   string='Odometer UoM', help="Odometer UoM", default='distance')    

    @api.one
    @api.constrains('cycle_next_service')
    def _check_next_service(self):
        if self.cycle_next_service and self.sequence_next_service:
            res = self.env['fleet.vehicle.mro_program'].search([('vehicle_id', '=', self.id), ('cycle_id', '=', self.cycle_next_service.id), ('sequence', '=', self.sequence_next_service)])
            if not res:
                raise UserError(_('Error ! Next service Cycle and Sequence was not found in Vehicle''s Program...'))


    def return_cycle_ids(self, cycle_id):
        ids = []
        if cycle_id:
            for cycle in self.env['fleet.mro.cycle'].browse([cycle_id]).cycle_ids: 
                ids.append(cycle.id)
                if cycle.cycle_ids: # and len(cycle.mro_cycle_ids):
                    ids += self.return_cycle_ids(cycle.id)
        return ids

    @api.multi
    def button_create_mro_program(self):
        self.ensure_one()
        if not self.mro_program_id:
            raise UserError(_('Warning! \nYou have not define Preventive Maintenance Program for this vehicle')) 
            
        program_obj = self.env['fleet.vehicle.mro_program']
        prog_ids = program_obj.search([('vehicle_id', '=', self.id)])
        prog_ids.unlink()            
            
        for cycle in self.mro_program_id.cycle_ids:
            seq = 1
            for x in range(cycle.frequency, 4000000, cycle.frequency): 
                program_obj.create({'vehicle_id': self.id, 'cycle_id' : cycle.id, 'trigger' : x,  'sequence': seq})
                seq += 1
        
        seq = 1
        last_trigger = 0
        last_cycle_id = False
        for cycle in self.mro_cycle_ids:
            if last_trigger == cycle.trigger and last_cycle_id and cycle.cycle_id.id in self.return_cycle_ids(last_cycle_id):
                cycle.unlink()
            else:
                diference = cycle.trigger - last_trigger
                last_trigger = cycle.trigger
                last_cycle_id = cycle.cycle_id.id
                cycle.write({ 'sequence': seq , 'diference' : diference })
                seq += 1

        return True

    @api.one
    def get_next_service_date(self):
        if not self.date_last_service:
            raise UserError(_('Warning! \nI can not calculate Next Preventive Service Date because this Vehicle (%s) has no record for Last Preventive Service') % (self.name)) 
        date_origin = datetime.datetime.strptime(self.date_last_service, '%Y-%m-%d %H:%M:%S')
        if not self.avg_odometer_uom_per_day:
            raise UserError(_('Warning! \nI can not calculate Next Preventive Service Date because you have not defined Average distance/time per day for vehicle: %s') % (self.name)) 
        delta = timedelta(days=int((self.main_odometer_next_service - self.main_odometer_last_service)/self.avg_odometer_uom_per_day))
        date_next_service = date_origin + delta
        return date_next_service.date().isoformat()

        

#### SE COPIO DEL TMS, PENDIENTE VER LA MANERA DE QUITAR ESTA TABLA        
##### INICIO ####
# Fleet Vehicle odometer device
class fleet_vehicle_odometer_device(models.Model):
    _name = "fleet.vehicle.odometer.device"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "Fleet Vehicle Odometer Device"

    state             = fields.Selection([('draft','Draft'), 
                                          ('active','Active'), 
                                          ('inactive','Inactive'), 
                                          ('cancel','Cancelled')], 
                                         default='draft', string='State', 
                                         index=True, track_visibility='onchange', readonly=True)
    date              = fields.Datetime(string='Date', required=True, default=time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                        index=True, track_visibility='onchange', 
                                        states={'cancel':[('readonly',True)], 'active':[('readonly',True)], 'inactive':[('readonly',True)]} )
    date_start        = fields.Datetime(string='Date Start', required=True, default=time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                        states={'cancel':[('readonly',True)], 'active':[('readonly',True)], 'inactive':[('readonly',True)]} )
    date_end          = fields.Datetime(string='Date End', readonly=True)
    name              = fields.Char(string='Name', size=128, required=True, 
                                    index=True, track_visibility='onchange', 
                                    states={'cancel':[('readonly',True)], 'active':[('readonly',True)], 'inactive':[('readonly',True)]} )
    vehicle_id        = fields.Many2one('fleet.vehicle', string='Vehicle', required=True, ondelete='cascade', 
                                        index=True, track_visibility='onchange', 
                                        states={'cancel':[('readonly',True)], 'active':[('readonly',True)], 'inactive':[('readonly',True)]} )
    replacement_of    = fields.Many2one('fleet.vehicle.odometer.device', string='Replacement of', required=False,  states={'cancel':[('readonly',True)], 'active':[('readonly',True)], 'inactive':[('readonly',True)]} )
    accumulated_start = fields.Float(string='Original Accumulated', digits=(16, 2),
                                     help="Kms /Miles Accumulated from vehicle at the moment of activation of this odometer", readonly=True )
    odometer_start    = fields.Float(string='Start count', required=True, help="Initial counter from device", default=0,
                                     digits=(16, 2), states={'cancel':[('readonly',True)], 'active':[('readonly',True)], 'inactive':[('readonly',True)]} )
    odometer_end      = fields.Float(string='End count', required=True, help="Ending counter from device", digits=(16, 2), default=0,
                                     states={'cancel':[('readonly',True)], 'active':[('readonly',True)], 'inactive':[('readonly',True)]} )
    odometer_reading_ids = fields.One2many('fleet.vehicle.odometer', 'odometer_id', string='Odometer Readings', 
                                           track_visibility='onchange', readonly=True)


    @api.one
    @api.constrains('vehicle_id', 'state')
    def _check_state(self):
        xid = self.id
        res = self.search([('vehicle_id', '=', self.vehicle_id.id),('state', 'not in', ('cancel','inactive')),('state','=',self.state)])
        if res and res[0] and res[0].id != xid:
            raise UserError(_('Warning !\nYou can not have two Odometer Devices with the same State (Draft / Active) !'))
        return

    @api.one
    @api.constrains('odometer_start', 'odometer_end')
    def _check_odometer(self):
        if self.odometer_end < self.odometer_start:
            raise UserError(_('Warning !\nYou can not have Odometer End less than Odometer Start'))
        return

    @api.one
    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        xid = self.id
        if self.date_end and self.date_end < self.date_start:
            raise UserError(_('Warning !\nYou can not have Ending Date (%s) less than Starting Date (%s)')%(self.date_end, self.date_start))
        res = self.search([('vehicle_id', '=', self.vehicle_id.id),('state', '!=', 'cancel'),('date_end','>',self.date_start)])
        if res and res[0] and res[0].id != record.id:
            raise UserError(_('Warning !\nYou can not have this Star Date because is overlaping with another record'))
        return

    @api.onchange('vehicle_id')
    def on_change_vehicle_id(self):
        res = self.env['fleet.vehicle.odometer.device'].search([('vehicle_id', '=', self.vehicle_id.id),('state', '!=', 'cancel'),('date_end','<',self.date_start)], limit=1, order="date_end desc")
        odometer_id = False
        accumulated = 0.0
        for rec in res:
            self.replacement_of = rec.id
            self.accumulated = rec.vehicle_id.odometer
        return

    @api.multi
    def action_activate(self):
        self.ensure_one()
        for rec in self:
            odometer = rec.vehicle_id.odometer
            self.write({'state':'active', 'accumulated' : odometer})
        return True

    @api.multi
    def action_inactivate(self):
        self.ensure_one()
        for rec in self:
            self.write({'state':'inactive', 'date_end': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        return True

    @api.multi
    def action_cancel(self):
        self.ensure_one()
        for rec in self:
            self.write({'state':'cancel'})
        return True


# Vehicle Odometer records
class fleet_vehicle_odometer(models.Model):
    _inherit = 'fleet.vehicle.odometer'
    _name='fleet.vehicle.odometer'
### PENDIENTES
# - CALCULAR LA DISTANCIA RECORRIDA ENTRE EL REGISTRO ACTUAL Y EL ANTERIOR BASADA EN EL ODOMETRO ACTIVO. NO SE PUEDEN GUARDAR
    odometer_id       = fields.Many2one('fleet.vehicle.odometer.device', string='Odometer', required=True)
    last_odometer     = fields.Float(string='Last Read', digits=(16,2), required=True)
    current_odometer  = fields.Float(string='Current Read', digits=(16,2), required=True)
    distance          = fields.Float(string='Distance', digits=(16,2), required=True)
    #expense_id    = fields.Many2one('tms.expense', string='Expense Rec')
    #travel_id     = fields.Many2one('tms.travel', string='Travel')

            

    # @api.one
    # @api.constrains('current_odometer', 'last_odometer')    
    # def _check_values(self):
    #     if self.current_odometer <= self.last_odometer:
    #         raise UserError(_('Warning !\nYou can not have Current Reading <= Last Reading !'))
    #     return

    @api.onchange('vehicle_id')
    def _onchange_vehicle(self):
        res = super(fleet_vehicle_odometer, self)._onchange_vehicle()
        if self.vehicle_id and not self.vehicle_id.active_odometer_id:
            raise UserError(_('Warning !\nThere is no Active Odometer for vehicle %s') % (self.vehicle_id.name))
        elif self.vehicle_id and self.vehicle_id.active_odometer_id:
            self.odometer_id = self.vehicle_id.active_odometer_id.id
            self.last_odometer = self.vehicle_id.active_odometer_id.odometer_end
            self.value = self.vehicle_id.odometer
        return

    @api.onchange('current_odometer')
    def on_change_current_odometer(self):
        self.distance = self.current_odometer - self.last_odometer
        self.value = self.vehicle_id.odometer + self.distance

    @api.onchange('distance') 
    def on_change_distance(self):
        self.current_odometer = self.last_odometer + self.distance
        self.value = self.vehicle_id.odometer + self.distance

    """    
    @api.onchange('distance') 
    def on_change_value(self):
        self.distance = self.value - self.vehicle_id.odometer
        self.current_odometer = self.last_odometer + distance
    """
    
    @api.model
    def create(self, vals):
        if 'odometer_id' in vals and vals['odometer_id']:
            odometer = self.env['fleet.vehicle.odometer.device'].browse([vals['odometer_id']])
            odometer_end = odometer.odometer_end + vals['distance']
            odometer.write({'odometer_end': odometer_end})
        return super(fleet_vehicle_odometer, self).create(vals)


    def create_odometer_log(self, expense_id, travel_id, vehicle_id, distance):
        vehicle = self.env['fleet.vehicle'].browse([vehicle_id])
        last_odometer = 0.0
        if vehicle.active_odometer_id:
            last_odometer = vehicle.active_odometer_id.odometer_end
        else:
            raise UserError(_('Warning !\nCould not create Odometer Record! \nThere is no Active Odometer for Vehicle %s') % (vehicle.name))
           
        values = { 'odometer_id'      : vehicle.active_odometer_id.id,
                   'vehicle_id'       : vehicle.id,
                   'value'            : vehicle.odometer + distance,
                   'last_odometer'    : last_odometer,
                   'distance'         : distance,
                   'current_odometer' : last_odometer + distance,
                   'expense_id'       : expense_id,
                   'travel_id'        : travel_id,
                   }
        res = self.create(values)
        # Falta crear un método para actualizar el promedio diario de recorrido de la unidad        
        return

                           
    def unlink_odometer_rec(self, travel_ids, vehicle_id=False):
        unit_obj = self.env['fleet.vehicle']
        odom_dev_obj = self.env['fleet.vehicle.odometer.device']
        res = self.search([('travel_id', 'in', tuple(travel_ids),), ('vehicle_id', '=', vehicle_id)])
        res1 = self.search([('travel_id', 'in', tuple(travel_ids),)])
        for odom_rec in res:
            unit_odometer = unit_obj.browse([odom_rec.vehicle_id.id])[0].current_odometer_read
            unit_obj.browse([vehicle_id]).write({'current_odometer_read': round(unit_odometer, 2) - round(odom_rec.distance, 2)})
        res1.unlink()
        return
            
        
#### FIN ####        
#### SE COPIO DEL TMS, PENDIENTE VER LA MANERA DE QUITAR ESTA TABLA        
        
        
        
class fleet_vehicle_mro_program(models.Model):
    _name = 'fleet.vehicle.mro_program'
    _description = 'Fleet Vehicle MRO Preventive Maintenance Program'

    vehicle_id      = fields.Many2one('fleet.vehicle', string='Vehicle', required=True, ondelete='restrict', index=True)
    cycle_id        = fields.Many2one('fleet.mro.cycle', string='MRO Cycle', required=True, ondelete='restrict')
    trigger         = fields.Integer(string='Scheduled at', required=True)
    sequence        = fields.Integer(string='Sequence', required=True)
    order_id        = fields.Many2one('fleet.mro.order', string='MRO Service Order', ondelete='restrict')
    order_date      = fields.Datetime(related='order_id.date', string="Date", store=True, readonly=True)
    order_distance  = fields.Float(related='order_id.accumulated_odometer', string="mi/km", store=True, readonly=True)
    next_date       = fields.Date('Date Next Service', default=fields.Date.context_today)
    diference       = fields.Integer(string='Distance in between', default=0)

    _order = 'trigger,sequence'

    @api.multi
    def button_set_next_cycle_service(self):
        self.ensure_one()
        self.vehicle_id.write({'cycle_next_service' : self.cycle_id.id, 
                              'date_next_service'   : self.next_date or fields.Date.context_today(self), 
                              'sequence_next_service' : self.sequence,
                              'main_odometer_next_service' : self.trigger,
                              'odometer_next_service' : self.trigger})

class fleet_vehicle_mro_program_reschedule(models.TransientModel):
    _name ='fleet.vehicle.mro_program.re_schedule'
    _description = 'Vehicle MRO Program re-schedule on avg distance/time per day'

    control     = fields.Boolean('Control', default=False)
    vehicle_ids = fields.One2many('fleet.vehicle.mro_program.re_schedule.line', 'wizard_id', 'Vehicles', default='_get_vehicle_ids')
    
    @api.multi
    def do_re_schedule(self):
        for vehicle in self.vehicle_ids:
            vehicle.write({'date_next_service':vehicle.next_date})
                
        return {'type': 'ir.actions.act_window_close'}
    
    
    def _get_vehicle_ids(self):
        vehicle_ids = []
        ids = self._context.get('active_ids', False)
        vehicle_obj = self.env['fleet.vehicle']
        for rec in vehicle_obj.browse(ids):
            vehicle_ids.append({'vehicle_id'        : rec.id,
                                'mro_program_id'    : rec.mro_program_id.id,
                                'cycle_next_service': rec.cycle_next_service.id,
                                'sequence_next_service': rec.sequence_next_service,
                                'odometer'          : rec.odometer,
                                'current_odometer'  : rec.current_odometer_read,
                                'avg_odometer_uom_per_day'  : rec.avg_odometer_uom_per_day,
                                'date_next_service' : rec.date_next_service,
                                'next_date'         : rec.get_next_service_date()[0], 
                                })

        return vehicle_ids
    
    
class fleet_vehicle_mro_program_reschedule_line(models.TransientModel):
    _name ='fleet.vehicle.mro_program.re_schedule.line'
    _description = 'Vehicle MRO Program re-schedule line'

    wizard_id                 = fields.Many2one('fleet.vehicle.mro_program.re_schedule', string="Wizard", ondelete='cascade')
    vehicle_id                = fields.Many2one('fleet.vehicle', 'Vehicle', required=True, readonly=True)
    mro_program_id            = fields.Many2one('fleet.mro.program', related='vehicle_id.mro_program_id', string='Maintenance Program', readonly=True)
    cycle_next_service        = fields.Many2one('fleet.mro.cycle', related='vehicle_id.cycle_next_service', string='Next Maintenance Service', readonly=True)
    sequence_next_service     = fields.Integer(related='vehicle_id.sequence_next_service', string='Cycle Seq. Next Serv.', readonly=True)
    odometer                  = fields.Float(related='vehicle_id.odometer', string='Accumulated Odometer', readonly=True)
    current_odometer          = fields.Float(related='vehicle_id.current_odometer_read', string='Current Odometer', readonly=True)
    avg_odometer_uom_per_day  = fields.Float(related='vehicle_id.avg_odometer_uom_per_day', string='Avg Distance/Time per day', readonly=True)
    date_next_service         = fields.Date(related='vehicle_id.date_next_service', string='Date Next Serv.', readonly=True)
    next_date                 = fields.Date('NEW Next Service', required=True)



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

