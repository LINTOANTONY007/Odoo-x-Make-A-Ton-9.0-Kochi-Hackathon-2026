# -*- coding: utf-8 -*-
from collections import OrderedDict

from odoo import http, _
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.http import request
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class CustomerPortal(portal.CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'subscription_count' in counters:
            Subscription = request.env['subscription.subscription']
            partner = request.env.user.partner_id
            values['subscription_count'] = (
                Subscription.search_count(self._prepare_subscriptions_domain(partner))
                if Subscription.has_access('read')
                else 0
            )
        return values

    def _prepare_subscriptions_domain(self, partner):
        return [
            ('partner_id', 'child_of', [partner.commercial_partner_id.id]),
        ]

    def _get_subscription_searchbar_sortings(self):
        return {
            'date': {'label': _('Start Date'), 'order': 'start_date desc, id desc'},
            'name': {'label': _('Reference'), 'order': 'name asc, id asc'},
            'stage': {'label': _('Status'), 'order': 'stage asc, id desc'},
            'amount_total': {'label': _('Total'), 'order': 'amount_total desc, id desc'},
        }

    def _get_subscription_searchbar_filters(self):
        return {
            'all': {'label': _('All'), 'domain': []},
            'active': {'label': _('Active'), 'domain': [('stage', '=', 'active')]},
            'paused': {'label': _('Paused'), 'domain': [('stage', '=', 'paused')]},
            'quotation': {'label': _('Quotations / Draft'), 'domain': [('stage', 'in', ['draft', 'quotation'])]},
            'confirmed': {'label': _('Confirmed'), 'domain': [('stage', '=', 'confirmed')]},
            'closed': {'label': _('Closed'), 'domain': [('stage', '=', 'closed')]},
        }

    def _get_subscription_searchbar_inputs(self):
        return {
            'all': {'input': 'all', 'label': _('Search in All')},
            'name': {'input': 'name', 'label': _('Search in Reference')},
            'plan': {'input': 'plan', 'label': _('Search in Plan')},
        }

    def _prepare_subscription_portal_rendering_values(
        self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='all', **kwargs
    ):
        Subscription = request.env['subscription.subscription']
        partner = request.env.user.partner_id
        values = self._prepare_portal_layout_values()
        url = "/my/subscriptions"

        domain = self._prepare_subscriptions_domain(partner)

        searchbar_sortings = self._get_subscription_searchbar_sortings()
        if not sortby or sortby not in searchbar_sortings:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = self._get_subscription_searchbar_filters()
        if not filterby or filterby not in searchbar_filters:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        searchbar_inputs = self._get_subscription_searchbar_inputs()
        if search and search_in:
            if search_in == 'all':
                domain += ['|', ('name', 'ilike', search), ('plan_id.name', 'ilike', search)]
            elif search_in == 'name':
                domain += [('name', 'ilike', search)]
            elif search_in == 'plan':
                domain += [('plan_id.name', 'ilike', search)]

        if date_begin and date_end:
            domain += [('start_date', '>=', date_begin), ('start_date', '<=', date_end)]

        count = Subscription.search_count(domain) if Subscription.has_access('read') else 0

        pager = portal_pager(
            url=url,
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby,
                'filterby': filterby,
                'search': search,
                'search_in': search_in,
            },
            total=count,
            page=page,
            step=self._items_per_page,
        )

        subscriptions = (
            Subscription.search(
                domain,
                order=order,
                limit=self._items_per_page,
                offset=pager['offset'],
            )
            if Subscription.has_access('read')
            else Subscription
        )

        values.update({
            'date': date_begin,
            'subscriptions': subscriptions.sudo() if Subscription.has_access('read') else Subscription,
            'page_name': 'subscriptions',
            'pager': pager,
            'default_url': url,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
            'search': search,
        })
        return values

    @http.route(['/my/subscriptions', '/my/subscriptions/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_subscriptions(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='all', **kwargs):
        values = self._prepare_subscription_portal_rendering_values(
            page=page,
            date_begin=date_begin,
            date_end=date_end,
            sortby=sortby,
            filterby=filterby,
            search=search,
            search_in=search_in,
            **kwargs
        )
        request.session['my_subscriptions_history'] = values['subscriptions'].ids[:100]
        return request.render("subscription_sales.portal_my_subscriptions", values)

    @http.route(['/my/subscriptions/<int:subscription_id>'], type='http', auth="public", website=True)
    def portal_subscription_page(self, subscription_id, access_token=None, report_type=None, download=False, **kw):
        try:
            subscription_sudo = self._document_check_access('subscription.subscription', subscription_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(
                model=subscription_sudo,
                report_type=report_type,
                report_ref='subscription_sales.action_report_subscription',
                download=download,
            )

        backend_url = f'/odoo/action-{subscription_sudo._get_portal_return_action().id}/{subscription_sudo.id}'
        values = {
            'subscription': subscription_sudo,
            'report_type': 'html',
            'backend_url': backend_url,
            'res_company': subscription_sudo.company_id,
        }
        values = self._get_page_view_values(subscription_sudo, access_token, values, 'my_subscriptions_history', False, **kw)
        return request.render("subscription_sales.portal_subscription_page", values)

    @http.route(['/my/subscriptions/<int:subscription_id>/confirm'], type='http', auth="public", methods=['POST', 'GET'], website=True)
    def portal_subscription_confirm(self, subscription_id, access_token=None, **kwargs):
        try:
            subscription_sudo = self._document_check_access('subscription.subscription', subscription_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if subscription_sudo.stage in ('draft', 'quotation'):
            subscription_sudo.action_confirm()
            return request.redirect(subscription_sudo.get_portal_url(query_string='&success=confirmed'))
        return request.redirect(subscription_sudo.get_portal_url())

    @http.route(['/my/subscriptions/<int:subscription_id>/pause'], type='http', auth="public", methods=['POST'], website=True)
    def portal_subscription_pause(self, subscription_id, access_token=None, **kwargs):
        try:
            subscription_sudo = self._document_check_access('subscription.subscription', subscription_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if subscription_sudo.stage == 'active' and (not subscription_sudo.plan_id or subscription_sudo.plan_id.allow_pause):
            subscription_sudo.action_pause()
            return request.redirect(subscription_sudo.get_portal_url(query_string='&success=paused'))
        return request.redirect(subscription_sudo.get_portal_url())

    @http.route(['/my/subscriptions/<int:subscription_id>/resume'], type='http', auth="public", methods=['POST'], website=True)
    def portal_subscription_resume(self, subscription_id, access_token=None, **kwargs):
        try:
            subscription_sudo = self._document_check_access('subscription.subscription', subscription_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if subscription_sudo.stage == 'paused':
            subscription_sudo.action_resume()
            return request.redirect(subscription_sudo.get_portal_url(query_string='&success=resumed'))
        return request.redirect(subscription_sudo.get_portal_url())

    @http.route(['/my/subscriptions/<int:subscription_id>/close'], type='http', auth="public", methods=['POST'], website=True)
    def portal_subscription_close(self, subscription_id, access_token=None, close_reason=None, **kwargs):
        try:
            subscription_sudo = self._document_check_access('subscription.subscription', subscription_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if subscription_sudo.stage in ('confirmed', 'active', 'paused'):
            subscription_sudo.action_close(reason=close_reason or _("Closed by customer via portal"))
            return request.redirect(subscription_sudo.get_portal_url(query_string='&warning=closed'))
        return request.redirect(subscription_sudo.get_portal_url())
