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
import openerp.addons.decimal_precision as dp
from .consts import PRICE_TYPES


class product_supplier_info(models.Model):
    _inherit = 'product.supplierinfo'

    @api.depends('attribute_value_ids')
    def _get_price_extra_percentage(self):
        product_id = self.env.context and self.env.context.get('product_id') or False
        for supplier in self:
            price_extra = 0.0
            for variant_id in supplier.attribute_value_ids:
                if product_id and variant_id.value not in product_id.attribute_value_ids:
                    continue
                if variant_id.price_extra_type != 'percentage' or supplier.id != variant_id.supplierinfo_id.id:
                    continue
                price_extra += variant_id.price_extra
            supplier.price_extra_perc = price_extra

    @api.depends('attribute_value_ids')
    def _get_price_extra(self):
        product_id = self.env.context and self.env.context.get('product_id') or False
        for supplier in self:
            price_extra = 0.0
            for variant_id in supplier.attribute_value_ids:
                if product_id and variant_id.value not in product_id.attribute_value_ids:
                    continue
                if variant_id.price_extra_type != 'standard' or supplier.id != variant_id.supplierinfo_id.id:
                    continue
                price_extra += variant_id.price_extra
            supplier.price_extra = price_extra

    price_area_min_width = fields.Float(string="Min. Width", default=0.0, digits=dp.get_precision('Product Price'))
    price_area_max_width = fields.Float(string="Max. Width", default=0.0, digits=dp.get_precision('Product Price'))
    price_area_min_height = fields.Float(string="Min. Height", default=0.0, digits=dp.get_precision('Product Price'))
    price_area_max_height = fields.Float(string="Max. Height", default=0.0, digits=dp.get_precision('Product Price'))
    min_price_area = fields.Monetary('Min. Price')

    price_type = fields.Selection(
            PRICE_TYPES,
            string='Supplier Price Type',
            required=True,
            default='standard',
        )
    prices_table = fields.One2many('product.prices_table', 'supplier_product_id', string="Supplier Prices Table")

    attribute_value_ids = fields.One2many(
        comodel_name='supplier.attribute.value',
        inverse_name='supplierinfo_id'
    )

    price_extra = fields.Float(compute='_get_price_extra', string='Variant Extra Price', help="This is the sum of the extra price of all attributes", digits_compute=dp.get_precision('Product Price'))
    price_extra_perc = fields.Float(compute='_get_price_extra_percentage', string='Variant Extra Price Percentage', help="This is the percentage of the extra price of all attributes", digits_compute=dp.get_precision('Product Price'))

    def get_price_table_headers(self):
        result = {'x': [0], 'y': [0]}
        for rec in self.prices_table:
            result['x'].append(rec.pos_x)
            result['y'].append(rec.pos_y)
        result.update({
            'x': sorted(list(set(result['x']))),
            'y': sorted(list(set(result['y'])))
        })
        return result

    # TODO: Estos metodos necesitarán ser reescritos cuando se usen los atributos
    def manzano_check_dim_values(self, width, height):
        if self.price_type in ['table_1d', 'table_2d']:
            product_prices_table_obj = self.env['product.prices_table']
            norm_width = self.manzano_normalize_width_value(width)
            if self.price_type == 'table_2d':
                norm_height = self.manzano_normalize_height_value(height)
                return product_prices_table_obj.search_count([('supplier_product_id', '=', self.id),
                                                              ('pos_x', '=', norm_width),
                                                              ('pos_y', '=', norm_height),
                                                              ('value', '!=', 0)]) > 0
            return product_prices_table_obj.search_count([('supplier_product_id', '=', self.id),
                                                          ('pos_x', '=', norm_width),
                                                          ('value', '!=', 0)]) > 0
        elif self.price_type == 'area':
            return width >= self.price_area_min_width and width <= self.price_area_max_width and height >= self.price_area_min_height and height <= self.price_area_max_height
        return True

    def manzano_normalize_width_value(self, width):
        headers = self.get_price_table_headers()
        norm_val = width
        for index in range(len(headers['x'])-1):
            if width > headers['x'][index] and width <= headers['x'][index+1]:
                norm_val = headers['x'][index+1]
        return norm_val

    def manzano_normalize_height_value(self, height):
        headers = self.get_price_table_headers()
        norm_val = height
        for index in range(len(headers['y'])-1):
            if height > headers['y'][index] and height <= headers['y'][index+1]:
                norm_val = headers['y'][index+1]
        return norm_val

    @api.depends('price')
    def get_supplier_price(self):
        # FIXME: Mejor usar atributos
        manzano_width = self.env.context and self.env.context.get('width') or False
        manzano_height = self.env.context and self.env.context.get('height') or False
        product_id = self.env.context and self.env.context.get('product_id') or False

        result = {}
        for record in self:
            result[record.id] = False
            if manzano_width:
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
                    result[record.id] = max(record.min_price_area, result[record.id])
            if not result[record.id]:
                result[record.id] = record.price
            result[record.id] += record.with_context(product_id=product_id).price_extra + record.with_context(product_id=product_id).price_extra_perc
        return result
    # ---

    # -- START Original source by 'Prev. Manzano Dev.'
    @api.multi
    def action_open_value_extras(self):
        self.ensure_one()
        extra_ds = self.env['supplier.attribute.value']
        for line in self.product_tmpl_id.attribute_line_ids:
            for value in line.value_ids:
                extra = extra_ds.search([('supplierinfo_id', '=', self.id),
                                         ('value', '=', value.id)])
                if not extra:
                    extra = extra_ds.create({
                        'supplierinfo_id': self.id,
                        'value': value.id,
                    })
                extra_ds |= extra
        all_supplierinfo_extra = extra_ds.search([
            ('supplierinfo_id', '=', self.id)
        ])
        remove_extra = all_supplierinfo_extra - extra_ds
        remove_extra.unlink()
        result = self.product_tmpl_id._get_act_window_dict(
            'price_dimension.supplier_attribute_value_action')
        return result
    # -- END
