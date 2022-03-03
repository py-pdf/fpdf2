#!/usr/bin/env python3

# LICENSE: CC-0
# INSTALL: pip install agithub jinja2
# USAGE:
#   export GITHUB_TOKEN=...
#   ./build_contributors_html_page.py $org/$repo

# API DOC: https://developer.github.com/v3/issues/

import argparse
import logging
import os
import sys

from agithub.GitHub import GitHub
from agithub.base import IncompleteRequest
from jinja2 import Environment, FileSystemLoader

THIS_SCRIPT_PARENT_DIR = os.path.dirname(os.path.realpath(__file__))


def main():
    if "GITHUB_TOKEN" not in os.environ:
        raise RuntimeError("Environment variable GITHUB_TOKEN must be defined")
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(filename)s:%(lineno)d [%(levelname)s] %(message)s",
    )
    logging.getLogger("agithub.GitHub").setLevel(logging.DEBUG)
    args = parse_args()
    ag = GitHubAPIWrapper(token=os.environ["GITHUB_TOKEN"])
    org, repo = args.org_repo.split("/")
    print("Fetching all issues...")
    issues = ag.repos[org][repo].issues.get(state="all")
    print("Now retrieving each user location...")
    user_locations = {}
    for issue in issues:
        user_login = issue["user"]["login"]
        if user_login not in user_locations:
            user_locations[user_login] = {
                "location": ag.users[user_login].get()["location"],
                "issues": 0,
                "pulls": 0,
            }
        if "pull_request" in issue:
            user_locations[user_login]["pulls"] += 1
        else:
            user_locations[user_login]["issues"] += 1
    print("Now generating the HTML page...")
    env = Environment(loader=FileSystemLoader(THIS_SCRIPT_PARENT_DIR), autoescape=True)
    template = env.get_template("contributors.html.jinja2")
    out_filepath = os.path.join(THIS_SCRIPT_PARENT_DIR, "contributors.html")
    with open(out_filepath, "w", encoding="utf-8") as out_file:
        out_file.write(
            template.render(org_repo=args.org_repo, user_locations=user_locations)
        )


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter, allow_abbrev=False
    )
    parser.add_argument("org_repo")
    return parser.parse_args()


# Below are some utility methods to enhance the agithub library:


class GitHubAPIWrapper(GitHub):
    def __init__(self, *args, ignore_403s=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.ignore_403s = ignore_403s

    def __getattr__(self, key):
        return IncompleteRequestWrapper(self.client, self.ignore_403s).__getattr__(key)

    __getitem__ = __getattr__


class IncompleteRequestWrapper(IncompleteRequest):
    def __init__(self, client, ignore_403s):
        super().__init__(client)
        self.ignore_403s = ignore_403s

    def __getattr__(self, key):
        result = super().__getattr__(key)
        if key in self.client.http_methods:
            return HTTPRequester(result, self.ignore_403s)
        return result

    __getitem__ = __getattr__


class HTTPRequester:
    """
    Callable, providing:
    - auto pages fetching when result count is > 100
    - raise exceptions on HTTP errors
    """

    MAX_RESULTS_COUNT = 30

    def __init__(self, http_method_executer, ignore_403s):
        self.http_method_executer = http_method_executer
        self.ignore_403s = ignore_403s

    def __call__(self, *args, **kwargs):
        all_results, page = [], 1
        while len(all_results) % self.MAX_RESULTS_COUNT == 0:
            result = self._fetch(*args, page=page, **kwargs)
            if not isinstance(result, list):
                return result
            if len(result) == 0:
                return all_results
            all_results.extend(result)
            page += 1
        return all_results

    def _fetch(self, *args, **kwargs):
        http_code, response = self.http_method_executer(*args, **kwargs)
        if http_code == 403 and self.ignore_403s:
            print(f"HTTP {http_code}: {response['message']}", file=sys.stderr)
            return []
        if http_code != 200:
            raise RuntimeError(f"HTTP code: {http_code}: {response}")
        return response


if __name__ == "__main__":
    main()
