# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Daniel Lutz <dlu-ch@users.noreply.github.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import pkg_resources
import trac.core
import trac.env
import trac.ticket.api
import trac.ticket.model
import trac.util.translation
import model

_, add_domain = trac.util.translation.domain_functions("ticketdependency", ("_", "add_domain"))

class TicketDependencyPlugin(trac.core.Component):
    """Extend custom field for ids of tickets a tickets depends on"""

    trac.core.implements(
        trac.env.IEnvironmentSetupParticipant,
        trac.ticket.api.ITicketManipulator)

    def __init__(self):
        locale_dir = pkg_resources.resource_filename(__name__, "locale")  # path of locale directory
        add_domain(self.env.path, locale_dir)

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self.upgrade_environment(self.env.get_db_cnx())

    def environment_needs_upgrade(self, db):
        for field in model.CUSTOM_FIELDS:
            if field["name"] not in self.config["ticket-custom"]:
                return True
        return False

    def upgrade_environment(self, db):
        custom = self.config["ticket-custom"]
        for field in model.CUSTOM_FIELDS:
            if field["name"] not in custom:
                custom.set(field["name"], field["type"])
                for key, value in field["properties"]:
                    custom.set(key, value)
                self.config.save()

    # ITicketManipulator methods
    def prepare_ticket(self, req, ticket, fields, actions):
        pass

    def validate_ticket(self, req, ticket):
        prop = ("ticket-custom", "ticketref.label")

        subticket_ids, invalid_tokens = model.parse_field_value(ticket[model.TICKETREF])

        for invalid_token in sorted(invalid_tokens):
            msg = _('Not a (decimal) ticked ID: {token}').format(
                token=repr(invalid_token).strip('u'))
            yield self.env.config.get(*prop), msg

        if ticket.id in subticket_ids:
            msg = _('Ticket must not depend on itself')
            yield self.env.config.get(*prop), msg

        for subticket_id in sorted(subticket_ids):
            try:
                trac.ticket.model.Ticket(self.env, subticket_id)
            except Exception, err:
                yield self.env.config.get(*prop), err

        # normalize
        ticket[model.TICKETREF] = model.field_value_from_ticket_ids(subticket_ids)

