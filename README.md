# Odoo x Make-A-Ton 9.0 Kochi Hackathon 2026

This repository is the project workspace for a subscription management solution built on Odoo 19.0. The planned implementation is split between Odoo's base addons and three custom addons under `custom_addons`.

## Planned addon architecture

| Addon | Responsibility |
| --- | --- |
| Odoo base addons | Core Odoo framework and standard addons used by the solution. The source checkout is in `odoo_base_addons/odoo`. |
| `subscription_catalog` | Define and maintain subscription plans, billing intervals, pricing, and the products or services included in each plan. |
| `subscription_sales` | Create subscriptions from sales, manage customer subscription records and lifecycle actions such as activation, renewal, upgrade, downgrade, and cancellation. |
| `subscription_billing` | Generate recurring invoices from active subscriptions, track billing periods, and handle billing-related status and history. |

The custom addons will live in `custom_addons/`. They are planned to be separate modules with dependencies between them: `subscription_catalog` provides plan data, `subscription_sales` uses the catalog to manage customer subscriptions, and `subscription_billing` bills those subscriptions. Exact Odoo module dependencies and supported workflows will be documented as implementation details are finalized.

## Repository layout

```text
.
├── custom_addons/       # Project-specific Odoo addons
└── odoo_base_addons/
    └── odoo/            # Odoo source and standard addons
```

## Development status

The subscription addon structure and responsibilities are currently planned. The three custom modules are not yet documented here as implemented or installable. Setup instructions, configuration, and usage guidance will be added as the modules are developed.
