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
from manzano_consts import PRICE_TYPES


class product_supplier_info(models.Model):
    _inherit = 'product.supplierinfo'

    price_area_min_width = fields.Float(string="Min. Width", default=0.0)
    price_area_max_width = fields.Float(string="Max. Width", default=0.0)
    price_area_min_height = fields.Float(string="Min. Height", default=0.0)
    price_area_max_height = fields.Float(string="Max. Height", default=0.0)

    price_type = fields.Selection(
            PRICE_TYPES,
            string='Supplier Price Type',
            required=True,
            default='standard',
        )
    prices_table = fields.One2many('product.prices_table', 'supplier_product_id', string="Supplier Prices Table")
