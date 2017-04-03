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

from openerp import models, fields, api
from consts import PRICE_TYPES
import openerp.addons.decimal_precision as dp


class product_template(models.Model):
    _inherit = 'product.template'

    sale_price_area_min_width = fields.Float(string="Min. Width", default=0.0, digits=dp.get_precision('Product Price'))
    sale_price_area_max_width = fields.Float(string="Max. Width", default=0.0, digits=dp.get_precision('Product Price'))
    sale_price_area_min_height = fields.Float(string="Min. Height", default=0.0, digits=dp.get_precision('Product Price'))
    sale_price_area_max_height = fields.Float(string="Max. Height", default=0.0, digits=dp.get_precision('Product Price'))
    sale_price_type = fields.Selection(
            PRICE_TYPES,
            string='Sale Price Type',
            required=True,
            default='standard',
        )
    sale_prices_table = fields.One2many('product.prices_table', 'sale_product_tmpl_id', string="Sale Prices Table")
#     sale_prices_table_attr_axe_x = fields.Many2one('product.attribute.line', 'Sale Price Table Attribute Axe X')
#     sale_prices_table_attr_axe_y = fields.Many2one('product.attribute.line', 'Sale Price Table Attribute Axe Y')

#     cost_price_area_min_width = fields.Float(string="Min. Width", default=0.0, digits=dp.get_precision('Product Price'))
#     cost_price_area_max_width = fields.Float(string="Max. Width", default=0.0, digits=dp.get_precision('Product Price'))
#     cost_price_area_min_height = fields.Float(string="Min. Height", default=0.0, digits=dp.get_precision('Product Price'))
#     cost_price_area_max_height = fields.Float(string="Max. Height", default=0.0, digits=dp.get_precision('Product Price'))
#     cost_price_type = fields.Selection(
#             PRICE_TYPES,
#             string='Cost Price Type',
#             required=True,
#             default='standard',
#         )
#     cost_prices_table = fields.One2many('product.prices_table', 'cost_product_tmpl_id', string="Cost Prices Table")

    @api.v7
    def _price_get(self, cr, uid, products, ptype='list_price', context=None):
        if context is None:
            context = {}

        res = super(product_template, self)._price_get(cr, uid, products, ptype=ptype, context=context)
        product_uom_obj = self.pool.get('product.uom')
        for product in products:
            # standard_price field can only be seen by users in base.group_user
            # Thus, in order to compute the sale price from the cost for users not in this group
            # We fetch the standard price as the superuser
            if ptype != 'standard_price':
                res[product.id] = product.get_sale_price(context=context)[product.id]
            else:
                company_id = context.get('force_company') or product.env.user.company_id.id
                product = product.with_context(force_company=company_id)
                res[product.id] = product.sudo()[ptype]
            if ptype == 'list_price' and product._name == "product.product":
                res[product.id] += (res[product.id] * product.price_extra_perc) / 100.0
                res[product.id] += product.price_extra
            if 'uom' in context:
                uom = product.uom_id
                res[product.id] = product_uom_obj._compute_price(cr, uid,
                        uom.id, res[product.id], context['uom'])
            # Convert from current user company currency to asked one
            if 'currency_id' in context:
                # Take current user company currency.
                # This is right cause a field cannot be in more than one currency
                res[product.id] = self.pool.get('res.currency').compute(cr, uid, product.currency_id.id,
                    context['currency_id'], res[product.id], context=context)
        return res
