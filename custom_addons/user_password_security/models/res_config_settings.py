# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    password_lower = fields.Integer(
        string="Lowercase",
        default=0,
        config_parameter="password_security.lower",
        help="Require minimum number of lowercase letters",
    )
    password_upper = fields.Integer(
        string="Uppercase",
        default=0,
        config_parameter="password_security.upper",
        help="Require minimum number of uppercase letters",
    )
    password_numeric = fields.Integer(
        string="Numeric",
        default=0,
        config_parameter="password_security.numeric",
        help="Require minimum number of numeric digits",
    )
    password_special = fields.Integer(
        string="Special",
        default=0,
        config_parameter="password_security.special",
        help="Require minimum number of special characters",
    )
