# -*- coding: utf-8 -*-
{
    'name': 'Subscription Sales',
    'version': '19.0.1.0.0',
    'category': 'Sales/Subscription',
    'summary': 'Quotation Templates, Subscriptions, and Contract Lifecycle',
    'description': """
Subscription Sales & Lifecycle
    """,
    'author': '',
    'depends': [
        'base',
        'mail',
        'portal',
        'subscription_catalog',
    ],
    'data': [
        'security/subscription_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/subscription_quotation_template_views.xml',
        'views/subscription_subscription_views.xml',
        'views/subscription_portal_templates.xml',
        'views/subscription_menus.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
