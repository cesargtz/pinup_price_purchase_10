# -*- coding: utf-8 -*-
{
    'name': "pinup_price_purchase",

    'description': """
        pin up price in the purchase order
    """,

    'author': "Yecora",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','purchase','truck_reception', 'sale','market_price'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'pinup_price.xml',
        'pinup_purchese_order.xml',
        
    ],
}
