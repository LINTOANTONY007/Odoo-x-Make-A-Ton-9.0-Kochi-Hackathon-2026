# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class SubscriptionSubscriptionLine(models.Model):
    _name = 'subscription.subscription.line'
    _description = 'Subscription Line'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    subscription_id = fields.Many2one(
        'subscription.subscription',
        string='Subscription',
        required=True,
        ondelete='cascade',
        index=True
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product / Add-on',
        required=True,
        domain="[('is_subscription', '=', True)]"
    )
    name = fields.Char(string='Description', required=True)
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    unit_price = fields.Float(string='Unit Price', required=True)
    tax_ids = fields.Many2many(
        'subscription.tax',
        'subscription_subscription_line_tax_rel',
        'line_id',
        'tax_id',
        string='Taxes'
    )
    tax_percent = fields.Float(string='Tax %', default=0.0)

    price_subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_price',
        store=True,
        currency_field='currency_id'
    )
    price_total = fields.Monetary(
        string='Total',
        compute='_compute_price',
        store=True,
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='subscription_id.currency_id',
        readonly=True
    )

    @api.depends('quantity', 'unit_price', 'tax_ids', 'tax_ids.amount', 'tax_ids.tax_type', 'tax_percent')
    def _compute_price(self):
        for line in self:
            subtotal = line.quantity * line.unit_price
            line.price_subtotal = subtotal
            tax_amt = 0.0
            if line.tax_ids:
                for tax in line.tax_ids:
                    if tax.tax_type == 'percent':
                        tax_amt += subtotal * (tax.amount / 100.0)
                    else:
                        tax_amt += tax.amount * line.quantity
                if subtotal > 0:
                    line.tax_percent = (tax_amt / subtotal) * 100.0
            elif line.tax_percent:
                tax_amt = subtotal * (line.tax_percent / 100.0)
            else:
                line.tax_percent = 0.0
            line.price_total = subtotal + tax_amt

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.display_name
            self.unit_price = self.product_id.lst_price

    @api.constrains('quantity')
    def _check_quantity(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_("Line quantity must be greater than zero."))

    def write(self, vals):
        for line in self:
            if line.subscription_id.stage not in ('draft', 'quotation'):
                raise UserError(_("You cannot modify line quantities, prices, or taxes on a confirmed subscription."))
        return super().write(vals)

    def unlink(self):
        for line in self:
            if line.subscription_id.stage not in ('draft', 'quotation'):
                raise UserError(_("You cannot delete product lines from a confirmed subscription."))
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            sub_id = vals.get('subscription_id')
            if sub_id:
                sub = self.env['subscription.subscription'].browse(sub_id)
                if sub.stage not in ('draft', 'quotation'):
                    raise UserError(_("You cannot add lines to a confirmed subscription."))
        return super().create(vals_list)
