# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class SubscriptionDiscount(models.Model):
    _name = 'subscription.discount'
    _description = 'Subscription Discount Rule'
    _order = 'name'

    name = fields.Char(string='Discount Rule Name', required=True)
    discount_type = fields.Selection([
        ('percentage', 'Percentage (%)'),
        ('fixed', 'Fixed Amount'),
    ], string='Discount Type', default='percentage', required=True)
    discount_value = fields.Float(string='Discount Value', required=True, default=0.0)

    # Qualification criteria
    min_purchase_amount = fields.Float(
        string='Minimum Purchase Amount',
        default=0.0,
        help="Minimum subscription amount required to qualify."
    )
    min_quantity = fields.Float(
        string='Minimum Quantity (Seats/Units)',
        default=0.0,
        help="Minimum quantity across lines required to qualify."
    )

    # Time validity & Limits
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    max_usage_count = fields.Integer(
        string='Usage Limit',
        default=0,
        help="Maximum number of times this discount can be applied. 0 means unlimited."
    )
    current_usage_count = fields.Integer(
        string='Times Used',
        default=0,
        readonly=True,
        help="Number of times this discount has been applied to invoices."
    )

    # Scope of application
    apply_to = fields.Selection([
        ('whole_subscription', 'Whole Subscription'),
        ('specific_products', 'Specific Products'),
    ], string='Applies To', default='whole_subscription', required=True)
    product_ids = fields.Many2many(
        'product.product',
        'subscription_discount_product_rel',
        'discount_id',
        'product_id',
        string='Eligible Products',
        domain="[('is_subscription', '=', True)]"
    )

    active = fields.Boolean(default=True)
    is_valid = fields.Boolean(
        string='Is Currently Valid',
        compute='_compute_is_valid',
        help="Indicates whether this discount is currently usable based on date and usage limits."
    )

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.user.has_group('subscription_catalog.group_subscription_admin'):
            raise UserError(_("Only administrators can create discount rules."))
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.user.has_group('subscription_catalog.group_subscription_admin'):
            raise UserError(_("Only administrators can modify discount rules."))
        return super().write(vals)

    @api.depends('active', 'start_date', 'end_date', 'max_usage_count', 'current_usage_count')
    def _compute_is_valid(self):
        today = fields.Date.context_today(self)
        for disc in self:
            if not disc.active:
                disc.is_valid = False
                continue
            date_ok = (not disc.start_date or disc.start_date <= today) and (not disc.end_date or disc.end_date >= today)
            usage_ok = disc.max_usage_count == 0 or disc.current_usage_count < disc.max_usage_count
            disc.is_valid = date_ok and usage_ok

    @api.constrains('discount_value', 'discount_type')
    def _check_discount_value(self):
        for disc in self:
            if disc.discount_value <= 0:
                raise ValidationError(_("Discount value must be greater than zero."))
            if disc.discount_type == 'percentage' and disc.discount_value > 100:
                raise ValidationError(_("Percentage discount cannot exceed 100%."))

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for disc in self:
            if disc.start_date and disc.end_date and disc.start_date > disc.end_date:
                raise ValidationError(_("Discount end date cannot be earlier than start date."))
