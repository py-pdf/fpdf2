# Context: https://github.com/squidfunk/mkdocs-material/discussions/8252

from mkdocs.plugins import BasePlugin


class InvalidPageStructure(Exception):
    pass


class CheckTocPlugin(BasePlugin):
    def on_page_content(self, html, *, page, config, files):
        if len(page.toc) > 1:
            raise InvalidPageStructure(
                f'Page "{page.url}" has to many #top-level headings ({len(page.toc)}),'
                " Table Of Contents will be broken"
            )
