# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class SubscriptionFinanceReport(models.TransientModel):
    _name = 'subscription.finance.report'
    _description = 'Subscription Finance Dashboard Report'

    name = fields.Char(default='Finance Summary', readonly=True)
    active_subscriptions_count = fields.Integer(
        string='Active Subscriptions',
        compute='_compute_metrics',
        help="Total number of currently active subscriptions."
    )
    total_recurring_revenue = fields.Monetary(
        string='Total Active Recurring Revenue',
        compute='_compute_metrics',
        currency_field='currency_id',
        help="Monthly/Contract recurring value of all active subscriptions."
    )
    total_invoiced_amount = fields.Monetary(
        string='Total Invoiced',
        compute='_compute_metrics',
        currency_field='currency_id'
    )
    total_revenue_collected = fields.Monetary(
        string='Revenue Collected (Paid)',
        compute='_compute_metrics',
        currency_field='currency_id'
    )
    total_outstanding_amount = fields.Monetary(
        string='Outstanding / Owed Amount',
        compute='_compute_metrics',
        currency_field='currency_id'
    )
    total_overdue_amount = fields.Monetary(
        string='Overdue Amount',
        compute='_compute_metrics',
        currency_field='currency_id'
    )
    overdue_invoices_count = fields.Integer(
        string='Overdue Invoices Count',
        compute='_compute_metrics'
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )

    @api.depends('name')
    def _compute_metrics(self):
        """
        Fast SQL aggregates to guarantee sub-second (< 2s) response time
        even with tens of thousands of subscription and invoice records.
        """
        today = fields.Date.context_today(self)
        self.env.cr.execute("""
            SELECT 
                COUNT(id) AS active_count,
                COALESCE(SUM(amount_total), 0) AS recurring_rev
            FROM subscription_subscription 
            WHERE stage = 'active'
        """)
        sub_row = self.env.cr.dictfetchone() or {}

        self.env.cr.execute("""
            SELECT 
                COALESCE(SUM(amount_total), 0) AS total_invoiced,
                COALESCE(SUM(amount_paid), 0) AS total_paid,
                COALESCE(SUM(amount_due), 0) AS total_due,
                COALESCE(SUM(CASE WHEN is_overdue THEN amount_due ELSE 0 END), 0) AS total_overdue,
                COUNT(CASE WHEN is_overdue THEN 1 ELSE NULL END) AS overdue_count
            FROM subscription_invoice
            WHERE state != 'cancelled'
        """)
        inv_row = self.env.cr.dictfetchone() or {}

        for rec in self:
            rec.active_subscriptions_count = sub_row.get('active_count', 0)
            rec.total_recurring_revenue = sub_row.get('recurring_rev', 0.0)
            rec.total_invoiced_amount = inv_row.get('total_invoiced', 0.0)
            rec.total_revenue_collected = inv_row.get('total_paid', 0.0)
            rec.total_outstanding_amount = inv_row.get('total_due', 0.0)
            rec.total_overdue_amount = inv_row.get('total_overdue', 0.0)
            rec.overdue_invoices_count = inv_row.get('overdue_count', 0)
