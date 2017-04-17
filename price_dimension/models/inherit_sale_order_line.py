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
from openerp.exceptions import ValidationError
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _


class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    # FIXME: Mejor usar atributos
    manzano_width = fields.Float(string="Width", required=True)
    manzano_height = fields.Float(string="Height", required=True)

    @api.constrains('manzano_width')
    def _check_manzano_width(self):
        for record in self:
            if not record.product_id.manzano_check_sale_dim_values(record.manzano_width, record.manzano_height)[0]:
                raise ValidationError("Invalid width!")

    @api.constrains('manzano_height')
    def _check_manzano_height(self):
        for record in self:
            if not record.product_id.manzano_check_sale_dim_values(record.manzano_width, record.manzano_height)[0]:
                raise ValidationError("Invalid height!")

    @api.onchange('product_id', 'manzano_width', 'manzano_height')
    def product_id_change(self):
        super(sale_order_line, self).product_id_change()

        if not self.product_id:
            return

        if self.manzano_height != 0 and self.manzano_width != 0 and not self.product_id.manzano_check_sale_dim_values(self.manzano_width, self.manzano_height)[0]:
            raise ValidationError(_("Invalid Dimensions!"))

        vals = {}
        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id,

            width=self.manzano_width,
            height=self.manzano_height
        )

        name = product.name_get()[0][1]
        if product.sale_price_type != 'standard':
            name += ' [%dx%d]' % (self.manzano_width, self.manzano_height)
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price(product.price, product.taxes_id, self.tax_id)
        self.update(vals)

    def product_uom_change(self):
        super(sale_order_line, self).product_uom_change()
        if not self.product_uom:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=self.product_uom_qty,
                date_order=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position'),

                width=self.manzano_width,
                height=self.manzano_height
            )
            self.price_unit = self.env['account.tax']._fix_tax_included_price(product.price, product.taxes_id, self.tax_id)

    @api.multi
    def _prepare_order_line_procurement(self, group_id=False):
        self.ensure_one()
        vals = super(sale_order_line, self)._prepare_order_line_procurement(group_id=group_id)
        vals.update({
            'manzano_width': self.manzano_width,
            'manzano_height': self.manzano_height
        })
        return vals

    # BREAK INHERITANCE!!
    @api.multi
    def _action_procurement_create(self):
        """
        Create procurements based on quantity ordered. If the quantity is increased, new
        procurements are created. If the quantity is decreased, no automated action is taken.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        new_procs = self.env['procurement.order'] #Empty recordset
        for line in self:
            if line.state != 'sale' or not line.product_id._need_procurement():
                continue
            qty = 0.0
            for proc in line.procurement_ids:
                qty += proc.product_qty
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                continue
 
            if not line.order_id.procurement_group_id:
                vals = line.order_id._prepare_procurement_group()
                line.order_id.procurement_group_id = self.env["procurement.group"].create(vals)
 
            vals = line._prepare_order_line_procurement(
                group_id=line.order_id.procurement_group_id.id)
            vals['product_qty'] = line.product_uom_qty - qty
            new_proc = self.env["procurement.order"].with_context(
                    procurement_autorun_defer=True,
                ).create(vals)
            # Do one by one because need pass specific context values
            new_proc.with_context(
                width=line.manzano_width,
                height=line.manzano_height).run()
            new_procs += new_proc
        return new_procs

#     def product_id_change(self):
#         res = super(sale_order_line, self).product_id_change()
# 
#         vals = {}
#         if self.order_id.pricelist_id and self.order_id.partner_id:
#             vals['price_unit'] = self.env['account.tax']._fix_tax_included_price(product.price, product.taxes_id, self.tax_id)
#         self.update(vals)
#         return res
