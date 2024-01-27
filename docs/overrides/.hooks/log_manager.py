# Configure mkdocs logging
# Inspired by: https://github.com/mkdocs/mkdocs/issues/2876
import logging

from mkdocs import plugins


@plugins.event_priority(100)
def on_startup(*_, **__):
    logger = logging.getLogger("mkdocs")
    # Instance of ColorFormatter defined in mkdocs/__main__.py:
    formatter = logger.handlers[0].formatter
    formatter.datefmt = "%H:%M:%S"
    formatter._style = logging.PercentStyle("%(asctime)s [%(name)s] %(message)s")
