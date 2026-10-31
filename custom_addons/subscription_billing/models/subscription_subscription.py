# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SubscriptionSubscription(models.Model):
    _inherit = 'subscription.subscription'

    invoice_ids = fields.One2many(
        'subscription.invoice',
        'subscription_id',
        string='Invoices'
    )
    invoice_count = fields.Integer(
        string='Invoice Count',
        compute='_compute_invoice_count'
    )
    last_billing_date = fields.Date(
        string='Last Billing Date',
        readonly=True,
        tracking=True
    )

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for sub in self:
            sub.invoice_count = len(sub.invoice_ids)

    def action_view_invoices(self):
        self.ensure_one()
        return {
            'name': _('Invoices for %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'subscription.invoice',
            'view_mode': 'list,form',
            'domain': [('subscription_id', '=', self.id)],
            'context': {'default_subscription_id': self.id, 'default_partner_id': self.partner_id.id},
        }

    def action_generate_invoice(self):
        """Manually trigger invoice generation for this subscription."""
        self.ensure_one()
        if self.stage != 'active':
            raise UserError(_("Invoices can only be generated for active subscriptions."))
        invoice = self._create_subscription_invoice()
        return {
            'name': _('Generated Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'subscription.invoice',
            'res_id': invoice.id,
            'view_mode': 'form',
        }

    def _create_subscription_invoice(self):
        """Creates an invoice from the subscription and applies active discounts automatically."""
        self.ensure_one()
        today = fields.Date.context_today(self)
        due_date = today + timedelta(days=15)  # standard 15-day term

        # Find best applicable discount rule (if any)
        discount_rule = self._find_applicable_discount()
        discount_percent = 0.0
        applied_discount = False

        if discount_rule:
            if discount_rule.discount_type == 'percentage':
                discount_percent = discount_rule.discount_value
            applied_discount = discount_rule

        # Build invoice lines from subscription lines
        invoice_lines = []
        for s_line in self.line_ids:
            line_disc = discount_percent
            if discount_rule and discount_rule.apply_to == 'specific_products':
                if s_line.product_id not in discount_rule.product_ids:
                    line_disc = 0.0

            invoice_lines.append((0, 0, {
                'product_id': s_line.product_id.id,
                'name': s_line.name,
                'quantity': s_line.quantity,
                'unit_price': s_line.unit_price,
                'discount': line_disc,
            }))

        invoice_vals = {
            'partner_id': self.partner_id.id,
            'subscription_id': self.id,
            'company_id': self.company_id.id,
            'invoice_date': today,
            'due_date': due_date,
            'payment_terms': self.payment_terms,
            'line_ids': invoice_lines,
            'applied_discount_id': applied_discount.id if applied_discount else False,
            'state': 'draft',
        }
        invoice = self.env['subscription.invoice'].create(invoice_vals)

        # Update discount usage count
        if applied_discount:
            applied_discount.current_usage_count += 1

        # Advance next billing date and mark last billing date
        self.last_billing_date = today
        self._advance_next_billing_date()
        self.message_post(body=_("Invoice %s generated automatically on billing day.") % invoice.name)
        return invoice

    def _find_applicable_discount(self):
        """Matches active discount rules based on minimum purchase and quantities."""
        today = fields.Date.context_today(self)
        total_sub_amount = self.amount_untaxed
        total_qty = sum(self.line_ids.mapped('quantity'))

        discounts = self.env['subscription.discount'].search([('active', '=', True)])
        for disc in discounts:
            if not disc.is_valid:
                continue
            if disc.min_purchase_amount > 0 and total_sub_amount < disc.min_purchase_amount:
                continue
            if disc.min_quantity > 0 and total_qty < disc.min_quantity:
                continue
            return disc
        return False

    def _advance_next_billing_date(self):
        """Advances next_billing_date based on plan's billing frequency."""
        freq = self.plan_id.billing_frequency or 'monthly'
        interval = self.plan_id.billing_interval_count or 1
        cur_date = self.next_billing_date or fields.Date.context_today(self)

        if freq == 'daily':
            self.next_billing_date = cur_date + timedelta(days=interval)
        elif freq == 'weekly':
            self.next_billing_date = cur_date + timedelta(weeks=interval)
        elif freq == 'yearly':
            self.next_billing_date = cur_date + timedelta(days=365 * interval)
        else:  # monthly
            self.next_billing_date = cur_date + timedelta(days=30 * interval)

    @api.model
    def _cron_recurring_billing(self):
        """Cron job executing on Billing Day to generate due invoices without human intervention."""
        today = fields.Date.context_today(self)
        due_subscriptions = self.search([
            ('stage', '=', 'active'),
            ('next_billing_date', '<=', today),
        ])
        for sub in due_subscriptions:
            try:
                sub._create_subscription_invoice()
            except Exception as e:
                sub.message_post(body=_("Recurring billing failed on Billing Day: %s") % str(e))

    @api.model
    def _cron_auto_close_expired(self):
        """Cron job to auto-close expired subscriptions if the plan has auto_close_at_end set."""
        today = fields.Date.context_today(self)
        expired_subs = self.search([
            ('stage', '=', 'active'),
            ('expiry_date', '<', today),
            ('plan_id.auto_close_at_end', '=', True),
        ])
        for sub in expired_subs:
            sub.action_close(reason=_("Auto-closed on expiry date by plan policy."))
