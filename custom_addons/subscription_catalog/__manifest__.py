# -*- coding: utf-8 -*-
{
    'name': 'Subscription Catalog',
    'version': '19.0.1.0.0',
    'category': 'Sales/Subscription',
    'summary': 'Subscription Plans, Products, Variants and Access Control',
    'description': """ Subscription Catalog Management """,
    'author': '',
    'depends': [
        'base',
        'mail',
        'product',
        'portal',
        'auth_signup',
    ],
    'data': [
        'security/subscription_security.xml',
        'security/ir.model.access.csv',
        'data/subscription_plan_data.xml',
        'views/subscription_menus.xml',
        'views/subscription_plan_views.xml',
        'views/subscription_product_views.xml',
        'views/subscription_tax_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
