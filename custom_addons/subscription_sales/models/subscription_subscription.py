# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class SubscriptionSubscription(models.Model):
    _name = 'subscription.subscription'
    _description = 'Customer Subscription'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Subscription Number',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('New')
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True,
        index=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        default=lambda self: self.env.user,
        tracking=True
    )
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

    plan_id = fields.Many2one(
        'subscription.plan',
        string='Subscription Plan',
        required=True,
        tracking=True,
        domain="[('active', '=', True), ('is_start_date_reached', '=', True), ('is_end_date_valid', '=', True)]"
    )
    template_id = fields.Many2one(
        'subscription.quotation.template',
        string='Quotation Template',
        help="Template used to populate lines and initial configuration."
    )

    # Dates & Terms
    start_date = fields.Date(
        string='Start Date',
        default=fields.Date.context_today,
        required=True,
        tracking=True
    )
    expiry_date = fields.Date(
        string='Expiry / End Date',
        tracking=True,
        help="Date when the current subscription period expires."
    )
    next_billing_date = fields.Date(
        string='Next Billing Date',
        default=fields.Date.context_today,
        tracking=True,
        index=True
    )
    payment_terms = fields.Char(
        string='Payment Terms',
        default='Due upon receipt',
        help="e.g. Immediate Payment, Net 15, Net 30"
    )

    # Lifecycle State
    stage = fields.Selection([
        ('draft', 'Draft'),
        ('quotation', 'Quotation'),
        ('confirmed', 'Confirmed'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
    ], string='Status', default='draft', required=True, tracking=True, index=True)

    line_ids = fields.One2many(
        'subscription.subscription.line',
        'subscription_id',
        string='Subscription Lines',
        copy=True
    )

    # Financial Totals
    amount_untaxed = fields.Monetary(
        string='Untaxed Amount',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    amount_tax = fields.Monetary(
        string='Taxes',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    amount_total = fields.Monetary(
        string='Recurring Total',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
        tracking=True
    )

    terms_conditions = fields.Html(string='Terms and Conditions')
    close_reason = fields.Char(string='Closing Reason', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('subscription.subscription') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        sensitive_fields = {'line_ids', 'partner_id', 'plan_id', 'template_id', 'company_id', 'start_date'}
        if sensitive_fields.intersection(vals.keys()):
            for sub in self:
                if sub.stage not in ('draft', 'quotation'):
                    raise UserError(_("You cannot modify order lines, plan, customer or agreement terms on a confirmed subscription."))
        return super().write(vals)

    @api.depends('line_ids.price_subtotal', 'line_ids.price_total')
    def _compute_amounts(self):
        for sub in self:
            sub.amount_untaxed = sum(sub.line_ids.mapped('price_subtotal'))
            sub.amount_tax = sum(sub.line_ids.mapped('price_total')) - sub.amount_untaxed
            sub.amount_total = sum(sub.line_ids.mapped('price_total'))

    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id:
            if self.template_id.plan_id:
                self.plan_id = self.template_id.plan_id
            if self.template_id.validity_days and self.start_date:
                self.expiry_date = self.start_date + timedelta(days=self.template_id.validity_days)
            if self.template_id.note:
                self.terms_conditions = self.template_id.note

            # Populate lines from template
            new_lines = []
            for t_line in self.template_id.line_ids:
                new_lines.append((0, 0, {
                    'product_id': t_line.product_id.id,
                    'name': t_line.name,
                    'quantity': t_line.quantity,
                    'unit_price': t_line.unit_price,
                }))
            if new_lines:
                self.line_ids = [(5, 0, 0)] + new_lines

    @api.onchange('plan_id')
    def _onchange_plan_id(self):
        if self.plan_id and not self.line_ids:
            # Check min quantity
            pass

    # Lifecycle State Transitions
    def action_send_quotation(self):
        """Move Draft to Quotation stage and log in chatter."""
        self.ensure_one()
        if self.stage != 'draft':
            raise UserError(_("Only draft subscriptions can be moved to Quotation."))
        if not self.line_ids:
            raise ValidationError(_("You cannot send a quotation with no product lines."))
        self.stage = 'quotation'
        self.message_post(body=_("Subscription Quotation prepared and sent to customer."))

    def action_confirm(self):
        """Move from Quotation (or Draft) to Confirmed."""
        self.ensure_one()
        if self.stage not in ('draft', 'quotation'):
            raise UserError(_("Only Draft or Quotation can be confirmed."))
        if not self.line_ids:
            raise ValidationError(_("Subscription must have at least one line before confirmation."))
        # Verify minimum quantity from plan
        total_qty = sum(self.line_ids.mapped('quantity'))
        if self.plan_id and self.plan_id.min_quantity > total_qty:
            raise ValidationError(_(
                "Total quantity (%s) is less than the plan minimum required (%s)."
            ) % (total_qty, self.plan_id.min_quantity))

        if self.plan_id:
            if not self.plan_id.is_start_date_reached:
                raise ValidationError(_(
                    "The selected subscription plan '%s' is not yet available because its start date (%s) has not been reached."
                ) % (self.plan_id.name, self.plan_id.start_date))
            if not self.plan_id.is_end_date_valid:
                raise ValidationError(_(
                    "The selected subscription plan '%s' cannot be used because its availability end date (%s) has passed."
                ) % (self.plan_id.name, self.plan_id.end_date))

        self.stage = 'confirmed'
        self.message_post(body=_("Subscription offer has been confirmed by customer."))

    def action_activate(self):
        """Activate the subscription and set the next billing date."""
        self.ensure_one()
        if self.stage not in ('confirmed', 'paused'):
            raise UserError(_("Only confirmed or paused subscriptions can be activated."))
        self.stage = 'active'
        if not self.next_billing_date:
            self.next_billing_date = self.start_date or fields.Date.context_today(self)
        self.message_post(body=_("Subscription is now Active and running."))

    def action_pause(self):
        """Pause active subscription if the plan permits it."""
        self.ensure_one()
        if self.stage != 'active':
            raise UserError(_("Only active subscriptions can be paused."))
        if self.plan_id and not self.plan_id.allow_pause:
            raise UserError(_("The plan '%s' does not permit pausing subscriptions.") % self.plan_id.name)
        self.stage = 'paused'
        self.message_post(body=_("Subscription has been paused."))

    def action_resume(self):
        """Resume a paused subscription."""
        self.ensure_one()
        if self.stage != 'paused':
            raise UserError(_("Only paused subscriptions can be resumed."))
        self.stage = 'active'
        self.message_post(body=_("Subscription has been resumed to active status."))

    def action_renew(self):
        """Renew active or expiring subscription if the plan permits renewal."""
        self.ensure_one()
        if self.plan_id and not self.plan_id.allow_renewal:
            raise UserError(_("The plan '%s' does not permit renewals.") % self.plan_id.name)
        # Advance expiry date based on plan interval
        interval = self.plan_id.billing_interval_count or 1
        freq = self.plan_id.billing_frequency
        cur_end = self.expiry_date or fields.Date.context_today(self)
        if freq == 'daily':
            new_end = cur_end + timedelta(days=interval)
        elif freq == 'weekly':
            new_end = cur_end + timedelta(weeks=interval)
        elif freq == 'yearly':
            new_end = cur_end + timedelta(days=365 * interval)
        else:  # monthly
            new_end = cur_end + timedelta(days=30 * interval)

        self.expiry_date = new_end
        if self.stage == 'closed':
            self.stage = 'active'
        self.message_post(body=_("Subscription renewed until %s.") % new_end)

    def action_close(self, reason=None):
        """Close/cancel subscription (honors allow_early_close policy)."""
        self.ensure_one()
        today = fields.Date.context_today(self)
        is_early = self.expiry_date and today < self.expiry_date
        if is_early and self.plan_id and not self.plan_id.allow_early_close and not self.env.is_admin():
            raise UserError(_("The plan '%s' does not allow early closure.") % self.plan_id.name)
        self.stage = 'closed'
        if reason:
            self.close_reason = reason
        self.message_post(body=_("Subscription closed. Reason: %s") % (reason or "End of lifecycle"))

    def action_reset_to_draft(self):
        """Reset subscription back to Draft state."""
        self.ensure_one()
        self.stage = 'draft'
        self.message_post(body=_("Subscription reset to Draft."))
