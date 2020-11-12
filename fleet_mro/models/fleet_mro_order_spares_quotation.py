# -*- encoding: utf-8 -*-
from openerp import api, fields, models, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError
import openerp.addons.decimal_precision as dp
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from pytz import timezone
import pytz
import time
import logging
_logger = logging.getLogger(__name__)


class FleetMROOrderTaskSparesQuotation(models.Model):
    _name = 'fleet.mro.order.task.spares_quotation'
    _description = "Spares Quotation for Fleet MRO Customer"
    
    
    @api.depends('product_uom_qty', 'price_unit', 'tax_id', 'qty_to_invoice')
    def _compute_amount(self):
        """
        Compute the amounts of the line.
        """
        for line in self:
            price = line.price_unit
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_invoice_id)
            line.update({
                'price_tax'     : taxes['total_included'] - taxes['total_excluded'],
                'price_total'   : taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.qty_to_invoice, product=line.product_id, partner=line.order_id.partner_invoice_id)
            line.update({
                'price_tax_2_invoice'      : taxes['total_included'] - taxes['total_excluded'],
                'price_total_2_invoice'    : taxes['total_included'],
                'price_subtotal_2_invoice' : taxes['total_excluded'],
            })
    
    
    order_id        = fields.Many2one('fleet.mro.order', string='Service Order', ondelete='cascade')
    state           = fields.Selection([('cancel','Cancelled'), 
                                             ('draft','Draft'),
                                             ('scheduled','Scheduled'),
                                             ('check_in','Check In'),
                                             ('revision','Revision'),
                                             ('waiting_approval','Waiting Approval'),
                                             ('open','Open'), 
                                             ('released','Released'),
                                             ('done','Done')], 
                                       related='order_id.state', store=True, string='State')
    task_id         = fields.Many2one('fleet.mro.order.task', string='Task', ondelete='cascade', required=True,
                                      states={'draft':[('readonly',False)]})
    product_id      = fields.Many2one('product.product', string='Product',  states={'draft':[('readonly',False)]},
                                        domain=[('type', '=', 'product')], ondelete='restrict')
    name            = fields.Text(string='Description', required=True,
                                  states={'draft':[('readonly',False)],'open':[('readonly',False)],'released':[('readonly',False)]})
    product_uom_qty = fields.Float(string='Quoted Quantity', digits=dp.get_precision('Product Unit of Measure'), default=1.0,
                                   required=True,  states={'draft':[('readonly',False)]})
    product_uom     = fields.Many2one('product.uom', string='Unit of Measure', required=True,
                                       states={'draft':[('readonly',False)]})
    tax_id          = fields.Many2many('account.tax', string='Taxes', 
                                       domain=['|', ('active', '=', False), ('active', '=', True),('type_tax_use','=','sale')],
                                        states={'draft':[('readonly',False)],'open':[('readonly',False)],'released':[('readonly',False)]})
    price_unit      = fields.Float('Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0,
                                    states={'draft':[('readonly',False)],'open':[('readonly',False)],'released':[('readonly',False)]})
    price_subtotal  = fields.Monetary(compute='_compute_amount', string='Subtotal Quoted', store=True)
    price_tax       = fields.Monetary(compute='_compute_amount', string='Taxes Quoted',  store=True)
    price_total     = fields.Monetary(compute='_compute_amount', string='Total Quoted',  store=True)
    price_subtotal_2_invoice  = fields.Monetary(compute='_compute_amount', string='Subtotal Real',  store=True)
    price_tax_2_invoice       = fields.Monetary(compute='_compute_amount', string='Taxes Real', store=True)
    price_total_2_invoice     = fields.Monetary(compute='_compute_amount', string='Total Real',  store=True)
    
    
    currency_id     = fields.Many2one(related='order_id.currency_id', store=True, string='Currency')    
    note            = fields.Text(string="Notes...", states={'draft':[('readonly',False)]})
    company_id      = fields.Many2one(related='order_id.company_id', string='Company', store=True)
    sequence        = fields.Integer(string='Sequence', default=10)
    quoted          = fields.Boolean(string='Quoted', default=True)
    qty_to_invoice  = fields.Float(string='Quantity to Invoice', digits=dp.get_precision('Product Unit of Measure'), default=0.0,
                                   required=True)
    stock_move_ids  = fields.One2many('stock.move', 'mro_task_spare_id', string="Stock Moves")
    
    @api.onchange('product_id','product_uom')
    def on_change_product_id(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id

        product = self.product_id.with_context(
                                lang        = self.order_id.partner_id.lang,
                                partner     = self.order_id.partner_id.id,
                                quantity    = vals.get('product_uom_qty') or self.product_uom_qty,
                                date        = self.order_id.date,
                                pricelist   = self.order_id.pricelist_id.id,
                                uom         = self.product_uom.id
                            )
        #product = self.product_id
        print "product.name_get(): ", product.name_get()
        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
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
                self.product_id = False
            return {'warning': warning}
        return {'domain': domain}


    @api.multi
    def _compute_tax_id(self):
        for line in self:
            fpos = line.order_id.fiscal_position_id or line.order_id.partner_id.property_account_position_id
            # If company_id is set, always filter taxes by the company
            taxes = line.product_id.taxes_id.filtered(lambda r: not line.company_id or r.company_id == line.company_id)
            line.tax_id = fpos.map_tax(taxes, line.product_id, line.order_id.partner_id) if fpos else taxes    
    
    @api.multi
    def _get_display_price(self, product):
        if self.order_id.pricelist_id.discount_policy == 'without_discount':
            from_currency = self.order_id.company_id.currency_id
            return from_currency.compute(product.lst_price, self.order_id.pricelist_id.currency_id)
        return product.with_context(pricelist=self.order_id.pricelist_id.id).price    
    
    
    
    @api.multi
    def _prepare_invoice_line(self, qty):
        self.ensure_one()
        res = {}
        account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
        if not account:
            raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)

        res = {
            'name': _('>> Spare >> ') + self.name,
            'sequence': self.sequence,
            'origin': self.order_id.name,
            'account_id': account.id,
            'price_unit': self.price_unit,
            'quantity': qty,
            #'discount': self.discount,
            'uom_id': self.product_uom.id,
            'product_id': self.product_id.id or False,
            #'layout_category_id': self.layout_category_id and self.layout_category_id.id or False,
            #'product_id': self.product_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            #'account_analytic_id': self.order_id.project_id.id,
            #'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
        }
        return res       
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
