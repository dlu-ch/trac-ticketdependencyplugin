# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Daniel Lutz <dlu-ch@users.noreply.github.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import pkg_resources
import trac.core
import trac.web.api
import trac.web.chrome
import trac.resource
import trac.ticket.model
import trac.util.text
import trac.util.translation
import genshi.builder
import model

_, add_domain = trac.util.translation.domain_functions("ticketdependency", ("_", "add_domain"))


def hyperlink_to_ticket(req, ticket, text_format):
    # ticket: trac.ticket.model.Ticket
    title = trac.util.text.shorten_line(ticket["summary"])
    return genshi.builder.tag.a(
        text_format.format(id=ticket.id, title=title),
        title=title,
        class_=ticket["status"],
        href=req.href.ticket(ticket.id))


class TicketDependencyTemplateStreamFilter(trac.core.Component):
    trac.core.implements(trac.web.api.ITemplateStreamFilter)

    def __init__(self):
        locale_dir = pkg_resources.resource_filename(__name__, "locale")  # path of locale directory
        add_domain(self.env.path, locale_dir)

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename in ('ticket.html', 'ticket_box.html', 'ticket_preview.html'):
            self._render_ticket_fields(req, data)
        elif filename in ('query.html', 'query_results.html'):
            self._render_query(req, data)

        return stream

    def _render_ticket_fields(self, req, data):
        for field in data.get("fields", []):
            if field["name"] == model.TICKETREF:
                field["label"] = _(model.TICKETREF_LABEL)
                ticket = data["ticket"]

                rendered_lines = []
                subticket_ids = model.ticket_ids_from_field_value(ticket[model.TICKETREF])  # None if new
                if subticket_ids:
                    rendered_lines.append(self._link_ticket_list(req, subticket_ids))
                superticket_ids = model.query_supertickets(self.env, ticket.id)
                if superticket_ids:
                    rendered_lines.append(
                        self._link_ticket_list(req, superticket_ids, is_super=True,
                                               element_id='tref_ticketid_super'))
                rendered_lines = sum([[i, genshi.builder.tag.br()] for i in rendered_lines], [])[:-1]

                if rendered_lines:
                    field["rendered"] = genshi.builder.tag([
                        genshi.builder.tag.span(rendered_lines),
                        # U+25BA: BLACK RIGHT-POINTING POINTER
                        genshi.builder.tag.a(_(u'(A \u25BA B: A depends on B)'), style='float: right')
                    ])

        for changes in data.get("changes", []):
            # yellow box in tickets's Change History
            ticketref_change = changes.get("fields", {}).get(model.TICKETREF)
            if ticketref_change:
                self._render_ticketref_change(req, ticketref_change)

    def _render_ticketref_change(self, req, ticketref_change):
        # req: Request
        # ticketref_change: Dictionary describing modification of field model.TICKETREF

        old_ids = model.ticket_ids_from_field_value(ticketref_change.get("old"))
        new_ids = model.ticket_ids_from_field_value(ticketref_change.get("new"))

        comma = genshi.builder.tag.span(u', ')

        added_elements = []
        for ticket_id in sorted(new_ids - old_ids):
            ticket = self._create_ticket_from_id(ticket_id)
            if ticket:
                added_elements.append(hyperlink_to_ticket(req, ticket, '#{id}'))
        if added_elements:
            added_elements = sum([[i, comma] for i in added_elements], [])[:-1] + [
                genshi.builder.tag.span(' ' + _('added'))
            ]

        removed_elements = []
        for ticket_id in sorted(old_ids - new_ids):
            ticket = self._create_ticket_from_id(ticket_id)
            if ticket:
                removed_elements.append(hyperlink_to_ticket(req, ticket, '#{id}'))
        if removed_elements:
            removed_elements = sum([[i, comma] for i in removed_elements], [])[:-1] + [
                genshi.builder.tag.span(' ' + _('removed'))
            ]

        elements = added_elements
        if elements and removed_elements:
            elements.append(comma)
        elements.extend(removed_elements)
        if elements:
            ticketref_change["rendered"] = genshi.builder.tag.span(elements)
            ticketref_change["label"] = _(model.TICKETREF_LABEL)

    # for "Custom Query"
    def _render_query(self, req, data):
        fields_tref = data.get("fields", {}).get(model.TICKETREF)
        if fields_tref:
            # name of checkbox for filter and column title with "Show under each result"
            fields_tref["label"] = _(model.TICKETREF_LABEL)
            if fields_tref["type"] == u"textarea":
                if isinstance(data.get("all_columns"), list):
                    data["all_columns"].append(model.TICKETREF)

        # column title of result
        for header in data.get("headers", []):
            if header["name"] == model.TICKETREF:
                header["label"] = _(model.TICKETREF_LABEL)

    def _link_ticket_list(self, req, ticket_ids, is_super=False, element_id='tref_ticketid'):
        if not ticket_ids:
            return None

        if is_super:
            text_format = u'\u25C4 #{id}'  # U+25C4: BLACK LEFT-POINTING POINTER
        else:
            text_format = u'\u25BA #{id}'  # U+25BA: BLACK RIGHT-POINTING POINTER

        text_format += ' - {title}'
        separator = genshi.builder.tag.br()

        elements = []
        for ticket_id in sorted(ticket_ids):
            ticket = self._create_ticket_from_id(ticket_id)
            if ticket:
                elements.append(hyperlink_to_ticket(req, ticket, text_format))
                elements.append(separator)
        elements = elements[:-1]

        return genshi.builder.tag.span(elements, id=element_id)

    def _create_ticket_from_id(self, ticket_id):
        try:
            return trac.ticket.model.Ticket(self.env, ticket_id)
        except trac.resource.ResourceNotFound:
            self.log.warn("ticket not found (ignored): {}".format(ticket_id))

