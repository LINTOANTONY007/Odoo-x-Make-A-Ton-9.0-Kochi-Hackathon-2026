# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SubscriptionTax(models.Model):
    _name = 'subscription.tax'
    _description = 'Subscription Tax Rule'
    _order = 'name'

    name = fields.Char(string='Tax Name', required=True)
    tax_type = fields.Selection([
        ('percent', 'Percentage (%)'),
        ('fixed', 'Fixed Amount'),
    ], string='Tax Computation', default='percent', required=True)
    amount = fields.Float(string='Tax Rate / Amount', required=True, default=0.0)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    active = fields.Boolean(default=True)

    @api.constrains('amount')
    def _check_amount(self):
        for tax in self:
            if tax.amount < 0:
                raise ValidationError(_("Tax amount cannot be negative."))
