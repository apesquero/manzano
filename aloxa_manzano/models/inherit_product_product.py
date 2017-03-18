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

import openerp
from openerp import api, tools, SUPERUSER_ID
from openerp.osv import osv, fields, expression


class product_product(osv.osv):
    _inherit = 'product.product'

    def _get_price_extra(self, cr, uid, ids, name, args, context=None):
        super(product_product, self)._get_price_extra(cr, uid, ids, name, args, context=context)
        result = dict.fromkeys(ids, False)
        for product in self.browse(cr, uid, ids, context=context):
            price_extra = 0.0
            for variant_id in product.attribute_value_ids:
                for price_id in variant_id.price_ids:
                    if price_id.product_tmpl_id.id == product.product_tmpl_id.id:
                        if price_id.price_extra_perc != 0.0:
                            price_extra += (price_id.product_tmpl_id.lst_price * price_id.price_extra_perc) / 100.0 
                        else:
                            price_extra += price_id.price_extra
            result[product.id] = price_extra
        return result
