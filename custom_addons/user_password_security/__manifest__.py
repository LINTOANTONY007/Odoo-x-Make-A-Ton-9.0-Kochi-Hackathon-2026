# -*- coding: utf-8 -*-
{
    'name': 'User Password Security',
    'version': '19.0.1.0.0',
    'category': 'Extra Tools/Authentication',
    'summary': 'Enforces password security checks (>8 chars, uppercase, lowercase, special characters) and unique email validation',
    'description': """
User Password Security Policy & Unique Email Validation
=======================================================
Implements robust password security checks:
- Configurable minimum password length (uses standard Odoo auth_password_policy.minlength)
- Enforces uppercase letter(s)
- Enforces lowercase letter(s)
- Enforces special character(s) (including underscores and symbols)
- Enforces unique email/login per user account
- Integrates with Settings -> General Settings -> Password Policy
    """,
    'author': '',
    'depends': [
        'base',
        'auth_password_policy',
        'auth_signup',
    ],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
