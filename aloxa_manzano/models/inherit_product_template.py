# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
from manzano_consts import PRICE_TYPES


class product_template(models.Model):
    _inherit = 'product.template'

    sale_price_area_min_width = fields.Float(string="Min. Width", default=0.0)
    sale_price_area_max_width = fields.Float(string="Max. Width", default=0.0)
    sale_price_area_min_height = fields.Float(string="Min. Height", default=0.0)
    sale_price_area_max_height = fields.Float(string="Max. Height", default=0.0)
    sale_price_type = fields.Selection(
            PRICE_TYPES,
            string='Sale Price Type',
            required=True,
            default='standard',
        )
    sale_prices_table = fields.One2many('product.prices_table', 'sale_product_tmpl_id', string="Sale  Prices Table")

    cost_price_area_min_width = fields.Float(string="Min. Width", default=0.0)
    cost_price_area_max_width = fields.Float(string="Max. Width", default=0.0)
    cost_price_area_min_height = fields.Float(string="Min. Height", default=0.0)
    cost_price_area_max_height = fields.Float(string="Max. Height", default=0.0)
    cost_price_type = fields.Selection(
            PRICE_TYPES,
            string='Cost Price Type',
            required=True,
            default='standard',
        )
    cost_prices_table = fields.One2many('product.prices_table', 'cost_product_tmpl_id', string="Cost Prices Table")
