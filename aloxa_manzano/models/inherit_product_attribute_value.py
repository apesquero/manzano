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


class product_attribute_value(osv.osv):
    _inherit = "product.attribute.value"

    _columns = {
        'price_extra_perc': fields.float(string="Price Extra Percentage"),
    }
    
    _constraints = [
        (_check_prices, "Can't set 'price extra percentage' and 'price extra' at the same time in the same record", ['price_extra','price_extra_perc']),
    ]

    def _get_price_extra(self, cr, uid, ids, name, args, context=None):
        super(product_attribute_value, self)._get_price_extra(cr, uid, ids, name, args, context=context)
        result = dict.fromkeys(ids, 0)
        if not context.get('active_id'):
            return result

        for obj in self.browse(cr, uid, ids, context=context):
            for price_id in obj.price_ids:
                if price_id.product_tmpl_id.id == context.get('active_id'):
                    if price_id.price_extra_perc != 0.0:
                        result[obj.id] = (price_id.product_tmpl_id.lst_price * price_id.price_extra_perc) / 100.0
                    else:
                        result[obj.id] = price_id.price_extra
                    break
        return result

    def _check_prices(self, cr, uid, ids, context=None):
        product_attrs = self.browse(cr, uid, ids, context=context)
        for attr in product_attrs:
            if attr.price_extra_perc != 0.0 and attr.price_extra != 0.0:
                return False
        return True
