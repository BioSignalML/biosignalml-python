Releasing a new version
=======================

Update and commit HISTORY:::

  git log --summary --oneline v0.3.5..
  vi HISTORY

::

  git push
  git tag -m"Release v0.3.6" v0.3.6
  git push origin v0.3.6
  python setup.py sdist upload
