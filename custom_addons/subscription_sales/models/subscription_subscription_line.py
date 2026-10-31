# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


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

    @api.depends('quantity', 'unit_price', 'tax_percent')
    def _compute_price(self):
        for line in self:
            subtotal = line.quantity * line.unit_price
            tax_amount = subtotal * (line.tax_percent / 100.0)
            line.price_subtotal = subtotal
            line.price_total = subtotal + tax_amount

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
