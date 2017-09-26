# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare


class pinupinvocie(models.Model):
    _inherit = 'pinup.price.purchase'

    @api.multi
    def pinup_price(self):
        self.ensure_one()
        try:
            form_id = self.env['ir.model.data'].get_object_reference('account.invoice', 'invoice_supplier_form')[1]
        except ValueError:
            form_id = False

        ctx = dict()
        ctx.update({
            'default_purchase_order_id': self.ids[0],
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'views': [(form_id, 'form')],
            'view_id': form_id,
            #'target': 'new',
            'context': ctx,
        }
