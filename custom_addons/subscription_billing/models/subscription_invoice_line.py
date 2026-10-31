from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class SubscriptionInvoiceLine(models.Model):
    _name = 'subscription.invoice.line'
    _description = 'Subscription Invoice Line'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    invoice_id = fields.Many2one(
        'subscription.invoice',
        string='Invoice',
        required=True,
        ondelete='cascade',
        index=True
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True
    )
    name = fields.Char(string='Description', required=True)
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    unit_price = fields.Float(string='Unit Price', required=True)
    discount = fields.Float(string='Discount (%)', default=0.0)
    discount_amount = fields.Monetary(
        string='Discount Amount',
        compute='_compute_line_amounts',
        store=True,
        currency_field='currency_id'
    )

    tax_ids = fields.Many2many(
        'subscription.tax',
        'subscription_invoice_line_tax_rel',
        'line_id',
        'tax_id',
        string='Taxes'
    )
    price_subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_line_amounts',
        store=True,
        currency_field='currency_id'
    )
    price_total = fields.Monetary(
        string='Total',
        compute='_compute_line_amounts',
        store=True,
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='invoice_id.currency_id',
        readonly=True
    )

    @api.depends('quantity', 'unit_price', 'discount', 'tax_ids.amount', 'tax_ids.tax_type')
    def _compute_line_amounts(self):
        for line in self:
            base_amount = line.quantity * line.unit_price
            disc_amt = base_amount * (line.discount / 100.0)
            net_subtotal = base_amount - disc_amt
            line.discount_amount = disc_amt
            line.price_subtotal = net_subtotal

            # Compute taxes
            tax_sum = 0.0
            for tax in line.tax_ids:
                if tax.tax_type == 'percent':
                    tax_sum += net_subtotal * (tax.amount / 100.0)
                else:  # fixed
                    tax_sum += tax.amount * line.quantity
            line.price_total = net_subtotal + tax_sum

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.display_name
            self.unit_price = self.product_id.lst_price

    @api.constrains('quantity')
    def _check_quantity(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_("Invoice line quantity must be greater than zero."))

    def write(self, vals):
        for line in self:
            if line.invoice_id.state != 'draft':
                raise UserError(_("You cannot modify line quantities, prices, or taxes on a confirmed or processed invoice."))
        return super().write(vals)

    def unlink(self):
        for line in self:
            if line.invoice_id.state != 'draft':
                raise UserError(_("You cannot delete lines from a confirmed or processed invoice."))
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            inv_id = vals.get('invoice_id')
            if inv_id:
                inv = self.env['subscription.invoice'].browse(inv_id)
                if inv.state != 'draft':
                    raise UserError(_("You cannot add lines to a confirmed or processed invoice."))
        return super().create(vals_list)
