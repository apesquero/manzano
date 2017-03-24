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

from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp import models, fields, api, SUPERUSER_ID
from openerp.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    # FIXME: Mejor usar atributos
    manzano_width = fields.Float(string="Width", required=True)
    manzano_height = fields.Float(string="Height", required=True)

    @api.constrains('manzano_width')
    def _check_manzano_width(self):
        for record in self:
            if not record.product_id.manzano_check_sale_width_value(record.manzano_width)[0]:
                raise ValidationError("Invalid width!")

    @api.constrains('manzano_height')
    def _check_manzano_height(self):
        for record in self:
            if not record.product_id.manzano_check_sale_height_value(record.manzano_height)[0]:
                raise ValidationError("Invalid height!")

    @api.onchange('product_id', 'manzano_width', 'manzano_height')
    def onchange_product_id(self):
        super(purchase_order_line, self).onchange_product_id()
        result = {}
        if not self.product_id:
            return result

        product = self.product_id.with_context(
            width=self.manzano_width,
            height=self.manzano_height
        )

        # Reset date, price and quantity since _onchange_quantity will provide default values
        self.date_planned = datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.price_unit = self.product_qty = 0.0
        self.product_uom = product.uom_po_id or product.uom_id
        result['domain'] = {'product_uom': [('category_id', '=', product.uom_id.category_id.id)]}

        product_lang = product.with_context({
            'lang': self.partner_id.lang,
            'partner_id': self.partner_id.id,
            'width': self.manzano_width,
            'height': self.manzano_height
        })
        self.name = product_lang.display_name
        self.name += ' [%dx%d]' % (self.manzano_width, self.manzano_height)
        if product_lang.description_purchase:
            self.name += '\n' + product_lang.description_purchase

        fpos = self.order_id.fiscal_position_id
        if self.env.uid == SUPERUSER_ID:
            company_id = self.env.user.company_id.id
            self.taxes_id = fpos.map_tax(product.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id))
        else:
            self.taxes_id = fpos.map_tax(product.supplier_taxes_id)

        self._suggest_quantity()
        self._onchange_quantity()

        return result

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        super(purchase_order_line, self)._onchange_quantity()
        if not self.product_id:
            return
        
        product = self.product_id.with_context(
            width=self.manzano_width,
            height=self.manzano_height
        )

        seller = product._select_seller(
            product,
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order[:10],
            uom_id=self.product_uom)

        seller = seller.with_context(
            width=self.manzano_width,
            height=self.manzano_height
        )

        if seller or not self.date_planned:
            self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        if not seller:
            return

        price_unit = self.env['account.tax']._fix_tax_included_price(seller.get_supplier_price()[seller.id], product.supplier_taxes_id, self.taxes_id) if seller else 0.0
        if price_unit and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
            price_unit = seller.currency_id.compute(price_unit, self.order_id.currency_id)

        if seller and self.product_uom and seller.product_uom != self.product_uom:
            price_unit = self.env['product.uom']._compute_price(seller.product_uom.id, price_unit, to_uom_id=self.product_uom.id)

        self.price_unit = price_unit
