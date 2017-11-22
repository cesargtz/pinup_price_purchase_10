# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from openerp.exceptions import ValidationError
import psycopg2
import logging

_logger = logging.getLogger(__name__)

class pinup_price_purchase(models.Model):
    _inherit = ['mail.thread']
    _name = 'pinup.price.purchase'

    name = fields.Char('Set Price Reference', required=True, select=True, copy=False, default=lambda self: self.env['ir.sequence'].next_by_code('reg_code_price'), help="Unique number of the set prices")
    purchase_order_id = fields.Many2one('purchase.order')
    partner_id = fields.Many2one(
        'res.partner', readonly=True, related="purchase_order_id.partner_id", store=True)
    tons_contract = fields.Float(compute="_compute_tons")
    request_date = fields.Date(required=True, default=fields.Date.today)
    pinup_tons = fields.Float(required=True, eval="False", digits=(12, 3))
    price_bushel = fields.Float(digits=(12, 2))
    bases_ton = fields.Float(compute="_compute_base", inverse="_inverse_base", digits=(12, 3), store=True)
    price_min = fields.Float(compute="_compute_min", inverse="_inverse_min", digits=(12, 2), store=True)
    service = fields.Float(digits=(12, 2))
    cost = fields.Float(compute="_compute_cost", inverse="_inverse_cost", digits=(12, 2), store=True)
    tc = fields.Float(digits=(12, 4))
    price_per_ton = fields.Float(compute="_compute_ton_usd", store=True, digits=(12, 2))
    price_mxn = fields.Float(compute="_compute_mx", store=True, digits=(12, 2))
    tons_reception = fields.Float(
        compute="_compute_tr", digits=(12, 3),  store=True)
    tons_invoiced = fields.Float(
        compute="_compute_ti", digits=(12, 3),  store=True)
    tons_priced = fields.Float(
        compute="_compute_priced", digits=(12, 3),  store=True)
    invoice_create_id = fields.Many2one('account.invoice', readonly=True)

    contract_type = fields.Selection([
        ('axc', 'AxC'),
        ('pf', 'Precio Fijo'),
        ('pm', 'Precio Minimo'),
        ('pd', 'Precio Despues'),
        ('pb', 'Precio Base'),
        ('surplus', 'Excedente'),
        ('na', 'No aplica'),
    ], 'Tipo de contrato', readonly=True, compute="_compute_contract_type", store=True, default='na')


    state = fields.Selection([
        ('draft', "Draft"),
        ('price', "Price"),
        ('currency', "Currency"),
        ('invoiced', "Invoiced"),
        ('close', "Close"),
    ], default='draft')



    @api.one
    @api.depends("purchase_order_id")
    def _compute_tons(self):
        self.tons_contract = self.purchase_order_id.tons_hired

    @api.one
    @api.depends("purchase_order_id","pinup_tons")
    def _compute_contract_type(self):
        if self.tons_priced > (self.tons_contract + .1):
            self.contract_type = "surplus"
            return {
                'warning': {
                    'title': "Toneladas fuera del rango contratado.",
                    'message': "Estas fuera del rango de las toneladas contradadas. usted contrato %s tons. El Tipo de contrato sera precio mínimo" % (self.tons_contract),
                }
            }
        else:
            self.contract_type = self.purchase_order_id.contract_type

    # @api.onchange("pinup_tons")
    # def onchange_tons(self):
    #     if (self.tons_priced + self.pinup_tons) > self.tons_reception:
    #         return {
    #             'warning': {
    #                 'title': "Toneladas no disponibles.",
    #                 'message': "Estas fuera del rango disponible. %s toneladas entregadas." % (self.tons_reception),
    #             }
    #         }

    @api.one
    @api.depends("purchase_order_id")
    def _compute_cost(self):
        if self.purchase_order_id.contract_type == 'pm':
            base = self.env['market.base'].search([], order='id desc', limit=1)
            self.cost = base.cost

    def _inverse_cost(self):
        pass

    @api.one
    @api.depends("purchase_order_id")
    def _compute_base(self):
        if self.purchase_order_id.contract_type == 'pm':
            base = self.env['market.base'].search([], order='id desc', limit=1)
            self.bases_ton = base.base

    def _inverse_base(self):
        pass

    @api.one
    @api.depends("purchase_order_id","price_min")
    def _compute_min(self):
        if self.purchase_order_id.contract_type == 'pm':
            base = self.env['market.base'].search([], order='id desc', limit=1)
            self.price_min = base.price_min

    def _inverse_min(self):
        pass

    @api.multi
    def action_draft(self):
        self.state = 'draft'

    @api.multi
    def action_confirmed(self):
        self.state = 'price'

    @api.multi
    def action_currency(self):
        self.state = 'currency'

    @api.multi
    def action_invoiced(self):
        self.state = 'invoiced'

    @api.multi
    def action_create(self):
        self.state = 'close'

    @api.one
    @api.constrains('pinup_tons','tons_priced','tons_reception')
    def _check_tons(self):
        if self.tons_priced > self.tons_reception:
            raise exceptions.ValidationError("No tienes las suficientes toneladas para preciar.")


    @api.multi
    @api.depends('purchase_order_id')
    def _compute_ti(self):
        tons_billing = 0
        if self.purchase_order_id.invoice_ids:
            for invoice in self.purchase_order_id.invoice_ids:
                if invoice.state in ('open', 'paid'):
                    tons_billing += invoice.tons
            self.tons_invoiced = tons_billing
        else:
            self.tons_invoiced = 0

    @api.one
    @api.depends('purchase_order_id')
    def _compute_tr(self):
        self.tons_reception = self.purchase_order_id.tons_reception

    @api.one
    @api.depends('purchase_order_id')
    def _compute_priced(self):
        for line in self.env['pinup.price.purchase'].search([('purchase_order_id', '=', self.purchase_order_id.name)]):
            self.tons_priced += line.pinup_tons
    @api.one
    @api.depends('price_bushel')
    def _compute_ton_usd(self):
            self.price_per_ton = self.price_bushel * 0.3936825 + self.bases_ton

    @api.one
    @api.depends('price_per_ton','tc')
    def _compute_mx(self):
        if self.price_per_ton >= self.price_min:
            self.price_mxn = self.price_per_ton * self.tc
        else:
            self.price_mxn = self.price_min * self.tc


    @api.multi
    def write(self, vals, recursive=None):
        if not recursive:
            if self.state == 'draft':
                self.write({'state': 'price'}, 'r')
            elif self.state == 'price':
                self.write({'state': 'currency'}, 'r')
            elif self.state == 'currency':
                self.write({'state': 'invoiced'}, 'r')
        res = super(pinup_price_purchase, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        vals['state'] = 'price'
        res = super(pinup_price_purchase, self).create(vals)
        return res

    @api.multi
    def action_create(self):
        invoice_id = self.env['account.invoice'].create({
            'partner_id' : self.partner_id.id,
            'account_id' : self.partner_id.property_account_payable_id.id,
            'journal_id' : self.env['account.journal'].search([('type','=','purchase')], order='id', limit = 1).id,
            'currency_id' : 34,
            'type':'in_invoice',
            'origin' : self.purchase_order_id.name,
            'date_invoice':self.request_date,
            'state':'draft',
            })
        self.create_move_id(invoice_id)
        self.invoice_create_id = invoice_id
        self.state = 'close'


    @api.multi
    def create_move_id(self, invoice_id):
        product = self.purchase_order_id.order_line.product_id
        # iva = product.product_tmpl_id.supplier_taxes_id.id
        move_id = self.env['account.invoice.line'].create({
            'invoice_id': invoice_id.id,
            'price_unit': self.price_mxn,
            'product_id': product[0].id,
            'quantity' : self.pinup_tons,
            'uom_id' : 7,
            'account_id': self.env['account.account'].search([('code','=','111211')]).id,
            'name': product[0].product_tmpl_id.description_purchase,
            'company_id':1,
            'purchase_line_id': self.env['purchase.order.line'].search([('order_id','=',self.purchase_order_id[0].id)]).id,
        })


    @api.onchange('pinup_tons')
    def _onchange_tons(self):
        advance_invoiced = 0
        tons_contract =  self.tons_reception
        for line in self.env['account.invoice'].search([('origin', '=', self.purchase_order_id.name), ('partner_id', '=', self.partner_id.id),('state', 'in', ['open','paid'])]):
            if line.invoice_line_ids.product_id.product_tmpl_id.consider_contract:
                advance_invoiced += line.invoice_line_ids.quantity
        # print(advance_invoiced)
        if (advance_invoiced + self.pinup_tons) > self.tons_reception:
            return {
                'warning': {
                    'title': "Estas tratando de facturar más de lo Entregado.",
                    'message': "Quieres facturar %s tons, pero estan facturadas %s tons. El total disponible es de %s tons" % (self.pinup_tons, advance_invoiced, self.tons_reception),
                }
            }


        # self.env.cr.execute('INSERT INTO account_invoice_line_tax VALUES (%s, %s)',(move_id.id, iva))
