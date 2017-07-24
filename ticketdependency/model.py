# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Daniel Lutz <dlu-ch@users.noreply.github.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import re
import trac.util.translation

_, add_domain = trac.util.translation.domain_functions("ticketdependency", ("_", "add_domain"))

# Name of custom field of tickets a ticked depends on (string).
# Is a list of decimal representations of ticket IDs, separated by space or comma.
# Invalid elements of the lists are ignored.
TICKETREF = 'ticketref'

TICKETREF_LABEL = 'Dependencies'
_('Dependencies')

TOKEN_SEPARATOR_REGEX = re.compile('[, ]+')

CUSTOM_FIELDS = [  # like TracTicketReference
    {
        'name': TICKETREF,
        'type': 'textarea',
        'properties': [
            ('ticketref.label', TICKETREF_LABEL),
            ('ticketref.cols', '68'),
            ('ticketref.rows', '1'),
        ],
    },
]


def query_supertickets(env, ticket_id):
    """
    Returns duplicate-free tuple of the IDs other than ``ticket_id`` of all tickets whose
    custom field ``TICKETREF`` contains ``ticket_id``.

    type ticket_id: int
    rtype: set(int)
    """
    with env.db_query as db:
        superticket_ids = db(
            (
                "SELECT ticket FROM ticket_custom "
                "WHERE name = %s "
                "AND ticket != %s "
                "AND ' ' || replace(value, ',', ' ') || ' ' LIKE %s "
            ),
            (TICKETREF, ticket_id, '% {} %'.format(ticket_id)))
        superticket_ids=set(t for (t,) in superticket_ids)
    return superticket_ids


def tokens_from_field_value(value):
    """
    Returns the set of all tokens (largest substrings containing neither space nor comma) in value.

    param value: value of custom field TICKETREF
    type value: str
    rtype: set(str)
    """
    return set(t for t in TOKEN_SEPARATOR_REGEX.split(value) if t)


def parse_field_value(value):
    ids = set()
    invalid_tokens = set()
    if value:
        for token in tokens_from_field_value(value):
            try:
                ids.add(int(token, 10))
            except ValueError:
                invalid_tokens.add(token)
    return ids, invalid_tokens


def ticket_ids_from_field_value(value):
    """
    Returns the set of all ticket IDs in value, ignoring all invalid tokens.

    param value:
        value of custom field ``TICKETREF``
        (decimal representations of ticket IDs, separated by space or comma or ``None``)
    type value: str | None
    rtype: set(int)
    """
    ids, _ = parse_field_value(value)
    return ids


def field_value_from_ticket_ids(ticket_ids):
    return ' '.join(str(i) for i in sorted(set(ticket_ids)))


assert parse_field_value('   5   ,,a,b, c\td\n  123,,, 0123, 0x123   ') \
    == (set([5, 123]), set(['a', 'b', 'c\td\n', '0x123']))
assert parse_field_value('   ') == (set(), set())
assert parse_field_value(None) == (set(), set())

assert field_value_from_ticket_ids(ticket_ids_from_field_value('0,1 234')) == '0 1 234'
