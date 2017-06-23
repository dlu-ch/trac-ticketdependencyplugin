# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Daniel Lutz <dlu-ch@users.noreply.github.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

# Usage:
#
#   python setup.py extract_messages    # update catalog template file (ticketdependency/locale/messages.pot)
#   python setup.py update_catalog      # regenerate the various string catalogs (ticketdependency/locale/*/LC_MESSAGES/messages.po)
#   python setup.py compile_catalog -f  # generate one compiled catalogs (message.mo files)
#
#   python setup.py egg_info
#   python setup.py bdist_egg

import setuptools
from babel.messages import frontend as babel  # Debian: python-pybabel

NAME = 'TicketDependencyPlugin'
PACKAGE = 'ticketdependency'
VERSION = '0.1'

setuptools.setup(
    name=NAME,
    version=VERSION,
    description="Support for (directed) dependencies between Trac tickets",

    keywords=["trac", "plugin", "ticket", "cross-reference"],
    author="Daniel Lutz",
    url="https://trac-hacks.org/wiki/TicketDependencyPlugin",
    license = "3-Clause BSD",

    packages=[PACKAGE],
    include_package_data=True,
    package_data={
        PACKAGE: [
            'locale/*/LC_MESSAGES/*.po',
            'locale/*/LC_MESSAGES/*.mo',
        ]
    },

    # Babel integration (see setup.cfg for configuration)
    # http://babel.pocoo.org/en/latest/setup.html#setup-integration
    cmdclass = {
        'compile_catalog': babel.compile_catalog,
        'extract_messages': babel.extract_messages,
        'init_catalog': babel.init_catalog,
        'update_catalog': babel.update_catalog
    },

    entry_points={
        'trac.plugins': [
            '{pkg}.web_ui = {pkg}.web_ui'.format(pkg=PACKAGE),
            '{pkg}.api = {pkg}.api'.format(pkg=PACKAGE)
        ]
    },
)

