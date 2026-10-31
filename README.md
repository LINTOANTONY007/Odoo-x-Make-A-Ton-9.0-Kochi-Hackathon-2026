# Odoo Subscription Management

An Odoo 19.0 subscription management project for the Kochi Hackathon. The repository includes the Odoo source checkout in `odoo-19.0/` and three custom addons in `custom_addons/`.

## Addon architecture

The addons are layered so each module builds on the previous one:

| Addon | Depends on | Main features |
| --- | --- | --- |
| `subscription_catalog` | Odoo `base`, `mail`, `product`, `portal`, `auth_signup` | Subscription plans, eligible products, tax rules, catalog access groups, and user account checks. |
| `subscription_sales` | `subscription_catalog` | Quotation templates, customer subscriptions and lines, subscription lifecycle, and customer portal pages. |
| `subscription_billing` | `subscription_sales` | Recurring custom invoices, invoice lines, payment records, discounts, billing schedules, and finance reporting. |

All three custom modules declare version `19.0.1.0.0`. Installing `subscription_billing` pulls in the catalog and sales addons through their manifest dependencies.

## Features

### Catalog and account controls

- Define plans with daily, weekly, monthly, or yearly billing frequency; interval count; recurring price; minimum quantity; availability dates; eligible products; and lifecycle policies.
- Mark service products as subscription products and associate them with available plans.
- Define percentage or fixed tax rules for use on subscription invoice lines.
- Restrict catalog configuration through subscription user and administrator groups.
- Validate passwords to require at least 9 characters, uppercase and lowercase letters, and a special character. Check login values for case-insensitive duplicates.
- Restrict non-administrators from creating staff accounts or assigning internal subscription staff groups.

### Sales and lifecycle

- Create quotation templates with a default plan, validity period, terms, products, quantities, and prices.
- Create subscriptions with customer, plan, product lines, billing dates, terms, and recurring totals.
- Move subscriptions through draft, quotation, confirmed, active, paused, and closed states. Actions support confirmation, activation, pause/resume, renewal, closure, and reset to draft, subject to plan policies.
- Use plan availability dates and minimum quantities as checks when confirming a subscription.

### Customer portal

Logged-in customers can open **My Account → Subscriptions** at `/my/subscriptions`. The portal home card remains visible when the customer has no subscriptions. The list includes subscription reference, plan, dates, state, and recurring total, with search, filters, sorting, and pagination. Customers can open a subscription detail page and use available actions to confirm, pause, resume, or close it.

Portal subscription lists are scoped to the logged-in customer's commercial partner and its child contacts. Detail pages use Odoo portal access checks and access tokens.

### Billing and finance

- Create custom `subscription.invoice` records manually for active subscriptions or generate them with a daily scheduled billing job when the next billing date is due.
- Build invoice lines from subscription lines, calculate line subtotals and taxes, and advance the next billing date using the plan's billing frequency and interval.
- Define discounts with date windows, usage limits, minimum purchase or quantity rules, and product scope. Recurring invoice generation currently applies percentage discounts; fixed discount rules are not applied by that flow.
- Record payments manually against invoices, track paid and due balances, and represent draft, confirmed, partially paid, paid, or cancelled invoice states.
- Identify overdue invoices, close expired subscriptions when the plan enables auto-close, and view active subscription and invoice totals in the finance dashboard.

## Current limitations

- Subscription invoices are custom records (`subscription.invoice`), not Odoo Accounting `account.move` invoices. They are not posted to Accounting.
- Payment records are manual entries; no payment provider or bank reconciliation is connected.
- Invoice send and print actions currently show an in-app notification or log a message; they do not send an email or generate a PDF.
- Tax rules and invoice-line tax calculations exist, but the recurring invoice generator does not automatically assign tax rules to generated lines.
- The quotation action changes the subscription state and logs a message; it does not send a quotation email.
- `custom_addons/requirement.txt` is empty. Odoo's Python dependencies are listed in `odoo-19.0/requirements.txt`.

## Install and run

Use a configured PostgreSQL database and an Odoo-compatible Python environment. From the repository root, install the custom billing addon and its dependencies with:

```bash
cd odoo-19.0
./odoo-bin --addons-path=addons,../custom_addons -d <database_name> -i subscription_billing
```

To start Odoo after installation, omit `-i subscription_billing`:

```bash
./odoo-bin --addons-path=addons,../custom_addons -d <database_name>
```

The portal is available to authenticated portal users at `http://localhost:8069/my`; the Subscriptions card links to `/my/subscriptions`.

## Repository layout

```text
.
├── custom_addons/
│   ├── requirement.txt
│   ├── subscription_catalog/
│   ├── subscription_sales/
│   └── subscription_billing/
└── odoo-19.0/
    ├── addons/
    ├── odoo/
    └── odoo-bin
```
