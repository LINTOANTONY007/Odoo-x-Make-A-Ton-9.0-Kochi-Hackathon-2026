# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class SubscriptionInvoice(models.Model):
    _name = 'subscription.invoice'
    _description = 'Subscription Invoice'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'invoice_date desc, id desc'

    name = fields.Char(
        string='Invoice Number',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('Draft')
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True,
        index=True
    )
    subscription_id = fields.Many2one(
        'subscription.subscription',
        string='Subscription Reference',
        ondelete='set null',
        tracking=True,
        index=True
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

    invoice_date = fields.Date(
        string='Invoice Date',
        default=fields.Date.context_today,
        required=True,
        tracking=True
    )
    due_date = fields.Date(
        string='Due Date',
        required=True,
        tracking=True,
        index=True
    )
    payment_terms = fields.Char(string='Payment Terms')

    # Status: Draft -> Confirmed -> Partial -> Paid (and Cancelled)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True, index=True)

    line_ids = fields.One2many(
        'subscription.invoice.line',
        'invoice_id',
        string='Invoice Lines',
        copy=True
    )
    payment_ids = fields.One2many(
        'subscription.payment',
        'invoice_id',
        string='Payments'
    )

    # Amounts
    amount_untaxed = fields.Monetary(
        string='Untaxed Amount',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    amount_discount = fields.Monetary(
        string='Discount',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    amount_tax = fields.Monetary(
        string='Tax',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    amount_total = fields.Monetary(
        string='Total Amount',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
        tracking=True
    )
    amount_paid = fields.Monetary(
        string='Amount Paid',
        compute='_compute_payment_totals',
        store=True,
        currency_field='currency_id'
    )
    amount_due = fields.Monetary(
        string='Amount Due',
        compute='_compute_payment_totals',
        store=True,
        currency_field='currency_id',
        tracking=True
    )

    is_overdue = fields.Boolean(
        string='Is Overdue',
        compute='_compute_is_overdue',
        store=True,
        index=True
    )

    applied_discount_id = fields.Many2one(
        'subscription.discount',
        string='Applied Discount Rule',
        readonly=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Draft')) == _('Draft'):
                vals['name'] = self.env['ir.sequence'].next_by_code('subscription.invoice') or _('Draft')
        return super().create(vals_list)

    def write(self, vals):
        sensitive_fields = {'line_ids', 'partner_id', 'company_id', 'invoice_date', 'due_date', 'applied_discount_id'}
        if sensitive_fields.intersection(vals.keys()):
            for inv in self:
                if inv.state != 'draft':
                    raise UserError(_("You cannot modify invoice lines, customer, or accounting dates on a confirmed or processed invoice."))
        return super().write(vals)

    @api.depends('line_ids.price_subtotal', 'line_ids.price_total', 'line_ids.discount_amount')
    def _compute_amounts(self):
        for inv in self:
            inv.amount_untaxed = sum(inv.line_ids.mapped('price_subtotal'))
            inv.amount_discount = sum(inv.line_ids.mapped('discount_amount'))
            inv.amount_tax = sum(inv.line_ids.mapped('price_total')) - inv.amount_untaxed
            inv.amount_total = sum(inv.line_ids.mapped('price_total'))

    @api.depends('amount_total', 'payment_ids.amount')
    def _compute_payment_totals(self):
        for inv in self:
            total_paid = sum(inv.payment_ids.mapped('amount'))
            inv.amount_paid = total_paid
            inv.amount_due = max(0.0, inv.amount_total - total_paid)

    @api.depends('due_date', 'state', 'amount_due')
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for inv in self:
            inv.is_overdue = (inv.state in ('confirmed', 'partial')) and (inv.due_date < today) and (inv.amount_due > 0)

    # Actions: Confirm, Mark as Done, Cancel, Send, Print
    def action_confirm(self):
        for inv in self:
            if inv.state != 'draft':
                raise UserError(_("Only draft invoices can be confirmed."))
            if not inv.line_ids:
                raise ValidationError(_("Invoice must have lines before confirmation."))
            inv.state = 'confirmed'
            inv.message_post(body=_("Invoice %s confirmed.") % inv.name)

    def action_mark_as_done(self):
        for inv in self:
            if inv.state not in ('confirmed', 'partial'):
                raise UserError(_("Only confirmed or partially paid invoices can be marked as done."))
            if inv.amount_paid <= 0:
                raise ValidationError(_("Please record a payment amount before marking the invoice as done."))
            if inv.amount_due > 0.001:
                inv.state = 'partial'
                inv.message_post(body=_("Invoice %s marked as Partially Paid. Total Paid: %s, Remaining Due: %s.") % (
                    inv.name, inv.amount_paid, inv.amount_due
                ))
            else:
                inv.state = 'paid'
                inv.message_post(body=_("Invoice %s marked as Paid. Full payment received: %s.") % (
                    inv.name, inv.amount_paid
                ))

    def action_cancel(self):
        for inv in self:
            if inv.state == 'paid':
                raise UserError(_("You cannot cancel an invoice that has been fully paid."))
            inv.state = 'cancelled'
            inv.message_post(body=_("Invoice %s was cancelled.") % inv.name)

    def action_send(self):
        self.ensure_one()
        self.message_post(body=_("Invoice %s sent to customer %s.") % (self.name, self.partner_id.name))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Invoice Sent'),
                'message': _('Invoice has been marked as sent to customer.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_print(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Print Invoice'),
                'message': _('Invoice prepared for printing.'),
                'type': 'info',
                'sticky': False,
            }
        }
