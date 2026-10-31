# -*- coding: utf-8 -*-
import re
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _get_all_password_params(self):
        """Fetch password security rules from system parameters."""
        params = self.env["ir.config_parameter"].sudo()
        return {
            "minlength": int(
                params.get_param("auth_password_policy.minlength") or 0
            ),
            "lower": int(params.get_param("password_security.lower", default=0)),
            "upper": int(params.get_param("password_security.upper", default=0)),
            "numeric": int(params.get_param("password_security.numeric", default=0)),
            "special": int(params.get_param("password_security.special", default=0)),
        }

    @api.model
    def get_password_policy(self):
        """Enrich frontend policy parameters with character classes."""
        data = super().get_password_policy()
        pwd_params = self._get_all_password_params()
        data.update({
            "password_lower": pwd_params["lower"],
            "password_upper": pwd_params["upper"],
            "password_numeric": pwd_params["numeric"],
            "password_special": pwd_params["special"],
        })
        return data

    def password_match_message(self):
        """Construct user-friendly error message based on active rules."""
        self.ensure_one()
        message = []
        pwd_params = self._get_all_password_params()
        if pwd_params["minlength"]:
            message.append(
                _("• Password must be at least %d character(s).", pwd_params["minlength"])
            )
        if pwd_params["upper"]:
            message.append(
                _("• Uppercase letter (at least %s character(s): A-Z)", pwd_params["upper"])
            )
        if pwd_params["lower"]:
            message.append(
                _("• Lowercase letter (at least %s character(s): a-z)", pwd_params["lower"])
            )
        if pwd_params["special"]:
            message.append(
                _("• Special character (at least %s character(s): e.g. !@#$%%^&*_-+=)", pwd_params["special"])
            )
        if pwd_params["numeric"]:
            message.append(
                _("• Numeric digit (at least %s digit(s): 0-9)", pwd_params["numeric"])
            )

        header = _("Password does not meet the security requirements:")
        return header + "\n" + "\n".join(message)

    def _check_password_rules(self, password):
        """Validate password against regex rules."""
        self.ensure_one()
        if not password:
            return True
        pwd_params = self._get_all_password_params()
        password_regex = [
            "^",
            "(?=.*?[a-z]){" + str(pwd_params["lower"]) + ",}",
            "(?=.*?[A-Z]){" + str(pwd_params["upper"]) + ",}",
            "(?=.*?\\d){" + str(pwd_params["numeric"]) + ",}",
            r"(?=.*?[\W_]){" + str(pwd_params["special"]) + ",}",
            ".{" + str(pwd_params["minlength"]) + ",}$",
        ]
        if not re.search("".join(password_regex), password):
            raise ValidationError(self.password_match_message())
        return True

    def _check_password_policy(self, passwords):
        """Hook into standard Odoo auth_password_policy."""
        if self.env.context.get("install_mode"):
            return True
        result = super()._check_password_policy(passwords)
        for password in passwords:
            if not password:
                continue
            for user in self:
                user._check_password_rules(password)
        return result

    def _set_password(self):
        """Intercept password setting across all entry points before encryption."""
        for user in self:
            if user.password:
                user._check_password_rules(user.password)
        super(ResUsers, self)._set_password()

    @api.constrains('login')
    def _check_unique_email_login(self):
        """Ensure each email/login can belong to only one account."""
        for user in self:
            if user.login:
                duplicate = self.with_context(active_test=False).search([
                    ('id', '!=', user.id),
                    ('login', '=ilike', user.login.strip()),
                ], limit=1)
                if duplicate:
                    raise ValidationError(_("An account with the email '%s' already exists.") % user.login)
