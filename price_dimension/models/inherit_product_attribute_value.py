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
from openerp.exceptions import UserError
from openerp.tools.translate import _
from .consts import EXTRA_PRICE_TYPES


class product_attribute_value(osv.osv):
    _inherit = "product.attribute.value"

    def unlink(self, cr, uid, ids, context=None):
        ctx = dict(context or {}, active_test=False)
        product_ids = self.pool['product.supplierinfo'].search(cr, uid, [('attribute_value_ids', 'in', ids)], context=ctx)
        if product_ids:
            raise UserError(_('The operation cannot be completed:\nYou are trying to delete an attribute value with a reference on a product supplier variant.'))
        return super(product_attribute_value, self).unlink(cr, uid, ids, context=context)

    _columns = {
        'price_extra_type': fields.selection(EXTRA_PRICE_TYPES,
                                             string='Price Extra Type',
                                             required=True,
                                             default='standard'),
        'supplier_ids': fields.many2many('product.supplierinfo', id1='att_id', id2='prod_id', string='Variants', readonly=True),
    }
