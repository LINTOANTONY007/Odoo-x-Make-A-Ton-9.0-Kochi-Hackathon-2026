# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SubscriptionPayment(models.Model):
    _name = 'subscription.payment'
    _description = 'Subscription Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'payment_date desc, id desc'

    name = fields.Char(
        string='Payment Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    invoice_id = fields.Many2one(
        'subscription.invoice',
        string='Invoice',
        required=True,
        ondelete='cascade',
        tracking=True,
        index=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        related='invoice_id.partner_id',
        store=True,
        readonly=True
    )
    payment_method = fields.Selection([
        ('credit_card', 'Credit / Debit Card'),
        ('bank_transfer', 'Bank Transfer (Wire)'),
        ('paypal', 'PayPal / Online'),
        ('cash', 'Cash'),
        ('other', 'Other'),
    ], string='Payment Method', default='credit_card', required=True, tracking=True)
    amount = fields.Monetary(
        string='Payment Amount',
        required=True,
        currency_field='currency_id',
        tracking=True
    )
    payment_date = fields.Date(
        string='Payment Date',
        default=fields.Date.context_today,
        required=True,
        tracking=True
    )
    note = fields.Text(string='Payment Note / Memo')
    company_id = fields.Many2one(
        'res.company',
        related='invoice_id.company_id',
        readonly=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='invoice_id.currency_id',
        readonly=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('subscription.payment') or _('New')
        records = super().create(vals_list)
        for rec in records:
            rec.invoice_id.message_post(
                body=_("Payment of %s received via %s on %s. Note: %s") % (
                    rec.amount, dict(rec._fields['payment_method'].selection).get(rec.payment_method),
                    rec.payment_date, rec.note or 'N/A'
                )
            )
        return records

    @api.constrains('amount')
    def _check_payment_amount(self):
        for pay in self:
            if pay.amount <= 0:
                raise ValidationError(_("Payment amount must be strictly greater than zero."))
