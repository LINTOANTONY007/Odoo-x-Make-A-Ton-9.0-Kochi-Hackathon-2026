# Odoo Subscription Management

This repository contains an Odoo 19.0 source checkout and custom addon workspace for the Kochi Hackathon project. The repository name refers to the event; the included Odoo server is version 19.0.

## Repository contents

- `odoo-19.0/` contains the Odoo 19.0 server source, standard addons, and `odoo-bin` entry point.
- `custom_addons/subscription_billing/` contains a custom billing addon, version `19.0.1.0.0`.
- `custom_addons/requirement.txt` is currently empty.

## Implemented: `subscription_billing`

The billing addon defines custom subscription invoice and invoice-line records, payment records, discount rules, tax rules, and a finance summary dashboard. Its invoice records use the custom model `subscription.invoice`; they are not Odoo Accounting `account.move` invoices.

The addon currently provides these behaviors:

- Generate a draft invoice manually for an active subscription.
- Run daily recurring billing for active subscriptions whose next billing date is due. Invoice lines are copied from subscription lines, and an applicable percentage discount can be applied.
- Advance the next billing date using the plan's configured frequency and interval.
- Record payments against custom invoices, calculate paid and outstanding amounts, and mark an invoice paid when the balance is cleared.
- Confirm or cancel invoices, identify overdue invoices, and run a daily job to close expired subscriptions when their plan enables auto-close.
- View invoice, payment, and finance summary screens in the subscription menu.

The invoice send and print actions currently provide an in-app notification or message; they do not send an email or produce a PDF. The billing addon does not connect payments to a payment provider or post invoices to Odoo Accounting.

## Planned addons and current dependency gap

The intended solution is split across three custom addons:

| Module | Status | Intended responsibility |
| --- | --- | --- |
| `subscription_catalog` | Not present in this checkout | Plans, pricing, billing intervals, products, and shared subscription security/menu definitions. |
| `subscription_sales` | Not present in this checkout | Customer subscription records, sales integration, and subscription lifecycle. |
| `subscription_billing` | Present; depends on the two missing addons | Recurring billing, custom invoices and payments, discounts, taxes, and finance reporting. |

`subscription_billing/__manifest__.py` declares `subscription_sales` as a dependency. Its models also extend `subscription.subscription`, while its views, menus, and access rules reference external IDs from `subscription_sales` and `subscription_catalog`. Since those addons are not currently in `custom_addons/`, the billing addon cannot be installed from this checkout by itself. The Odoo source checkout also does not include a `sale_subscription` addon.

## Repository layout

```text
.
├── custom_addons/
│   ├── requirement.txt
│   └── subscription_billing/
│       ├── __manifest__.py
│       ├── data/
│       ├── models/
│       ├── security/
│       └── views/
└── odoo-19.0/
    ├── addons/
    └── odoo-bin
```

## Development status

`subscription_billing` is the only custom addon currently present. The catalog and sales addons are still required before the billing module can be installed and its flows exercised in Odoo. Setup instructions and verification steps can be added once the dependency modules and development environment are available.
