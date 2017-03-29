# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                        Alexandre Díaz <alex@aloxa.eu>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import openerp
from openerp import api, tools, SUPERUSER_ID
from openerp.osv import osv, fields, expression
import openerp.addons.decimal_precision as dp


class product_product(osv.osv):
    _inherit = 'product.product'

    def _product_lst_price(self, cr, uid, ids, name, arg, context=None):
        res = super(product_product, self)._product_lst_price(cr, uid, ids, name, arg, context=context)

        product_uom_obj = self.pool.get('product.uom')
        product_ids = self.browse(cr, uid, ids, context=context)
        sale_prices = product_ids.get_sale_price(cr, uid, ids, context=context)
        for product in product_ids:
            if 'uom' in context:
                uom = product.uom_id
                res[product.id] = product_uom_obj._compute_price(cr,
                                                                 uid,
                                                                 uom.id,
                                                                 sale_prices[product.id],
                                                                 context['uom'])
            else:
                res[product.id] = sale_prices[product.id]
            res[product.id] += (res[product.id] * product.price_extra_perc) / 100.0
            res[product.id] += product.price_extra

        return res

    def _set_product_lst_price(self, cr, uid, id, name, value, args, context=None):
        super(product_product, self)._set_product_lst_price(self, cr, uid, id, name, value, args, context=context)
        product_uom_obj = self.pool.get('product.uom')
        product = self.browse(cr, uid, id, context=context)
        if 'uom' in context:
            uom = product.uom_id
            value = product_uom_obj._compute_price(cr, uid,
                    context['uom'], value, uom.id)
        value -= (product.get_sale_price(cr, uid, id, context=context)[id] * product.price_extra_perc) / 100.0
        value -= product.price_extra

        return product.write({'list_price': value})

#     def get_sale_price(self):
#         result = dict.fromkeys(ids, False)
#         product_ids = self.browse(cr, uid, ids, context=context)
#         for product in product_ids:
#             if product.sale_price_type == 'table_2d':
#                 value_x = 0.0
#                 value_y = 0.0
#                 for variant_id in product.attribute_value_ids:
#                     if variant_id.id == product.sale_prices_table_attr_axe_x.attribute_id.id:
#                         value_x = variant_id.name
#                     elif variant_id.id == product.sale_prices_table_attr_axe_y.attribute_id.id:
#                         value_y = variant_id.name
#                 res = self.env['product.prices_table'].search([
#                     ('pos_x', '=', value_x),
#                     ('pos_y', '=', value_y)
#                 ])
#                 result[product.id] = res.value
#             elif product.sale_price_type == 'table_1d':
#                 value_x = 0.0
#                 for variant_id in product.attribute_value_ids:
#                     if variant_id.id == product.sale_prices_table_attr_axe_x.attribute_id.id:
#                         value_x = variant_id.name
#                 res = self.env['product.prices_table'].search([('pos_x', '=', value_x)])
#                 result[product.id] = res.value
#             else:
#                 result[product.id] = product.list_price
#         return result

    def get_sale_price(self, cr, uid, ids, context=False):
        result = dict.fromkeys(ids, False)
        product_ids = self.browse(cr, uid, ids, context=context)

        # FIXME: Mejor usar atributos
        manzano_width = context and context.get('width') or False
        manzano_height = context and context.get('height') or False

        product_prices_table_obj = self.pool.get('product.prices_table')

        for product in product_ids:
            if not manzano_width and not manzano_height:
                result[product.id] = False
            else:
                if product.sale_price_type == 'table_2d':
                    res = product_prices_table_obj.search_read(cr, uid, [
                        ('sale_product_tmpl_id', '=', product.product_tmpl_id.id),
                        ('pos_x', '=', manzano_width),
                        ('pos_y', '=', manzano_height)
                    ], limit=1, context=context)
                    result[product.id] = res and res[0]['value'] or False
                elif product.sale_price_type == 'table_1d':
                    res = product_prices_table_obj.search_read(cr, uid, [
                        ('sale_product_tmpl_id', '=', product.product_tmpl_id.id),
                        ('pos_x', '=', manzano_width)
                    ], limit=1, context=context)
                    result[product.id] = res and res[0]['value'] or False
                elif product.sale_price_type == 'area':
                    result[product.id] = product.list_price * manzano_width * manzano_height
            if not result[product.id]:
                result[product.id] = product.list_price
        return result

    def _get_price_extra_percentage(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for product in self.browse(cr, uid, ids, context=context):
            price_extra = 0.0
            for variant_id in product.attribute_value_ids:
                if not variant_id.price_extra_type == 'percentage':
                    continue
                for price_id in variant_id.price_ids:
                    if price_id.product_tmpl_id.id == product.product_tmpl_id.id:
                        price_extra += price_id.price_extra
            result[product.id] = price_extra
        return result

    def _get_price_extra(self, cr, uid, ids, name, args, context=None):
        result = super(product_product, self)._get_price_extra(cr, uid, ids, name, args, context=context)
        for product in self.browse(cr, uid, ids, context=context):
            price_extra = 0.0
            for variant_id in product.attribute_value_ids:
                if not variant_id.price_extra_type == 'standard':
                    continue
                for price_id in variant_id.price_ids:
                    if price_id.product_tmpl_id.id == product.product_tmpl_id.id:
                        price_extra += price_id.price_extra
            result[product.id] = price_extra
        return result

    def manzano_check_sale_width_value(self, cr, uid, id, width, context=None):
        product = self.browse(cr, uid, id, context=context)
        product_prices_table_obj = self.pool.get('product.prices_table')
        if product.sale_price_type in ['table_1d', 'table_2d']:
            return product_prices_table_obj.search_count(cr, uid, [('sale_product_tmpl_id', '=', product.product_tmpl_id.id),
                                                                   ('pos_x', '=', width)], context=context) > 0
        elif product.sale_price_type == 'area':
            return width >= product.sale_price_area_min_width and width <= product.sale_price_area_max_width
        return True

    def manzano_check_sale_height_value(self, cr, uid, id, height, context=None):
        product = self.browse(cr, uid, id, context=context)
        product_prices_table_obj = self.pool.get('product.prices_table')
        if product.sale_price_type in ['table_1d', 'table_2d']:
            return product_prices_table_obj.search_count(cr, uid, [('sale_product_tmpl_id', '=', product.product_tmpl_id.id), 
                                                                   ('pos_y', '=', height)], context=context) > 0
        elif product.sale_price_type == 'area':
            return height >= product.sale_price_area_min_height and height <= product.sale_price_area_max_height

        return True

    _columns = {
        'price_extra': fields.function(_get_price_extra, type='float', string='Variant Extra Price', help="This is the sum of the extra price of all attributes", digits_compute=dp.get_precision('Product Price')),
        'lst_price': fields.function(_product_lst_price, fnct_inv=_set_product_lst_price, type='float', string='Sale Price', digits_compute=dp.get_precision('Product Price')),

        'price_extra_perc': fields.function(_get_price_extra_percentage, type='float', string='Variant Extra Price Percentage', help="This is the percentage of the extra price of all attributes", digits_compute=dp.get_precision('Product Price')),
    }
