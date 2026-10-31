# -*- coding: utf-8 -*-
import re
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.constrains('password')
    def _check_subscription_password_policy(self):
        """
        Password Policy:
        - Must be strictly more than 8 characters (> 8, i.e. min 9 characters)
        - Must contain at least one uppercase letter
        - Must contain at least one lowercase letter
        - Must contain at least one special character
        """
        for user in self:
            if not user.password:
                continue
            pwd = user.password
            if len(pwd) <= 8:
                raise ValidationError(_("Password must be more than 8 characters long."))
            if not re.search(r'[A-Z]', pwd):
                raise ValidationError(_("Password must contain at least one uppercase letter."))
            if not re.search(r'[a-z]', pwd):
                raise ValidationError(_("Password must contain at least one lowercase letter."))
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', pwd):
                raise ValidationError(_("Password must contain at least one special character."))

    @api.constrains('login')
    def _check_unique_email_login(self):
        """Ensure each email can belong to only one account."""
        for user in self:
            if user.login:
                duplicate = self.search([
                    ('id', '!=', user.id),
                    ('login', '=ilike', user.login.strip()),
                ], limit=1)
                if duplicate:
                    raise ValidationError(_("An account with the email '%s' already exists.") % user.login)

    @api.model_create_multi
    def create(self, vals_list):
        # Only admin can add a new member of staff
        for vals in vals_list:
            if not self.env.is_admin() and not self.env.user.has_group('subscription_catalog.group_subscription_admin'):
                # Check if trying to create an internal user (staff)
                admin_group = self.env.ref('subscription_catalog.group_subscription_admin', raise_if_not_found=False)
                user_group = self.env.ref('subscription_catalog.group_subscription_user', raise_if_not_found=False)
                internal_group = self.env.ref('base.group_user', raise_if_not_found=False)
                groups_to_check = [g.id for g in [admin_group, user_group, internal_group] if g]
                
                # If adding staff groups
                for g_id in groups_to_check:
                    if 'groups_id' in vals and any(op in (4, 6) for op in [cmd[0] for cmd in vals.get('groups_id', []) if len(cmd) > 1 and (cmd[1] == g_id or (cmd[0] == 6 and g_id in cmd[2]))]):
                        raise UserError(_("Only administrators can add a new member of staff."))
        return super().create(vals_list)
