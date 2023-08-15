---
name: Bug report
about: Report some unexpected behaviour to help us improve
title: ''
labels: bug
assignees: ''
---
<!--
Hi there! Thank you for wanting to make fpdf2 better 😉.

Please perform a quick search first, in order to check if your problem has already been reported:
https://github.com/py-pdf/fpdf2/issues
-->

Describe the bug

**Error details**
If an exception is raised, it is very important that you provide the full error message.
Otherwise members of the fpdf2 community won't be able to help you with your problem.

**Minimal code**
Please include some minimal Python code reproducing your issue:
```python
from fpdf import FPDF

pdf = FPDF()
...
```
If you don't know how to build a minimal reproducible example, please check this tutorial: https://stackoverflow.com/help/minimal-reproducible-example

**Environment**
Please provide the following information:
* **Operating System**: Windows, Mac OSX, Linux flavour...
* **Python version**: you can get this information with `python --version`
* **`fpdf2` version used**: if you installed it with `pip`, you can get this information in `pip freeze` output

<!-- Bonus / recommended:

Often, there are bugfixes & other changes on fpdf2 git repo `master` branch
that have not been released yet. They are listed in the ChangeLog:
https://github.com/py-pdf/fpdf2/blob/master/CHANGELOG.md

Hence, please check that your bug is still present using the latest version of fpdf2 from the git repository,
by installing it this way:

    pip install git+https://github.com/py-pdf/fpdf2.git@master

-->
