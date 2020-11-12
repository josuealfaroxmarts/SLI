# -*- encoding: utf-8 -*-
from openerp.exceptions import UserError, ValidationError
from openerp import api, fields, models, _


class hr_job(models.Model):
    _inherit = "hr.job"

    wage_per_hour       = fields.Float(string='Hourly Salary', digits=(18,2), default=0)


class hr_employee(models.Model):
    _inherit='hr.employee'

    fleet_mro_mechanic  = fields.Boolean(string='Fleet MRO Mechanic')
    wage_per_hour       = fields.Float(related="job_id.wage_per_hour", string='Hourly Salary', digits=(18,2), readonly=True)
    

## MRO Tast Time Event Types
class hr_employee_mro_productive_type(models.Model):
    _name='hr.employee.mro_productive.type'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    code        = fields.Char(string='Code', index=True, required=True, track_visibility='onchange')
    name        = fields.Char(string='Name', size=64, index=True, required=True, track_visibility='onchange')
    active      = fields.Boolean(string='Active', default=True, track_visibility='onchange')
    
    type        = fields.Selection([('busy', 'Busy'), ('not_busy', 'Not Busy')], default='not_busy',
                                    string="Type", required=True, track_visibility='onchange')

    default_for_busy = fields.Boolean(string='Default for Busy', default=False, track_visibility='onchange')
    notes       = fields.Text(string="Notes")

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                    default=lambda self: self.env['res.company']._company_default_get('account.account'))

    _sql_constraints = [('code_company_uniq', 'unique (code,company_id)', 'The code of the record must be unique per company !')]
    
    @api.multi
    @api.constrains('default_for_busy')
    def _check_default_for_busy(self):        
        for record in self:
            res = self.env['hr.employee.mro_productive.type'].search([('default_for_busy', '=', 1)], limit=1)
            print "res: ", res
            print "res.id: ", res.id
            print "record.id: ", record.id
            if record.default_for_busy and res and res.id != record.id:
                raise ValueError(_('Error ! You can not have more than one Type defined as Default for Busy'))

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for record in self:
            name = '[' + record.code + '] ' + record.name
            result.append((record.id, name))
        return result







# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
