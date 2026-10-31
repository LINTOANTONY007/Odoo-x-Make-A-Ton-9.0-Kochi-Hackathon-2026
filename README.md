# Odoo Subscription Management

Subscription management addons developed for the Odoo x Make-A-Ton Kochi Hackathon. The repository includes Odoo 19.0 source in `odoo-19.0/` and custom addons in `custom_addons/`.

## Addons

The subscription workflow is split into three dependent addons. `user_password_security` is a separate, optional security addon.

| Addon | Purpose |
| --- | --- |
| `subscription_catalog` | Configure subscription plans, eligible service products, tax rules, and subscription access groups. |
| `subscription_sales` | Create quotation templates and customer subscriptions; manage the subscription lifecycle and customer portal. |
| `subscription_billing` | Create recurring custom invoices, record payments, apply discounts, and review finance summaries. |
| `user_password_security` | Configure password character requirements and enforce case-insensitive login uniqueness. |

The dependency chain is `subscription_catalog` → `subscription_sales` → `subscription_billing`. The password security addon depends on Odoo's `auth_password_policy` and can be installed independently.

## Subscription workflow

### Catalog

Create plans with a daily, weekly, monthly, or yearly billing frequency, interval count, recurring price, minimum quantity, availability dates, eligible products, and lifecycle policies. Products can be marked as subscription services and linked to plans. Catalog permissions distinguish subscription users from administrators.

### Sales and lifecycle

Quotation templates provide a default plan, validity period, terms, and preset product lines. Customer subscriptions include plan and product lines, billing and expiry dates, payment terms, and recurring totals.

Subscriptions move through **Draft**, **Quotation**, **Confirmed**, **Active**, **Paused**, and **Closed** states. Available actions include confirmation, activation, pause and resume, renewal, closure, and reset to draft. Confirmation checks plan availability and minimum quantity; pause, renewal, early closure, and auto-close behavior follow plan settings.

### Customer portal

After signing in, customers can use the **Subscriptions** card on `/my` to open `/my/subscriptions`. The card remains visible when no subscriptions exist. The list supports searching, filtering by status, sorting, and pagination. Customers can view a subscription and use available portal actions to confirm, pause, resume, or close it.

Portal lists are limited to subscriptions belonging to the customer's commercial partner or its child contacts. Subscription detail links use Odoo's portal access checks and access tokens.

### Billing

`subscription_billing` adds custom `subscription.invoice`, `subscription.invoice.line`, and `subscription.payment` records. Invoices can be generated manually for active subscriptions or by a daily scheduled job when the next billing date is due. Billing copies subscription lines and advances the next billing date using the plan interval. A second daily job closes expired subscriptions when their plan enables auto-close.

Discount rules support date and usage limits, minimum purchase or quantity criteria, and whole-subscription or product-specific scope. The recurring invoice flow currently applies percentage discounts; fixed discount rules are not applied by that flow. Invoice lines can calculate percentage or fixed taxes when tax rules are assigned.

Payments are entered against invoices and update paid and outstanding balances. Invoice states include **Draft**, **Confirmed**, **Partially Paid**, **Paid**, and **Cancelled**. The finance dashboard reports active subscription and invoice totals, collected revenue, outstanding balances, and overdue invoices.

## Account security

The catalog addon checks for case-insensitive duplicate logins and restricts non-administrators from creating staff accounts or assigning internal subscription staff groups. It also contains a fixed password check requiring more than 8 characters, uppercase and lowercase letters, and a special character.

For configurable password rules, install `user_password_security`. In **Settings → General Settings → Password Policy**, administrators can configure the minimum length and required lowercase, uppercase, numeric, and special characters. The addon also checks login uniqueness without regard to case.

## Known scope limits

- Subscription invoices are custom records; they are not Odoo Accounting `account.move` invoices and are not posted to Accounting.
- Payments are manual records. No payment provider or bank reconciliation is connected.
- Invoice send and print actions currently show a notification or log a message; they do not send an email or generate a PDF. The quotation action changes state and logs a message but does not send an email.
- Tax calculations are available on invoice lines, but recurring invoice generation does not automatically assign tax rules to the generated lines.
- `custom_addons/requirement.txt` is empty. Odoo's Python dependencies are listed in `odoo-19.0/requirements.txt`.

## Install and run

Set up PostgreSQL and an Odoo-compatible Python environment first. From the repository root, install the subscription workflow and optional password security addon with:

```bash
cd odoo-19.0
./odoo-bin --addons-path=addons,../custom_addons -d <database_name> -i subscription_billing,user_password_security
```

Odoo installs `subscription_catalog` and `subscription_sales` as dependencies of `subscription_billing`. To start the server after installation, omit the `-i` option:

```bash
./odoo-bin --addons-path=addons,../custom_addons -d <database_name>
```

The customer portal is available at `http://localhost:8069/my` after signing in.

## Repository layout

```text
.
├── custom_addons/
│   ├── subscription_catalog/
│   ├── subscription_sales/
│   ├── subscription_billing/
│   ├── user_password_security/
│   └── requirement.txt
└── odoo-19.0/
    ├── addons/
    ├── odoo/
    ├── requirements.txt
    └── odoo-bin
```
