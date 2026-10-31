# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SubscriptionPlan(models.Model):
    _name = 'subscription.plan'
    _description = 'Subscription Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Plan Name', required=True, tracking=True)
    code = fields.Char(string='Code', tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True
    )

    # Billing cadence & Pricing
    billing_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ], string='Billing Frequency', required=True, default='monthly', tracking=True)
    billing_interval_count = fields.Integer(
        string='Interval Count',
        default=1,
        help="Number of days/weeks/months/years between billing cycles.",
        required=True
    )
    cost = fields.Monetary(
        string='Plan Cost / Recurring Price',
        currency_field='currency_id',
        required=True,
        tracking=True
    )
    min_quantity = fields.Float(
        string='Minimum Quantity',
        default=1.0,
        help="Minimum number of seats/units required for this plan."
    )

    # Availability Dates
    start_date = fields.Date(
        string='Available From',
        help="Date from which this plan can be offered to customers."
    )
    end_date = fields.Date(
        string='Available Until',
        help="Date after which this plan cannot be selected for new subscriptions."
    )
    is_available = fields.Boolean(
        string='Is Available',
        compute='_compute_is_available',
        store=False,
        help="Indicates whether the plan is currently available based on dates and active status."
    )

    # Lifecycle Policies
    auto_close_at_end = fields.Boolean(
        string='Auto-Close at Expiry',
        default=False,
        help="If enabled, subscriptions on this plan will automatically close when their end date arrives."
    )
    allow_early_close = fields.Boolean(
        string='Allow Early Cancellation',
        default=True,
        help="If enabled, customers or staff can terminate the subscription before the contract expiration."
    )
    allow_pause = fields.Boolean(
        string='Allow Pause',
        default=True,
        help="If enabled, active subscriptions can be temporarily suspended/paused."
    )
    allow_renewal = fields.Boolean(
        string='Allow Renewal',
        default=True,
        help="If enabled, expiring subscriptions can be extended or renewed for another period."
    )

    description = fields.Html(string='Plan Terms & Description')
    product_ids = fields.Many2many(
        'product.template',
        'subscription_plan_product_rel',
        'plan_id',
        'product_id',
        string='Eligible Products'
    )

    @api.depends('active', 'start_date', 'end_date')
    def _compute_is_available(self):
        today = fields.Date.context_today(self)
        for plan in self:
            if not plan.active:
                plan.is_available = False
                continue
            valid_start = not plan.start_date or plan.start_date <= today
            valid_end = not plan.end_date or plan.end_date >= today
            plan.is_available = valid_start and valid_end

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for plan in self:
            if plan.start_date and plan.end_date and plan.start_date > plan.end_date:
                raise ValidationError(_("The plan's 'Available Until' date must be after 'Available From' date."))

    @api.constrains('min_quantity')
    def _check_min_quantity(self):
        for plan in self:
            if plan.min_quantity <= 0:
                raise ValidationError(_("Minimum quantity must be greater than zero."))
