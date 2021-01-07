Docs generation & publication on GitHub Pages is performed for every new commit on the `master` branch
throught the GitHub Actions pipeline.

Please refer to the [development manual](https://alexanderankin.github.io/pyfpdf/Development.html#documentation)
for more information.

Any non-automatically generated and separately maintained documentation should
be added into a separate folder that is ignored by `MANIFEST.in` such that it
is not packaged with a source distribution of this package (but available
through hosting elsewhere on a different service, maybe like readthedocs).

