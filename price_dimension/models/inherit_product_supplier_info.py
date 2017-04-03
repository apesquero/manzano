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


class product_supplier_info(models.Model):
    _inherit = 'product.supplierinfo'

    price_area_min_width = fields.Float(string="Min. Width", default=0.0, digits=dp.get_precision('Product Price'))
    price_area_max_width = fields.Float(string="Max. Width", default=0.0, digits=dp.get_precision('Product Price'))
    price_area_min_height = fields.Float(string="Min. Height", default=0.0, digits=dp.get_precision('Product Price'))
    price_area_max_height = fields.Float(string="Max. Height", default=0.0, digits=dp.get_precision('Product Price'))

    price_type = fields.Selection(
            PRICE_TYPES,
            string='Supplier Price Type',
            required=True,
            default='standard',
        )
    prices_table = fields.One2many('product.prices_table', 'supplier_product_id', string="Supplier Prices Table")

    def get_price_table_headers(self):
        result = {'x': [], 'y': []}
        for rec in self.prices_table:
            result['x'].append(rec.pos_x)
            result['y'].append(rec.pos_y)
        result.update({
            'x': sorted(list(set(result['x']))),
            'y': sorted(list(set(result['y'])))
        })
        return result

    # TODO: Estos metodos necesitarán ser reescritos cuando se usen los atributos
    def manzano_check_dim_values(self, cr, uid, id, width, height, context=None):
        if self.price_type in ['table_1d', 'table_2d']:
            product_prices_table_obj = self.pool.get('product.prices_table')
            norm_width = self.manzano_normalize_width_value(cr, uid, id, width, context=context)
            if self.price_type == 'table_2d':
                norm_height = self.manzano_normalize_height_value(cr, uid, id, height, context=context)
                return product_prices_table_obj.search_count(cr, uid, [('supplier_product_id', '=', self.id),
                                                                       ('pos_x', '=', norm_width),
                                                                       ('pos_y', '=', norm_height),
                                                                       ('value', '!=', 0)], context=context) > 0
            return product_prices_table_obj.search_count(cr, uid, [('supplier_product_id', '=', self.id),
                                                                   ('pos_x', '=', norm_width),
                                                                   ('value', '!=', 0)], context=context) > 0
        elif self.price_type == 'area':
            return width >= self.price_area_min_width and width <= self.price_area_max_width
        return True

    def manzano_normalize_width_value(self, width):
        headers = self.get_price_table_headers()
        norm_val = width
        num_x_headers = len(headers['x'])
        for index in range(num_x_headers-1):
            if width >= headers['x'][index] and width < headers['x'][num_x_headers-1]:
                norm_val = headers['x'][index]
        return norm_val

    def manzano_normalize_height_value(self, height):
        headers = self.get_price_table_headers()
        norm_val = height
        num_y_headers = len(headers['y'])
        for index in range(num_y_headers-1):
            if height >= headers['y'][index] and height < headers['y'][num_y_headers-1]:
                norm_val = headers['y'][index]
        return norm_val
    # ---

    @api.depends('price')
    def get_supplier_price(self):
        # FIXME: Mejor usar atributos
        manzano_width = self.env.context and self.env.context.get('width') or False
        manzano_height = self.env.context and self.env.context.get('height') or False

        result = {}
        for record in self:
            if not manzano_width and not manzano_height:
                result[record.id] = False
            else:
                product_prices_table_obj = self.env['product.prices_table']
                manzano_width = record.manzano_normalize_width_value(manzano_width)
                if record.price_type == 'table_2d':
                    manzano_height = record.manzano_normalize_height_value(manzano_height)
                    res = product_prices_table_obj.search([
                        ('supplier_product_id', '=', record.id),
                        ('pos_x', '=', manzano_width),
                        ('pos_y', '=', manzano_height)
                    ], limit=1)
                    result[record.id] = res and res.value or False
                elif record.price_type == 'table_1d':
                    res = product_prices_table_obj.search([
                        ('supplier_product_id', '=', record.id),
                        ('pos_x', '=', manzano_width)
                    ], limit=1)
                    result[record.id] = res and res.value or False
                elif record.price_type == 'area':
                    result[record.id] = record.price * manzano_width * manzano_height
            if not result[record.id]:
                result[record.id] = record.price
        return result
