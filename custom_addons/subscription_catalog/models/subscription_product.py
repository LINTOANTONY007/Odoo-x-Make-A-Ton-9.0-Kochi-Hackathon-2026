# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_subscription = fields.Boolean(
        string='Is Subscription Product',
        default=False,
        help="Check this if this product or service is sold on a recurring subscription basis."
    )
    subscription_plan_ids = fields.Many2many(
        'subscription.plan',
        'subscription_plan_product_rel',
        'product_id',
        'plan_id',
        string='Available Plans',
        domain="[('is_start_date_reached', '=', True), ('is_end_date_valid', '=', True)]"
    )
    brand = fields.Char(
        string='Brand / Variant Tag',
        help="Brand variant tag (e.g. Odoo brand)."
    )
