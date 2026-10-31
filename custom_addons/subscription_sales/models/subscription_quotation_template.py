# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SubscriptionQuotationTemplate(models.Model):
    _name = 'subscription.quotation.template'
    _description = 'Subscription Quotation Template'
    _order = 'name'

    name = fields.Char(string='Template Name', required=True)
    plan_id = fields.Many2one(
        'subscription.plan',
        string='Default Plan',
        required=True,
        domain="[('is_start_date_reached', '=', True), ('is_end_date_valid', '=', True)]",
        help="Pre-configured plan applied when using this template."
    )
    validity_days = fields.Integer(
        string='Quotation Validity (Days)',
        default=30,
        help="Number of days the quotation remains valid from date of issuance."
    )
    note = fields.Html(string='Terms & Conditions Note')
    line_ids = fields.One2many(
        'subscription.quotation.template.line',
        'template_id',
        string='Template Lines',
        copy=True
    )
    active = fields.Boolean(default=True)


class SubscriptionQuotationTemplateLine(models.Model):
    _name = 'subscription.quotation.template.line'
    _description = 'Subscription Quotation Template Line'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    template_id = fields.Many2one(
        'subscription.quotation.template',
        string='Template',
        required=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        domain="[('is_subscription', '=', True)]"
    )
    name = fields.Char(string='Description', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    unit_price = fields.Float(string='Unit Price')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.display_name
            self.unit_price = self.product_id.lst_price
