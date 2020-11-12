# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import odoo.addons.decimal_precision as dp
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from pytz import timezone
import pytz
import time
import logging
_logger = logging.getLogger(__name__)


class fleet_mro_order(models.Model):
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _name = 'fleet.mro.order'
    _description = 'MRO Service Order'

    @api.multi
    @api.depends('state','task_ids.spares_quotation_line_ids.price_subtotal','task_ids.stock_move_ids.state','purchase_order_ids.state','task_ids.control_time_ids.state')
    def _get_resume(self):
        for rec in self:
            spares, manpower, spares_ext, manpower_ext, hours_real, income_manpower, income_spares, amount_tax = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
            for task in rec.task_ids:
                income_manpower += task.price_subtotal
                amount_tax += task.price_tax
                for spare in task.spares_quotation_line_ids:
                    income_spares += spare.price_subtotal_2_invoice
                    amount_tax += spare.price_tax
                for xline in task.stock_move_ids.filtered(lambda r: r.state == 'done'):
                    if xline.location_id.usage =='supplier' and xline.location_dest_id.usage in ('production','inventory','customer'): # Compra de refacciones para Taller Externo
                        spares_ext += (xline.price_unit * xline.product_uom_qty)
                    elif xline.location_dest_id.usage =='supplier' and xline.location_id.usage in ('production','inventory','customer'): # Devolución de Compra de refacciones para Taller Externo
                        spares_ext -= (xline.price_unit * xline.product_uom_qty)
                    elif xline.location_id.usage =='internal' and xline.location_dest_id.usage in ('production','inventory','customer'): # Salidas de Inventario
                        spares += (xline.price_unit * xline.product_uom_qty)
                    elif xline.location_dest_id.usage =='internal' and xline.location_id.usage in ('production','inventory','customer'): # Devoluciones de Inventario
                        spares -= (xline.price_unit * xline.product_uom_qty)
                for line in task.control_time_ids:
                    cost_mechanic = line.hr_employee_id.wage_per_hour or 0.0
                    manpower += (cost_mechanic * line.hours_mechanic)
                    hours_real += line.hours_mechanic
            for purchase in rec.purchase_order_ids:
                if purchase.state in ('purchase', 'done'):
                    manpower_ext += purchase.mro_manpower                    
            rec.update({'spare_parts'   : spares,
                        'manpower'      : manpower,
                        'spare_parts_external': spares_ext,
                        'manpower_external'   : manpower_ext,
                        'costs_internal': spares + manpower,
                        'costs_external': spares_ext + manpower_ext,
                        'costs_all'     : spares + manpower + spares_ext + manpower_ext,
                        'income_manpower': rec.pricelist_id.currency_id.round(income_manpower),
                        'income_spares' : rec.pricelist_id.currency_id.round(income_spares),
                        'amount_untaxed': rec.pricelist_id.currency_id.round(income_manpower + income_spares),
                        'amount_tax'    : rec.pricelist_id.currency_id.round(amount_tax),
                        'amount_total'  : rec.pricelist_id.currency_id.round(income_manpower + income_spares + amount_tax),
                        'profit_or_loss': (income_manpower + income_spares) - (spares + manpower + spares_ext + manpower_ext),
                        'profit_or_loss_percent': (income_manpower + income_spares) and \
                            (((income_manpower + income_spares) - (spares + manpower + spares_ext + manpower_ext)) / (income_manpower + income_spares))  \
                            or 0.0
                       })            
            

    @api.one
    @api.depends('date_end', 'date_start', 'date_end_real', 'date_start_real')
    def _get_duration(self):
        x1 = x2 = 0.0
        if self.date_end and self.date_start:
            dur1 = datetime.strptime(self.date_end, '%Y-%m-%d %H:%M:%S') - datetime.strptime(self.date_start, '%Y-%m-%d %H:%M:%S')
            x1 = ((dur1.days * 24.0*60.0*60.0) + dur1.seconds) / 3600.0 if dur1 else 0.0
            #res[record.id]['duration'] = x1
        if self.date_end_real and self.date_start_real:
            dur2 = datetime.strptime(self.date_end_real, '%Y-%m-%d %H:%M:%S') - datetime.strptime(self.date_start_real, '%Y-%m-%d %H:%M:%S')
            x2 = ((dur2.days * 24.0*60.0*60.0) + dur2.seconds) / 3600.0 if dur2 else 0.0
            #res[record.id]['duration_real'] = x2
        self.duration = x1
        self.duration_real = x2


    @api.multi
    @api.depends('purchase_order_ids', 'task_ids')
    def _check_counters(self):
        for record in self:
            purchase_order_ids = [x.id for x in record.purchase_order_ids]
            stock_picking_ids = [z.id for z in record.stock_picking_ids]
            time_records_count = []
            tasks_count = 0
            for rec in record.task_ids:
                tasks_count += 1
                time_records_count = [y.id for y in rec.control_time_ids]
            record.purchase_order_count = len(set(purchase_order_ids)) 
            record.time_records_count = len(set(time_records_count))
            record.task_records_count = tasks_count
            record.stock_pickings_count = len(set(stock_picking_ids))
            record.driver_report_count = len(record.fleet_mro_driver_report_ids)

    @api.multi
    @api.depends('state', 'invoice_id', 'invoice_id.state')
    def _get_invoiced(self):
        """
        Compute the invoice status of a SO. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also hte default value if the conditions of no other status is met.
        - to invoice: if any SO line is 'to invoice', the whole SO is 'to invoice'
        - invoiced: if all SO lines are invoiced, the SO is invoiced.
        - upselling: if all SO lines are invoiced or upselling, the status is upselling.

        The invoice_ids are obtained thanks to the invoice lines of the SO lines, and we also search
        for possible refunds created directly from existing invoices. This is necessary since such a
        refund is not directly linked to the SO.
        """
        for order in self:
            invoice_ids = [] #order.task_ids.mapped('invoice_id').filtered(lambda r: r.type in ['out_invoice', 'out_refund'])
            refunds = [] # invoice_ids.search([('origin', 'like', order.name)])
            #invoice_ids |= refunds.filtered(lambda r: order.name in [origin.strip() for origin in r.origin.split(',')])
            # Search for refunds as well
            #refund_ids = self.env['account.invoice'].browse()
            #if invoice_ids:
            #    for inv in invoice_ids:
            #        refund_ids += refund_ids.search([('type', '=', 'out_refund'), ('origin', '=', inv.number), ('origin', '!=', False), ('journal_id', '=', inv.journal_id.id)])

            #line_invoice_status = [line.invoice_status for line in order.task_ids]

            if order.internal_repair or order.state not in ('done'):
                invoice_status = 'no'
            elif not order.invoice_id or order.invoice_id.state == 'cancel':
                invoice_status = 'to invoice'
            elif order.invoice_id and order.invoice_id.state != 'cancel':
                invoice_status = 'invoiced'
            else:
                invoice_status = 'no'
            order.update({
                'invoice_count': (order.invoice_id and order.invoice_id.state != 'cancel') and 1 or 0,
                'invoice_ids': order.invoice_id and [order.invoice_id.id] or [],
                'invoice_status': invoice_status,
            })


    @api.model
    def _get_default_team(self):
        return self.env['crm.team']._get_default_team_id()


    @api.multi
    @api.depends('invoice_id', 'invoice_id.state')
    def _invoiced(self):    
        for order in self:
            order.invoiced     = bool(order.invoice_id and order.invoice_id.state != 'cancel' or False)
            order.paid         = bool(order.invoice_id and order.invoice_id.state == 'paid' or False)
            order.invoice_name = order.invoice_id and order.invoice_id.state != 'cancel' and (order.invoice_id.number or order.invoice_id.reference) or False    
    
    
    ### Columns ###
    name                 = fields.Char(string='Name', readonly=True)
    state                = fields.Selection([('cancel','Cancelled'), 
                                             ('draft','Draft'),
                                             ('scheduled','Scheduled'),
                                             ('check_in','Check In'),
                                             ('revision','Revision'),
                                             ('waiting_approval','Waiting Approval'),
                                             ('open','Open'), 
                                             ('released','Released'),
                                             ('done','Done')],
                                            string='State', default='draft', index=True, track_visibility='onchange')
    description          = fields.Char(string='Description', readonly=False, 
                                        states={'done':[('readonly',True)],'cancel':[('readonly',True)]})
    note                 = fields.Text(string='Notes', readonly=False, 
                                        states={'done':[('readonly',True)],'cancel':[('readonly',True)]})
    partner_id          = fields.Many2one('res.partner', string='Customer', readonly=False, change_default=True, index=True, 
                                            track_visibility='always', domain=[('customer', '=', True)], ondelete='restrict',
                                            states={'done':[('readonly',True)], 'cancel':[('readonly',True)]})
    partner_invoice_id  = fields.Many2one('res.partner', string='Invoice Address', readonly=False, help="Invoice address for current MRO Service Order.", 
                                            track_visibility='always', domain=[('customer', '=', True)], ondelete='restrict',
                                            states={'done':[('readonly',True)], 'cancel':[('readonly',True)]})
    partner_contact_id = fields.Many2one('res.partner', string='Contact', readonly=False, help="Contact that will receive vehicle.", 
                                            track_visibility='always', domain=[('customer', '=', True)], ondelete='restrict',
                                            states={'done':[('readonly',True)], 'cancel':[('readonly',True)]})

    pricelist_id        = fields.Many2one('product.pricelist', string='Pricelist', required=True, readonly=False, 
                                          states={'waiting_approval':[('readonly',True)],'open':[('readonly',True)],'released':[('readonly',True)], 'done':[('readonly',True)], 'cancel':[('readonly',True)]},
                                          help="Pricelist for current sales order.")
    currency_id         = fields.Many2one("res.currency", related='pricelist_id.currency_id', string="Currency", readonly=True, required=True)
    payment_term_id     = fields.Many2one('account.payment.term', string='Payment Terms', readonly=False, 
                                          states={'waiting_approval':[('readonly',True)],'open':[('readonly',True)],'released':[('readonly',True)], 'done':[('readonly',True)], 'cancel':[('readonly',True)]})
    fiscal_position_id  = fields.Many2one('account.fiscal.position', string='Fiscal Position', readonly=False,
                                          states={'waiting_approval':[('readonly',True)],'open':[('readonly',True)],'released':[('readonly',True)], 'done':[('readonly',True)], 'cancel':[('readonly',True)]})
    company_id          = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('fleet.mro.order'))
    user_id             = fields.Many2one('res.users', string='Salesperson', index=True, track_visibility='onchange', default=lambda self: self.env.user,
                                            readonly=False, 
                                            states={'done':[('readonly',True)],'cancel':[('readonly',True)]})
    team_id             = fields.Many2one('crm.team', string='Sales Team', change_default=True, default=_get_default_team, readonly=False, 
                                            states={'done':[('readonly',True)],'cancel':[('readonly',True)]})
    project_id          = fields.Many2one('account.analytic.account', 'Analytic Account', readonly=False,
                                          states={'cancel':[('readonly',True)], 'open':[('readonly',True)], 'released':[('readonly',True)], 'done':[('readonly',True)]},
                                            help="The analytic account related to a MRO Service Order.", copy=False)
    related_project_id  = fields.Many2one('account.analytic.account', inverse='_inverse_project_id', related='project_id', 
                                            string='Analytic Account', help="The analytic account related to a sales order.")
    client_order_ref    = fields.Char(string='Customer Reference', copy=False, readonly=False,
                                      states={'released':[('readonly',False)],'done':[('readonly',False)],'cancel':[('readonly',False)]})
    
    invoice_count = fields.Integer(string='# of Invoices', compute='_get_invoiced', readonly=True)
    invoice_ids = fields.Many2many("account.invoice", string='Invoices', compute="_get_invoiced", readonly=True, copy=False)
    
    invoice_id       = fields.Many2one('account.invoice', string='Invoice', default=False,
                                       index=True, track_visibility='onchange', readonly=True)
    invoiced         = fields.Boolean(compute='_invoiced', string='Invoiced', store=True, default=False)
    invoice_paid     = fields.Boolean(compute='_invoiced', string='Paid', store=True, default=False)
    invoice_name     = fields.Char(compute='_invoiced', string='Invoice', size=64, store=True, default=False)
    
    invoice_status = fields.Selection([ ('to invoice', 'To Invoice'),
                                        ('invoiced', 'Invoiced'),
                                        ('partial', 'Partially Invoiced'),
                                        ('no', 'Nothing to Invoice')
                                        ], string='Invoice Status', compute='_get_invoiced', store=True, readonly=True)

    internal_repair     = fields.Boolean(string='Internal', readonly=False, default=False, track_visibility='onchange',
                                          states={'cancel':[('readonly',True)],'open':[('readonly',True)],'released':[('readonly',True)],'done':[('readonly',True)]})
    date_start          = fields.Datetime(
        string='Scheduled Start',
        required=False,
        # default=time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
        default=fields.Datetime.now,
        track_visibility='onchange',
        readonly=True,
        states={
            'draft':[('required',False),('readonly',False)],
            'scheduled':[('required',True),('readonly',False)],
            'check_in':[('required',True),('readonly',False)],
            'revision':[('required',True),('readonly',False)],
            'waiting_approval':[('required',True),('readonly',False)],
            'open':[('required',True),('readonly',False)]})
    date_end            = fields.Datetime(string='Scheduled End', required=False, track_visibility='onchange',
                                          readonly=True, 
                                          states={'draft':[('required',False),('readonly',False)],
                                                  'scheduled':[('readonly',False)],
                                                  'check_in':[('readonly',False)],
                                                  'revision':[('readonly',False)],
                                                  'waiting_approval':[('required',True),('readonly',False)],
                                                  'open':[('required',True),('readonly',False)]})
    date_start_real     = fields.Datetime(string='Real Start', track_visibility='onchange', readonly=True,
                                         states={'draft':[('readonly',False)]})
    date_end_real       = fields.Datetime(string='Real End', track_visibility='onchange', readonly=True)
    date_appointment    = fields.Datetime(string='Appointment', track_visibility='onchange', readonly=True)
    date                = fields.Datetime(
        string='Date',
        readonly=True,
        # default=time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
        default=fields.Datetime.now,
        states={'draft':[('readonly',False)],'scheduled':[('readonly',False)],'check_in':[('readonly',False)],'revision':[('readonly',False)],'waiting_approval':[('readonly',False)]},
        track_visibility='onchange', required=True)
    duration            = fields.Float(compute='_get_duration', string='Scheduled Duration', digits=(18,6), store=True,
                                        help="Scheduled duration in hours")
    duration_real       = fields.Float(compute='_get_duration', string='Duration Real', digits=(18,6), store=True,
                                        help="Real duration in hours")
    manpower            = fields.Float(compute='_get_resume', digits=dp.get_precision('Product Price'), store=True, 
                                             string='Manpower')
    spare_parts         = fields.Float(compute='_get_resume', digits=dp.get_precision('Product Price'), 
                                             string='Spare Parts', store=True)

    manpower_external   = fields.Float(compute='_get_resume', digits=dp.get_precision('Product Price'), 
                                             string='External Manpower', store=True)

    spare_parts_external= fields.Float(compute='_get_resume', digits=dp.get_precision('Product Price'), 
                                             string='External Spare Parts', store=True)

    costs_internal      = fields.Float(compute='_get_resume', digits=dp.get_precision('Product Price'), 
                                             string='All Internal Costs', store=True)
    
    costs_external      = fields.Float(compute='_get_resume', digits=dp.get_precision('Product Price'), 
                                             string='All External Costs', store=True)
    
    costs_all           = fields.Float(compute='_get_resume', digits=dp.get_precision('Product Price'), 
                                             string='All Costs', store=True)
    
    income_manpower     = fields.Float(compute='_get_resume', digits=dp.get_precision('Product Price'), 
                                             string='Income Manpower', store=True)
    
    income_spares       = fields.Float(compute='_get_resume', digits=dp.get_precision('Product Price'), 
                                             string='Income Spares', store=True)
    
    amount_untaxed      = fields.Monetary(compute='_get_resume', digits=dp.get_precision('Product Price'), 
                                             string='Subtotal', store=True)
    
    amount_tax          = fields.Monetary(compute='_get_resume', digits=dp.get_precision('Product Price'), 
                                             string='Taxes', store=True)
    
    amount_total        = fields.Monetary(compute='_get_resume', digits=dp.get_precision('Product Price'), 
                                             string='Total', store=True)
    
    profit_or_loss      = fields.Float(compute='_get_resume', digits=dp.get_precision('Product Price'), 
                                             string='Profit/Loss', store=True)
    
    profit_or_loss_percent = fields.Float(compute='_get_resume', digits=dp.get_precision('Product Price'), 
                                             string='Profit/Loss %', store=True)

    operating_unit_id            = fields.Many2one('operating.unit', string='Operating Unit', required=True, readonly=True, track_visibility='onchange',
                                           states={'draft':[('readonly',False)]}, ondelete='restrict')
    vehicle_id           = fields.Many2one('fleet.vehicle', string='Vehicle', required=True, track_visibility='onchange',
                                           # readonly=True, 
                                           # states={'draft':[('readonly',False)]}, 
                                           ondelete='restrict')
    mro_type_id           = fields.Many2one('fleet.mro.type', string='Main Service Type', required=True, track_visibility='onchange',
                                           readonly=False, states={'draft':[('readonly',False)], 'scheduled':[('readonly',False)], 'check_in':[('readonly',False)], 'revision':[('readonly',False)], 'waitting_approval':[('readonly',False)]}, 
                                            ondelete='restrict')
    driver_id            = fields.Many2one('res.partner', string='Driver', track_visibility='onchange',
                                           # domain=[('tms_category', '=', 'driver'),('tms_supplier_driver', '=', False)],  # PENDIENTE TMS_AND_MRO
                                           required=False, 
                                           readonly=True, states={'draft':[('readonly',False)], 'scheduled':[('readonly',False)], 'check_in':[('readonly',False)], 'revision':[('readonly',False)], 'waitting_approval':[('readonly',False)]}, 
                                           ondelete='restrict')
    supervisor_id        = fields.Many2one('hr.employee', string='Supervisor', track_visibility='onchange',
                                           domain=[('fleet_mro_mechanic', '=', True)],
                                           required=True, 
                                           readonly=True, states={'draft':[('readonly',False)], 'scheduled':[('readonly',False)], 'check_in':[('readonly',False)], 'revision':[('readonly',False)], 'waitting_approval':[('readonly',False)], 'open':[('readonly',False)]}, 
                                           ondelete='restrict')
    user_id              = fields.Many2one('res.users', string='User', readonly=True, 
                                           default=lambda self: self.env.user, ondelete='restrict')
    warehouse_id         = fields.Many2one('stock.warehouse', string='Warehouse', required=True, track_visibility='onchange',
                                           readonly=True, states={'draft':[('readonly',False)], 'scheduled':[('readonly',False)], 'check_in':[('readonly',False)], 'revision':[('readonly',False)], 'waitting_approval':[('readonly',False)]}, 
                                           ondelete='restrict')
    
    stock_origin_id      = fields.Many2one('stock.location', string='Stock Location Origin', required=True, readonly=True, states={'draft':[('readonly',False)]}, 
                                           domain=[('usage', '=', 'internal'),('chained_location_type', '=', 'none')], ondelete='restrict')
    stock_dest_id        = fields.Many2one('stock.location','Stock Location Dest', ondelete='restrict', required=True)


    accumulated_odometer = fields.Float(string='Accumulated Odometer', 
                                        readonly=True, states={'draft':[('readonly',False)], 'scheduled':[('readonly',False)], 'check_in':[('readonly',False)], 'revision':[('readonly',False)], 'waitting_approval':[('readonly',False)]})
    current_odometer     = fields.Float(string='Current Odometer', 
                                        readonly=True, states={'draft':[('readonly',False)], 'scheduled':[('readonly',False)], 'check_in':[('readonly',False)], 'revision':[('readonly',False)], 'waitting_approval':[('readonly',False)]})
    program_sequence     = fields.Integer(string='Preventive Program Seq.', 
                                          readonly=True, states={'draft':[('readonly',False)], 'scheduled':[('readonly',False)], 'check_in':[('readonly',False)], 'revision':[('readonly',False)], 'waitting_approval':[('readonly',False)]})
    mro_program_id       = fields.Many2one('fleet.mro.program', string='Preventive Program', ondelete='restrict',
                                           readonly=False, states={'draft':[('readonly',False)], 'scheduled':[('readonly',False)], 'check_in':[('readonly',False)], 'revision':[('readonly',False)], 'waitting_approval':[('readonly',False)]})
    
    mro_cycle_id       = fields.Many2one('fleet.mro.cycle', string='Preventive Cycle', ondelete='restrict',
                                           readonly=False, states={'draft':[('readonly',False)], 'scheduled':[('readonly',False)], 'check_in':[('readonly',False)], 'revision':[('readonly',False)], 'waitting_approval':[('readonly',False)]})


    task_ids             = fields.One2many('fleet.mro.order.task', 'order_id', string='Tasks', readonly=False, 
                                           states={'cancel':[('readonly',True)], 'released':[('readonly',True)], 'done':[('readonly',True)]})
    
    spares_quotation_line_ids = fields.One2many('fleet.mro.order.task.spares_quotation', 'order_id', string="Spare Parts Quotation"
                                            )
                                                
    stock_picking_ids    = fields.One2many('stock.picking','mro_order_id', string='Stock Pickings')
    stock_move_ids       = fields.One2many('stock.move','mro_order_id', string='Stock Moves')
    
    purchase_order_line_ids  = fields.One2many('purchase.order.line','mro_order_id',string='External Workshop Detail')
    purchase_order_ids  = fields.One2many('purchase.order','mro_order_id',string='External Workshop')
    fleet_mro_driver_report_ids   = fields.Many2many('fleet.mro.driver_report', 'fleet_mro_driver_report_mro_order_rel', 
                                                     'order_id', 'report_id', 
                                                     string='Driver Report of Failures', readonly=True, 
                                                     states={'draft':[('readonly',False)], 'open':[('readonly',False)], 'released':[('readonly',False)]},
                                                     required=True)
    
    purchase_order_count = fields.Integer(string='# of External Workshop', compute='_check_counters', readonly=True)
    task_records_count   = fields.Integer(string='# of Tasks', compute='_check_counters', readonly=True)
    time_records_count   = fields.Integer(string='# of Time Records', compute='_check_counters', readonly=True)
    stock_pickings_count = fields.Integer(string='# of Pickings', compute='_check_counters', readonly=True)
    driver_report_count  = fields.Integer(string='# of Driver Reports', compute='_check_counters', readonly=True)
    dummy                = fields.Boolean(string="Usado para vista Kanban")

    _order = 'date, name'

    def _inverse_project_id(self):
        self.project_id = self.related_project_id

    """    
    @api.multi
    @api.constrains('vehicle_id', 'state', 'operating_unit_id')
    def _check_unique_draft_open_state_per_vehicle(self):
        parameter = int(self.env['ir.config_parameter'].get_param('fleet_mro_restrict_morethanone_service_order_in_draft_open_state')[0]) or 0
        if parameter:
            for record in self:
                res = self.search([('vehicle_id','=',record.vehicle_id.id),('state','in',('draft','scheduled','revision','waiting_approval','open')),('operating_unit_id','=',record.operating_unit_id.id)])
                if res and record.state in ('draft','open') and res.id != record.id:
                    raise ValueError(_('Error ! You can''t have more than one Service Order in Draft / Open state for this Vehicle'))
        return
    
    @api.multi
    @api.constrains('vehicle_id', 'state', 'operating_unit_id')
    def _check_unique_released_state_per_vehicle(self):
        parameter = int(self.env['ir.config_parameter'].get_param('fleet_mro_restrict_more_than_one_service_order_in_released_state')[0]) or 0
        if parameter:
            for record in self:
                res = self.search([('vehicle_id','=',record.vehicle_id.id),('state','=','released'),('operating_unit_id','=',record.operating_unit_id.id)])
                if res and record.state == 'released' and res.id != record.id:
                    raise ValueError(_('Error ! You can''t have more than one Service Order in Released State for this Vehicle'))
        return


    """
    @api.onchange('fiscal_position_id')
    def _compute_tax_id(self):
        return # PENDIENTE
        for order in self:
            order.task_ids._compute_tax_id()


    @api.multi
    @api.onchange('internal_repair')
    def onchange_internal_repair(self):
        if self.internal_repair:
            self.partner_id = self.env.user.company_id.partner_id.id
        else:
            self.update({
                'partner_invoice_id': False,
                'partner_contact_id': False,
                'payment_term_id': False,
                'fiscal_position_id': False,
            })
        return


    @api.multi
    @api.onchange('partner_contact_id', 'partner_id')
    def onchange_partner_contact_id(self):
        """
        Trigger the change of fiscal position when the shipping address is modified.
        """
        self.fiscal_position_id = self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id, self.partner_contact_id.id)
        return {}

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment term
        - Invoice address
        - Delivery address
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_contact_id': False,
                'payment_term_id': False,
                'fiscal_position_id': False,
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_contact_id': addr['delivery'],
        }
        if self.env.user.company_id.sale_note:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.user.company_id.sale_note
        self.update(values)

        
    @api.onchange('partner_id')
    def onchange_partner_id_warning(self):
        if not self.partner_id:
            return
        warning = {}
        title = False
        message = False
        partner = self.partner_id

        # If partner has no warning, check its company
        if partner.sale_warn == 'no-message' and partner.parent_id:
            partner = partner.parent_id

        if partner.sale_warn != 'no-message':
            # Block if partner only has warning but parent company is blocked
            if partner.sale_warn != 'block' and partner.parent_id and partner.parent_id.sale_warn == 'block':
                partner = partner.parent_id
            title = ("Warning for %s") % partner.name
            message = partner.sale_warn_msg
            warning = {
                    'title': title,
                    'message': message,
            }
            if partner.sale_warn == 'block':
                self.update({'partner_id': False, 'partner_invoice_id': False, 'partner_contact_id': False, 'pricelist_id': False})
                return {'warning': warning}

        if warning:
            return {'warning': warning}

    
    @api.model
    def create(self, vals):
        operating_unit = self.env['operating.unit'].browse([vals['operating_unit_id']])
        if operating_unit.fleet_mro_service_order_seq:
            vals['name'] = operating_unit.fleet_mro_service_order_seq.next_by_id()
        else:
            raise ValueError(_('MRO Sequence Error ! You have not defined MRO Service Order Sequence for Operating Unit ' + operating_unit.name))
        # Makes sure partner_invoice_id', 'partner_contact_id' and 'pricelist_id' are defined
        if any(f not in vals for f in ['partner_invoice_id', 'partner_contact_id', 'pricelist_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
            vals['partner_contact_id'] = vals.setdefault('partner_contact_id', addr['delivery'])
            vals['pricelist_id'] = vals.setdefault('pricelist_id', partner.property_product_pricelist and partner.property_product_pricelist.id)
            
        return super(fleet_mro_order, self).create(vals)
    
    
    @api.onchange('mro_type_id','date', 'vehicle_id')
    def on_change_mro_type_id(self):
        if self.mro_type_id:
            self.warehouse_id = self.mro_type_id.warehouse_id
            self.operating_unit_id = self.mro_type_id.warehouse_id.operating_unit_id
            self.stock_origin_id = self.mro_type_id.stock_picking_type.default_location_src_id.id
            self.stock_dest_id = self.mro_type_id.stock_picking_type.default_location_dest_id.id
        if self.mro_type_id.preventive and self.vehicle_id.mro_program_id and \
           self.vehicle_id.sequence_next_service:
            #self.vehicle_id.main_odometer_next_service and \
            #self.vehicle_id.odometer_next_service  and self.vehicle_id.cycle_next_service:
            self.program_sequence = self.vehicle_id.sequence_next_service
            self.mro_program_id = self.vehicle_id.mro_program_id.id
            self.mro_cycle_id   = self.vehicle_id.cycle_next_service.id
            self.task_ids         = self.get_tasks_from_cycle(self.vehicle_id.cycle_next_service, self.date)        
                        
    
    @api.onchange('vehicle_id')
    def on_change_vehicle_id(self):
        if not self.vehicle_id:
            return
        self.accumulated_odometer   = self.vehicle_id.odometer
        self.current_odometer       = self.vehicle_id.current_odometer_read
        self.driver_id              = self.vehicle_id.driver_id.id
        domain = {}
        res = [x.id for x in self.vehicle_id.model_id.mro_type_ids] or [0]
        for mro_type in self.env['fleet.mro.type'].search([('fleet_vehicle_model_ids','=',False),('id','not in', res)]):
            res.append(mro_type.id)
        domain['mro_type_id'] = [('id', 'in', res)]
        return {'domain': domain}


    
    @api.onchange('warehouse_id')
    def on_change_warehouse_id(self):
        self.stock_origin_id   = self.warehouse_id.lot_stock_id.id
    

    @api.multi
    def action_view_purchase_orders(self):
        if self.state in ('draft','cancel'):
            raise UserError(_('Warning!!! \n\nYou cannot create Purchase Orders for External Workshop on MRO Service Order in Draft or Cancel State'))
        record_ids = self.mapped('purchase_order_ids')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('fleet_mro.fleet_mro_purchase_form_action')
        list_view_id = imd.xmlid_to_res_id('purchase.purchase_order_tree')
        form_view_id = imd.xmlid_to_res_id('purchase.purchase_order_form')

        result = {
            'name': _('External Workshop for MRO Service Order %s') % (self.name),
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        result['context'] = "{'default_fleet_mro_related': %s, 'default_mro_order_id': %s, 'search_default_mro_order_id': [%s], 'default_picking_type_id': %s, 'default_for_fleet_mro_order':True}" % (True, self.id, self.id, self.internal_repair and self.mro_type_id.purchase_picking_type.id or self.mro_type_id.dropship_picking_type.id)
        result['domain'] = "[('mro_order_id','=',%s)]" % self.id
        return result


    @api.multi
    def action_view_pickings(self):
        if self.state in ('draft','cancel'):
            raise UserError(_('Warning!!! \n\nYou cannot create Pickings on MRO Service Order in Draft or Cancel State'))
        record_ids = self.mapped('stock_picking_ids')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('stock.action_picking_tree_all')
        list_view_id = imd.xmlid_to_res_id('stock.vpicktree')
        form_view_id = imd.xmlid_to_res_id('stock.view_picking_form')

        result = {
            'name': _('Stock Pickings related to MRO Service Order %s') % (self.name),
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        result['context'] = "{'default_for_fleet_mro_order':True, 'default_mro_order_id': %s, 'search_default_mro_order_id': [%s], 'default_picking_type_id':%s}" % (self.id, self.id, self.mro_type_id.stock_picking_type.id)
        result['domain'] = "[('mro_order_id','=',%s)]" % self.id
        return result


    @api.multi
    def action_view_tasks(self):
        record_ids = self.mapped('task_ids')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('fleet_mro.fleet_mro_order_task_action')
        list_view_id = imd.xmlid_to_res_id('fleet_mro.fleet_mro_order_task_tree')
        form_view_id = imd.xmlid_to_res_id('fleet_mro.fleet_mro_order_task_form')

        result = {
            'name': _('Tasks related to MRO Service Order %s') % (self.name),
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        result['context'] = result['context'][:-1] + ",'default_order_id': %s, 'search_default_order_id': [%s]}" % (self.id, self.id)
        """
        if len(record_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % record_ids.ids
        elif len(record_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = record_ids.ids[0]
        """
        return result

    
    @api.multi
    def action_view_driver_reports(self):
        record_ids = self.mapped('fleet_mro_driver_report_ids') 
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('fleet_mro.open_view_fleet_mro_driver_report_form')
        list_view_id = imd.xmlid_to_res_id('fleet_mro.view_fleet_mro_driver_report_tree')
        form_view_id = imd.xmlid_to_res_id('fleet_mro.view_fleet_mro_driver_report_form')

        result = {
            'name': _('Drivers Report of Failure related to Service Order %s') % (self.name),
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        result['context'] = result['context'][:-1] + ",'default_order_id': %s, 'search_default_order_id': [%s]}" % (self.id, self.id)
        result['domain'] = "[('order_id','=',%s)]" % self.id
        return result
    
    
    @api.multi
    def action_view_task_times(self):
        record_ids = self.mapped('task_ids.control_time_ids')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('fleet_mro.fleet_mro_order_task_time_action')
        list_view_id = imd.xmlid_to_res_id('fleet_mro.view_fleet_mro_order_task_time_tree')
        form_view_id = imd.xmlid_to_res_id('fleet_mro.view_fleet_mro_order_task_time_form')

        result = {
            'name': _('Tasks Time Sheets related to MRO Service Order %s') % (self.name),
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        result['context'] = result['context'][:-1] + ",'default_order_id': %s, 'search_default_order_id': [%s]}" % (self.id, self.id)
        result['domain'] = "[('order_id','=',%s)]" % self.id
        return result


    @api.multi
    def action_view_invoice(self):
        self.ensure_one()
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
        action['res_id'] = self.invoice_id.id
        return action


    def get_tasks_from_cycle(self, cycle, date):
        task_ids = self.task_ids.browse([])
        for task in cycle.task_ids:
            task_data = task_ids.new({'task_id'      : task.id,
                                       'breakdown'    : True,
                                       'date_start'   : date,
                                       'date_end'     : date,
                                       'state'       : 'pending',
                                    })
            task_data.on_change_task_id()
            task_ids += task_data
        for sub_cycle in cycle.cycle_ids:
            task_ids = task_ids + self.get_tasks_from_cycle(sub_cycle, date)
        return task_ids

    @api.multi
    def action_schedule(self):
        self.write({'state':'scheduled','dummy':False})
        return True
    

    @api.multi
    def action_check_in(self):
        self.write({'state':'check_in','dummy':False})
        return True
    
    
    @api.multi
    def action_revision(self):
        self.write({'state':'revision','dummy':False})
        return True
    
    
    @api.multi
    def action_waiting_approval(self):
        self.write({'state':'waiting_approval','dummy':False})    
        return True
    
    
    @api.multi
    def action_open(self):
        self.write({'state':'open','date_start_real':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}) 
        
        for order in self:
            if not order.task_ids:
                raise UserError(_('Warning! \n\nYou can not set to Open State a MRO Service Order without Tasks'))
            for task in order.task_ids:
                if task.state == 'pending':
                    task.action_process()
            if order.spares_quotation_line_ids:
                picking_obj = self.env['stock.picking']
                vals = {'mro_order_id'      : order.id,
                        'for_fleet_mro_order' : True,
                        'origin'            : order.name,
                        'mechanic_id'       : order.supervisor_id.id,
                        'picking_type_id'   : order.mro_type_id.stock_picking_type.id,
                        'location_id'       : order.mro_type_id.stock_picking_type.default_location_src_id.id,
                        'location_dest_id'  : order.mro_type_id.stock_picking_type.default_location_dest_id.id,                          
                        
                       }
                stock_moves = []
                for spare in order.spares_quotation_line_ids:
                    sm = {'mro_order_id': order.id,
                          'mro_task_id' : spare.task_id.id,
                          'name'        : spare.name,
                          'product_id'  : spare.product_id.id,
                          'product_uom_qty' : spare.product_uom_qty,
                          'product_uom'     : spare.product_uom.id,
                          'location_id'     : order.mro_type_id.stock_picking_type.default_location_src_id.id,
                          'location_dest_id': order.mro_type_id.stock_picking_type.default_location_dest_id.id,                          
                         }
                    stock_moves.append((0,0,sm))
                if stock_moves:
                    vals.update({'move_lines':stock_moves})
                picking_res = picking_obj.create(vals)                
        return True

    @api.multi
    def action_reopen(self):
        if self.invoice_id and self.invoice_id.state !='cancel':
            raise UserError(_('Warning !!!\nYou can not Re-Open this record because is already invoiced, You have to Cancel Invoice record so you can re-open it.'))
        self.write({'state':'open','dummy':False})
        return True
    
    @api.multi
    def action_draft(self):
        self.write({'state':'draft','dummy':False})
        return True
    
    
    @api.multi
    def action_cancel(self):
        for order in self:
            order.task_ids.action_cancel()
        self.write({'state':'cancel','dummy':False})
        return True

    
    @api.multi
    def action_release(self):
        for order in self:
            order.task_ids.action_done()
        # self.write({'state':'released','dummy':False})
        self.write({'state':'released','dummy':False,'date_end_real':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        return True

    @api.multi
    def action_done(self):
        program_obj = self.env['fleet.vehicle.mro_program']
        for order in self:
            if order.mro_program_id.id:
                order.vehicle_id.write({'last_preventive_service': order.id})
                prog_id = program_obj.search([('vehicle_id', '=', order.vehicle_id.id), ('sequence','=', order.program_sequence)])
                if prog_id:
                    prog_id.write({'order_id':order.id})
                    service_trigger = order.accumulated_odometer
                    diference = prog_id.diference
                    prog_ids = program_obj.search([('vehicle_id', '=', order.vehicle_id.id), ('sequence','>', order.program_sequence)], order='sequence')
                    x = 0
                    for rec in prog_ids:
                        prog_next_trigger = rec.trigger + diference
                        rec.write({'trigger' : prog_next_trigger})
                        if not x:
                            order.vehicle_id.write({'cycle_next_service': rec.cycle_id.id, 
                                                    'main_odometer_next_service': prog_next_trigger, 
                                                    'odometer_next_service'  : order.current_odometer + (rec.trigger + diference), 
                                                    'sequence_next_service'  : rec.sequence,
                                                   })
                        x += 1
                        service_trigger = prog_next_trigger
                order.vehicle_id.get_next_service_date()
                        
        
        # self.write({'state':'done', 'date_end_real':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        self.write({'state':'done'})
        return True     
    
    
    @api.multi
    def write(self, vals):
        if vals.keys() == ['state']:
            for rec in self:
                if rec.state=='open' and vals['state']=='draft':
                    raise UserError(_('Warning !!! You can not change Service Order %s from Open to Draft State') % rec.name)            
        return super(fleet_mro_order, self).write(vals)    
    
    
    
    @api.multi
    def _prepare_invoice(self):
        self.ensure_one()
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))
        invoice_vals = {
            'name'          : self.client_order_ref or '',
            'origin'        : self.name,
            'type'          : 'out_invoice',
            'account_id'    : self.partner_invoice_id.property_account_receivable_id.id,
            'partner_id'    : self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_id.id,
            'journal_id'    : journal_id,
            'currency_id'   : self.pricelist_id.currency_id.id,
            'comment'       : self.note,
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
            'company_id'    : self.company_id.id,
            'user_id'       : self.user_id and self.user_id.id,
            'team_id'       : self.team_id.id
        }
        return invoice_vals    
    
    

    
    @api.multi
    def action_invoice_create(self):
        """
        Create the invoice associated to the MRO Service Order.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        inv_obj = self.env['account.invoice']
        inv_line_obj = self.env['account.invoice.line']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        references = {}
        for order in self.filtered(lambda r: r.state == 'done' and (not r.invoice_id or r.invoice_id.state=='cancel')):
            group_key = (order.partner_invoice_id.id, order.currency_id.id)
            for task in order.task_ids.filtered(lambda r: r.state == 'done'):
                if float_is_zero(task.product_uom_qty, precision_digits=precision):
                    continue
                if group_key not in invoices:
                    inv_data = order._prepare_invoice()
                    invoice = inv_obj.create(inv_data)
                    references[invoice] = order
                    invoices[group_key] = invoice
                elif group_key in invoices:
                    vals = {}
                    if order.name not in invoices[group_key].origin.split(', '):
                        vals['origin'] = invoices[group_key].origin + ', ' + order.name
                    if order.client_order_ref and order.client_order_ref not in invoices[group_key].name.split(', '):
                        vals['name'] = invoices[group_key].name + ', ' + order.client_order_ref
                    invoices[group_key].write(vals)
                if task.product_uom_qty > 0:
                    vals = task._prepare_invoice_line(qty=task.product_uom_qty)
                    vals.update({'invoice_id': invoices[group_key].id})
                    res = inv_line_obj.create(vals)
                    
                    if task.spares_quotation_line_ids.filtered(lambda r: r.qty_to_invoice > 0.0):
                        for spare in task.spares_quotation_line_ids.filtered(lambda r: r.qty_to_invoice > 0.0):
                            vals = spare._prepare_invoice_line(qty=spare.qty_to_invoice)
                            vals.update({'invoice_id': invoices[group_key].id})
                            res = inv_line_obj.create(vals)
            order.write({'invoice_id':invoices[group_key].id})
            
            if references.get(invoices.get(group_key)):
                if order not in references[invoices[group_key]]:
                    references[invoice] = references[invoice] | order

        if not invoices:
            raise UserError(_('There is no invoicable line.'))

        for invoice in invoices.values():
            if not invoice.invoice_line_ids:
                raise UserError(_('There is no invoicable line.'))
            # If invoice is negative, do a refund invoice instead
            #if invoice.amount_untaxed < 0:
            #    invoice.type = 'out_refund'
            #    for line in invoice.invoice_line_ids:
            #        line.quantity = -line.quantity
            # Use additional field helper function (for account extensions)
            for line in invoice.invoice_line_ids:
                line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
            invoice.compute_taxes()
            invoice.message_post_with_view('mail.message_origin_link',
                values={'self': invoice, 'origin': references[invoice]},
                subtype_id=self.env.ref('mail.mt_note').id)
        return [inv.id for inv in invoices.values()]


        
class fleet_mro_order_invoice_wizard(models.TransientModel):
    _name = 'fleet.mro.order.invoice_wizard'
    _description = 'Create Invoices for Customer'
                                   
                                   
    @api.multi
    def button_create_invoices(self):
        order_obj = self.env['fleet.mro.order']
        record_ids =  self._context.get('active_ids',[])
                                   
        orders = order_obj.browse(record_ids)    
        invoice_ids = self.env['account.invoice'].browse(orders.action_invoice_create())
        imd_obj = self.env['ir.model.data']
        action = imd_obj.xmlid_to_object('account.action_invoice_tree')
        list_view_id = imd_obj.xmlid_to_res_id('account.invoice_tree')
        form_view_id = imd_obj.xmlid_to_res_id('account.invoice_form')

        result = {
            'name': _('MRO Service Order Invoices'),
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        
        if len(invoice_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % invoice_ids.ids
        elif len(invoice_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = invoice_ids.ids[0]
        return result
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
