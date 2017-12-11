from openerp import fields, models, api
import logging
logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    pinup_purchase_count = fields.Integer(compute="_pinup_purchase_count")
    split_reception_count = fields.Integer(compute="_split_reception_count")

    @api.multi
    def pinup_price(self):
        self.ensure_one()
        try:
            form_id = self.env['ir.model.data'].get_object_reference('pinup_price_purchase', 'pinup_price_purchase_form_view')[1]
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
            'res_model': 'pinup.price.purchase',
            'views': [(form_id, 'form')],
            'view_id': form_id,
            #'target': 'new',
            'context': ctx,
        }


    # Buttons
    # Preciaciones
    @api.multi
    def _pinup_purchase_count(self):
        for pinup in self:
            count = 0
            for itr in self.env['pinup.price.purchase'].search([('purchase_order_id.id','=', self.id)]):
                count = count + 1
        self.pinup_purchase_count = count

    @api.multi
    def pinup_price_tree(self):
        tree_res = self.env['ir.model.data'].get_object_reference('pinup_price_purchase', 'pinup_price_purchase_tree_view')
        tree_id = tree_res and tree_res[1] or False
        form_res = self.env['ir.model.data'].get_object_reference('pinup_price_purchase', 'pinup_price_purchase_form_view')
        form_id = form_res and form_res[1] or False

        return{
            'type'          :   'ir.actions.act_window',
            'view_type'     :   'form', #Tampilan pada tabel pop-up
            'view_mode'     :   'tree,form', # Menampilkan bagian yang di pop up, tree = menampilkan tabel tree nya utk product
            'res_model'     :   'pinup.price.purchase', #Menampilkan tabel yang akan di show di pop-up screen
            'target'        :   'new', # Untuk menjadikan tampilan prduct yang dipilih menjadi pop-up table tampilan baru, jika dikosongin maka tidak muncul pop-up namun muncul halaman baru.
            'views'         :   [(tree_id, 'tree'),(form_id, 'form')],
            'domain'        :   [('purchase_order_id.id','=', self.id)] #Filter id barang yang ditampilkan
            }


    # Tranferencias parciales
    @api.multi
    def _split_reception_count(self):
        for split in self:
            count = 0
            for itr in self.env['split.receptions'].search([('contract_id.id','=', self.id)]):
                count = count + 1
        self.split_reception_count = count

    @api.multi
    def split_receptions_tree(self):
        tree_res = self.env['ir.model.data'].get_object_reference('split_receptions', 'split_reception_tree_view')
        tree_id = tree_res and tree_res[1] or False
        form_res = self.env['ir.model.data'].get_object_reference('split_receptions', 'split_reception_form_view')
        form_id = form_res and form_res[1] or False

        return{
            'type'          :   'ir.actions.act_window',
            'view_type'     :   'form', #Tampilan pada tabel pop-up
            'view_mode'     :   'tree,form', # Menampilkan bagian yang di pop up, tree = menampilkan tabel tree nya utk product
            'res_model'     :   'split.receptions', #Menampilkan tabel yang akan di show di pop-up screen
            'target'        :   'new', # Untuk menjadikan tampilan prduct yang dipilih menjadi pop-up table tampilan baru, jika dikosongin maka tidak muncul pop-up namun muncul halaman baru.
            'views'         :   [(tree_id, 'tree'),(form_id, 'form')],
            'domain'        :   [('contract_id.id','=', self.id)] #Filter id barang yang ditampilkan
            }
