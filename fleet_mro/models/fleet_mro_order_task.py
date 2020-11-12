# -*- encoding: utf-8 -*-
from openerp import api, fields, models, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError
import openerp.addons.decimal_precision as dp
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, date, timedelta
import time
import pytz

class fleet_mro_order_task(models.Model):
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _name = 'fleet.mro.order.task'
    _description = 'MRO Service Order Task'
    #_rec_name='product_id'

    """
    @api.multi
    @api.depends('invoice_id', 'invoice_id.state')
    def _supplier_invoiced(self):
        for record in self:
            record.supplier_invoiced = bool(record.invoice_id.id)
            record.supplier_invoice_paid = (record.invoice_id.state == 'paid') if record.invoice_id.id else False
            record.supplier_invoice_name = record.invoice_id.reference or record.invoice_id.number
    
    """
    @api.multi
    @api.depends('state','stock_move_ids.state','purchase_order_line_ids.order_id.state','control_time_ids.state','spares_quotation_line_ids.price_subtotal')
    def _get_resume(self):
        for rec in self:
            spares, manpower, spares_ext, manpower_ext, hours_real, income_spares = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
            for xline in rec.stock_move_ids.filtered(lambda r: r.state == 'done'):
                if xline.location_id.usage =='supplier' and xline.location_dest_id.usage in ('production','inventory','customer'): # Compra de refacciones para Taller Externo
                    spares_ext += (xline.price_unit * xline.product_uom_qty)
                elif xline.location_dest_id.usage =='supplier' and xline.location_id.usage in ('production','inventory','customer'): # Devolución de Compra de refacciones para Taller Externo
                    spares_ext -= (xline.price_unit * xline.product_uom_qty)
                elif xline.location_id.usage =='internal' and xline.location_dest_id.usage in ('production','inventory','customer'): # Salidas de Inventario
                    spares += (xline.price_unit * xline.product_uom_qty)
                elif xline.location_dest_id.usage =='internal' and xline.location_id.usage in ('production','inventory','customer'): # Devoluciones de Inventario
                    spares -= (xline.price_unit * xline.product_uom_qty)                

            for purchase_line in rec.purchase_order_line_ids:
                if purchase_line.order_id.state in ('purchase', 'done'):
                    if purchase_line.product_id.type=='service':
                        manpower_ext += purchase_line.price_subtotal
                    #else:    
                    #    spares_ext += purchase_line.price_subtotal
            for line in rec.control_time_ids:                
                manpower += line.amount
                hours_real += line.hours_mechanic
            
            for spare in rec.spares_quotation_line_ids:
                income_spares += spare.price_subtotal_2_invoice
            
            rec.update({
                'income_spares'     : income_spares,
                'amount_untaxed'    : (rec.price_subtotal + income_spares),
                'parts_cost'        : spares,
                'cost_service'      : manpower,
                'parts_cost_external' : spares_ext,
                'cost_service_external' : manpower_ext,
                'cost_internal'     : spares + manpower,
                'cost_external'     : spares_ext + manpower_ext,
                'cost_all'          : spares + manpower + spares_ext + manpower_ext,
                'profit_loss'       : (income_spares + rec.price_subtotal) -  (spares + manpower + spares_ext + manpower_ext),
                'hours_real'        : hours_real,
                })
   

    @api.depends('state', 'product_uom_qty')  #, 'qty_delivered', 'qty_to_invoice', 'qty_invoiced')
    def _compute_invoice_status(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if line.state not in ('done'):
                line.invoice_status = 'no'
            elif line.state == 'done' and (not line.invoice_id or line.invoice_id.state=='cancel'):
                line.invoice_status = 'to invoice'
            elif line.state=='done' and line.invoice_id and line.invoice_id.state!='cancel':
                line.invoice_status = 'invoiced'
            #elif not float_is_zero(line.qty_to_invoice, precision_digits=precision):
            #    line.invoice_status = 'to invoice'
            #elif float_compare(line.qty_invoiced, line.product_uom_qty, precision_digits=precision) >= 0:
            #    line.invoice_status = 'invoiced'
            else:
                line.invoice_status = 'no'   


    @api.depends('product_uom_qty', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the line.
        """
        for line in self:
            if line.order_id.internal_repair:
                line.update({
                    'price_tax': 0.0,
                    'price_total': 0.0,
                    'price_subtotal': 0.0,
                })
            else:
                price = line.price_unit
                taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.task_id, partner=line.order_id.partner_id)
                line.update({
                    'price_tax': taxes['total_included'] - taxes['total_excluded'],
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })


    @api.depends('task_id', 'date_start')
    def _compute_date_end(self):
        for line in self:
            delta = timedelta(hours=(line.task_id.duration or 1))
            origin = datetime.strptime(line.date_start, '%Y-%m-%d %H:%M:%S')
            end_date = origin + delta
            line.date_end = end_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            

    state           = fields.Selection([('cancel','Cancelled'), 
                                        ('pending','To Do'), 
                                        ('process','In Process'),
                                        ('unattended','Pending'), 
                                        ('done','Done')], 
                                       string='State', default='pending', track_visibility='onchange', store=True)

    state_order     = fields.Selection([('cancel','Cancelled'), 
                                         ('draft','Draft'), 
                                         ('open','Open'), 
                                         ('released','Released'), 
                                         ('done','Done')], related='order_id.state', string='State Order', readonly=True)

    date_start      = fields.Datetime(string='Scheduled Date Start', required=True, track_visibility='onchange', 
                                      readonly=False, states={'done':[('readonly',True)],'cancel':[('readonly',True)]},
                                      # default=time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                                      default=fields.Datetime.now,
                                      )
    date_end        = fields.Datetime(string='Scheduled Date End', compute='_compute_date_end', readonly=True)
    date_start_real = fields.Datetime(string='Date Start Real', readonly=True, track_visibility='onchange')
    date_end_real   = fields.Datetime(string='Date End Real', readonly=True, track_visibility='onchange')
    date_most_recent_end_mechanic_task = fields.Datetime(string='Scheduled Most Recent Task End of Mechanic')

    product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True, 
                                   readonly=False, states={'done':[('readonly',False)],'cancel':[('readonly',True)]},
                                   default=1.0)
    product_uom     = fields.Many2one('product.uom', string='Unit of Measure', required=True,
                                     readonly=False, states={'done':[('readonly',True)],'cancel':[('readonly',True)]})
    tax_id          = fields.Many2many('account.tax', string='Taxes', 
                                       domain=['|', ('active', '=', False), ('active', '=', True),('type_tax_use','=','sale')],
                                       readonly=False, states={'done':[('readonly',True)],'cancel':[('readonly',True)]})
    price_unit      = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0,
                                   readonly=False, states={'done':[('readonly',True)],'cancel':[('readonly',True)]})

    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Monetary(compute='_compute_amount', string='Taxes', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)


    hours_estimated = fields.Float(string='Hours Est.', readonly=True)
    hours_real      = fields.Float(compute='_get_resume' , string='Hours Real', readonly=True, store=True)

    parts_cost      = fields.Float(compute='_get_resume', string='Spare Parts', store=True, digits=dp.get_precision('Product Price'))
    cost_service    = fields.Float(compute='_get_resume', string='Manpower', store=True, digits=dp.get_precision('Product Price'))
    cost_service_external = fields.Float(compute='_get_resume', string='Service Cost External', store=True, digits=dp.get_precision('Product Price'))
    parts_cost_external   = fields.Float(compute='_get_resume', string='Spare Parts External', store=True, digits=dp.get_precision('Product Price'))
    cost_internal   = fields.Float(compute='_get_resume', string='Cost Internal', store=True, digits=dp.get_precision('Product Price'))
    cost_external   = fields.Float(compute='_get_resume', string='Cost External', store=True, digits=dp.get_precision('Product Price'))
    cost_all        = fields.Float(compute='_get_resume', string='All Costs', store=True, digits=dp.get_precision('Product Price'))
    profit_loss     = fields.Float(compute='_get_resume', string='Profit/Loss', store=True, digits=dp.get_precision('Product Price'))
    amount_untaxed  = fields.Float(compute='_get_resume', string='Amount Task', store=True, digits=dp.get_precision('Product Price'))
    income_spares   = fields.Float(compute='_get_resume', string='Income Spares', store=True, digits=dp.get_precision('Product Price'))
    
    external_workshop = fields.Boolean(string='External Workshop', track_visibility='onchange', 
                                       readonly=False, states={'done':[('readonly',True)],'cancel':[('readonly',True)]},
                                       help="Check if this task is going to be done by an external supplier")
    breakdown       = fields.Boolean(string='Breakdown', default=True)

    name            = fields.Text(string='Description', required=True,
                                  readonly=False, states={'done':[('readonly',True)],'cancel':[('readonly',True)]})
    sequence        = fields.Integer(string='Sequence', default=10,
                                     readonly=False, states={'done':[('readonly',True)],'cancel':[('readonly',True)]})

    ######## Many2One ##########################
    task_id         = fields.Many2one('product.product', string='Task', required=True, ondelete='restrict', 
                                      track_visibility='onchange', domain=[('fleet_mro_task', '=', True)],
                                      readonly=False, states={'done':[('readonly',True)],'cancel':[('readonly',True)]})
    spares_quotation_line_ids = fields.One2many('fleet.mro.order.task.spares_quotation', 'task_id', 
                                                string="Spare Parts Quotation", readonly=True)
    ######## Many2One request One2Many ##########
    order_id        = fields.Many2one('fleet.mro.order', string='Service Order', readonly=True, ondelete='restrict')
    currency_id     = fields.Many2one(related='order_id.currency_id', store=True, string='Currency', readonly=True)
    company_id      = fields.Many2one(related='order_id.company_id', string='Company', store=True, readonly=True)    
    internal_repair = fields.Boolean(string='Internal Repair', related="order_id.internal_repair", store=True,
                                    readonly=True)
    ######## Many2Many ##########################
    mechanic_ids    = fields.Many2many('hr.employee','fleet_mro_order_task_rel','task_id','employee_id', track_visibility='onchange', 
                                       readonly=False, states={'done':[('readonly',True)],'cancel':[('readonly',True)]},
                                       string='Mechanics', domain=[('fleet_mro_mechanic', '=', True)])
    ######## One2Many ###########################
    purchase_order_line_ids  = fields.One2many('purchase.order.line','mro_task_id',string='External Workshop Detailed')
    #purchase_order_ids  = fields.One2many('purchase.order','mro_task_id',string='External Workshop')
    stock_move_ids      = fields.One2many('stock.move','mro_task_id',string='Stock Moves', readonly="True")
    control_time_ids    = fields.One2many('fleet.mro.order.task.time','task_id', string='Time Sheet')
    ########Related ###########
    operating_unit_id       = fields.Many2one('operating.unit', related='order_id.operating_unit_id', 
                                              string='Operating Unit', store=True, readonly=True)
    vehicle_id      = fields.Many2one('fleet.vehicle', related='order_id.vehicle_id', string='Vehicle', store=True, readonly=True)
    dummy_field     = fields.Boolean(string='Dummy')
    #invoice_status = fields.Selection([ ('to invoice', 'To Invoice'),
    #                                    ('invoiced', 'Fully Invoiced'),
    #                                    ('partial', 'Partially Invoiced'),
    #                                    ('no', 'Nothing to Invoice')
    #                                    ], string='Invoice Status', compute='_compute_invoice_status', store=True, readonly=True)
    
    #invoice_id      = fields.Many2one('account.invoice', string='Invoice', readonly=True)
    
    @api.one
    @api.constrains('order_id', 'state')
    def _check_task_state(self):
        if self.order_id.state == 'released' and not self.state in ('done','cancel'):
            raise UserError(_("Error ! You can not create Tasks in MRO Service Order if it's in Released State, please delete any Task recently added to be able to save changes"))

    @api.one
    @api.constrains('task_id', 'order_id')            
    def _check_for_duplicate_task(self):
        if [task.id for task in self.order_id.task_ids if task.id != self.id and task.task_id.id == self.task_id.id]:
            raise UserError(_("Error ! You can not create Duplicate Tasks, please delete any Task recently added to be able to save changes"))


    @api.multi
    def _get_display_price(self, product):
        if self.order_id.pricelist_id.discount_policy == 'without_discount':
            from_currency = self.order_id.company_id.currency_id
            return from_currency.compute(product.lst_price, self.order_id.pricelist_id.currency_id)
        return product.with_context(pricelist=self.order_id.pricelist_id.id).price
            

    @api.onchange('task_id', 'date_start')
    def on_change_task_id(self):
        res = [x.id for x in self.order_id.vehicle_id.model_id.task_ids] or [0]
        for task in self.env['product.product'].search([('fleet_mro_task','=','True'),('fleet_vehicle_model_ids','=',False),('id','not in', res)]):
            res.append(task.id)
        domain = {'task_id': [('id', 'in', res)]}
        if not self.task_id:
            domain.update({'product_uom': []})
            return {'domain': domain}
            
        delta = timedelta(hours=(self.task_id.duration or 1))
        origin = datetime.strptime(self.date_start, '%Y-%m-%d %H:%M:%S')
        end_date = origin + delta
        self.date_end = end_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        self.hours_estimated = self.task_id.duration
        self.product_uom_qty = 1 #self.task_id.duration      

        vals = {}
        domain.update({'product_uom': [('category_id', '=', self.task_id.uom_id.category_id.id)]})
        if not self.product_uom or (self.task_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.task_id.uom_id

        task = self.task_id.with_context(
                                lang        = self.order_id.partner_id.lang,
                                partner     = self.order_id.partner_id.id,
                                quantity    = vals.get('product_uom_qty') or self.product_uom_qty,
                                date        = self.order_id.date,
                                pricelist   = self.order_id.pricelist_id.id,
                                uom         = self.product_uom.id
                            )
        product = self.task_id
        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id and not self.order_id.internal_repair:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price(self._get_display_price(product), product.taxes_id, self.tax_id)
        self.update(vals)
        title = False
        message = False
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            if product.sale_line_warn == 'block':
                self.task_id = False
            return {'warning': warning}
        return {'domain': domain}


    @api.multi
    def _compute_tax_id(self):
        for line in self:
            fpos = line.order_id.fiscal_position_id or line.order_id.partner_id.property_account_position_id
            # If company_id is set, always filter taxes by the company
            taxes = line.task_id.taxes_id.filtered(lambda r: not line.company_id or r.company_id == line.company_id)
            line.tax_id = fpos.map_tax(taxes, line.task_id, line.order_id.partner_id) if fpos else taxes


    @api.multi
    def action_view_purchase_orders(self):
        rec_ids = self.mapped('purchase_order_line_ids')
        record_ids = []
        if rec_ids:
            res = self._cr.execute("select distinct order_id from purchase_order_line where id IN %s", (tuple(rec_ids),))
            record_ids = filter(None, map(lambda x:x[0], self._cr.fetchall()))

        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('fleet_mro.fleet_mro_purchase_form_action')
        list_view_id = imd.xmlid_to_res_id('purchase.purchase_order_tree')
        form_view_id = imd.xmlid_to_res_id('purchase.purchase_order_form')

        result = {
            'name': _('External Workshop for MRO Service Order %s including Task: %s') % (self.order_id.name, self.name),
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        result['context'] = "{'default_fleet_mro_related': %s, 'default_mro_order_id': %s, 'default_mro_task_id': %s, 'search_default_mro_task_id': [%s], 'default_picking_type_id': %s}" % (True, self.order_id.id, self.id, self.id, self.order_id.mro_type_id.id)
        result['domain'] = "[('id','in',%s)]" % record_ids
        #if len(record_ids) > 1:
        #    result['domain'] = "[('id','in',%s)]" % record_ids.ids
        #elif len(record_ids) == 1:
        #    result['views'] = [(form_view_id, 'form')]
        #    result['res_id'] = record_ids.ids[0]
        return result

    
    @api.onchange('external_workshop')
    def on_change_external_workshop(self):
        self.breakdown = not self.external_workshop
            
    @api.multi
    def unlink(self):
        for task in self:
            if task.state!='cancel':
                raise UserError(_('Warning!\nYou can not delete Tasks unless they are Cancelled')) 
        return super(fleet_mro_order_task, self).unlink()


    @api.multi        
    def action_process(self):
        for task in self:
            if task.order_id.state != 'open':
                raise UserError(_('Warning!\nYou can only change Task to Process State when MRO Service Order is in Open State')) 
            band = task.external_workshop or bool(task.mechanic_ids)
            if not band:
                raise UserError(_('Warning!\nYou can only change Task to Process State when it has assigned Mechanic'))
            task.write({'state'           : 'process',
                        'date_start_real' : time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                        'hours_estimated' : task.task_id.duration,
                       })
            task.stock_move_ids.action_confirm()
            for mechanic in task.mechanic_ids:
                vals = {'order_id'  : task.order_id.id,
                        'task_id'   : task.id,
                        'name_order': task.order_id.name,
                        'name_task' : task.task_id.name,
                        'hr_employee_id': mechanic.id,
                        'hr_employee_user_id' : mechanic.user_id.id,
                       }
                control_time_id  = self.env['fleet.mro.order.task.time'].create(vals)                
        return True

    
    @api.multi
    def action_cancel(self):
        for task in self:
            if task.state=='done':
                raise UserError(_('Warning! \n\nYou can not Cancel a MRO Service Order with Tasks in Done State'))
            if any(stock_move.state == 'done' for stock_move in task.stock_move_ids):
                UserError(_('Warning!\n\nYou can not cancel Task if there are Stock Moves related to task %s') % (task.name)) 
            task.stock_move_ids.action_cancel()
            task.control_time_ids.action_cancel()
        self.write({'state':'cancel'})
        return True

    @api.multi
    def action_done(self):
        for task in self:
            ## Check if any Purchase Order is in Draft State
            if any(purchase_line.order_id.state in ('draft') for purchase_line in task.purchase_order_line_ids):
                raise UserError(_('Warning!\nAll Purchase Order for External Workshop must be Confirmed'))
            for mechanic_task in task.control_time_ids:
                if mechanic_task.state !='done':
                    raise UserError(_('Warning!\nAll Mechanics Tasks must be Ended'))
            if not any(stock_move.state in ('pending','delivered') for stock_move in task.stock_move_ids):
                for line in task.stock_move_ids:
                    if line.state == 'draft':
                        line.action_cancel()
        
            task.write({'state':'done', 'date_end_real' : task.date_most_recent_end_mechanic_task})
        return True
    
    @api.one
    def set_task_as_done_if_posible(self):
        if any(x.state != 'done' for x in self.control_time_ids):
            return False
        #######################################################################
        if not any(pl.state in ('pending','delivered') for pl in self.stock_move_ids):
            for line in self.stock_move_ids:
                if line.state == 'draft':
                    line.action_cancel()
            self.write({'state':'done','date_end_real':self.date_most_recent_end_mechanic_task})
        return True


    
    @api.multi
    def _prepare_invoice_line(self, qty):
        self.ensure_one()
        res = {}
        account = self.task_id.property_account_income_id or self.task_id.categ_id.property_account_income_categ_id
        if not account:
            raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                (self.task_id.name, self.task_id.id, self.task_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)

        res = {
            'name': _('Task: ') + self.name,
            'sequence': self.sequence,
            'origin': self.order_id.name,
            'account_id': account.id,
            'price_unit': self.price_unit,
            'quantity': qty,
            #'discount': self.discount,
            'uom_id': self.product_uom.id,
            'product_id': self.task_id.id or False,
            #'layout_category_id': self.layout_category_id and self.layout_category_id.id or False,
            #'product_id': self.product_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            #'account_analytic_id': self.order_id.project_id.id,
            #'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
        }
        return res    
        
    

# Wizard que permite asignar Mecánicos a una o varias Tareas a la vez
class fleet_mro_order_task_assign_manpower(models.TransientModel):

    _name = 'fleet.mro.order.task.assing_manpower'
    _description = 'Assign internal Manpower to several Tasks'

    mechanic_ids = fields.Many2many('hr.employee', string='Mechanics', required=True,
                                    domain=[('fleet_mro_mechanic', '=', True)])  

    @api.multi
    def assign_manpower(self):
        rec_ids =  self._context.get('active_ids',[])
        task_ids = self.env['fleet.mro.order.task'].search([('id','in',tuple(rec_ids),),('state','=', 'pending')])
        if not task_ids:
            raise UserError(_('Warning !\nPlease select at least one Task in Pending state to assign manpower')) 
        mechanic_ids = [x.id for x in self.mechanic_ids]
        if not mechanic_ids:
            raise UserError(_('Warning !\nPlease select at least one Mechanic or Technical Staff to assign manpower to selected Tasks'))

        for record in task_ids:
            mechanics = [x.id for x in record.mechanic_ids]
            for mechanic_id in mechanic_ids:
                if mechanic_id not in mechanics:
                    mechanics.append(mechanic_id)
            if mechanics != [x.id for x in record.mechanic_ids]:
                record.write({'mechanic_ids': [(6, 0, [x for x in mechanics])]})
        return {'type': 'ir.actions.act_window_close'}



    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
