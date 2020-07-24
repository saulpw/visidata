# Release process for the next `stable` version

1. Merge `stable` to `develop` (if necessary)

2. Verify that VisiData is up-to-date:
    * vdmenu
    * plugins.jsonl

2. Verify that documentation/docstrings are up-to-date on features and functionality

    a. manpage;

    b. visidata.org; (formats?)

    c. CHANGELOG;

    d. patrons.tsv;

    e. contributors.tsv

3. Ensure `develop` automated tests run correctly with dev/test.sh

4. Go through the manual tests checklist

5. Verify that setup.py is up-to-date with requirements.

    a. Review current dependency versions and if a new version of Python has been released.

    b. Update any new plugins or extras in setup.py

5. Set version number to next most reasonable number (v#.#.#)

   a. add to front of CHANGELOG, along with the release date and bullet points of major changes;

   b. update the date in the manpage;

   c. update version number on README and front page of website (update dates here too);

   d. bump version in `__version__` in source code (visidata/main.py, visidata/__init__.py) and setup.py;

6. Run dev/mkman.sh to build the manpage and updated website

7. Push `develop` to testpypi

    a. set up a ~/.pypirc

    ```
    [distutils]
    index-servers=
        pypi
        testpypi
    [pypi]
    repository:https://upload.pypi.org/legacy/
    username:
    password:

    [testpypi]
    repository: https://test.pypi.org/legacy
    username:
    password:
    ```

    b. push to testpypi

    ```
    python3 setup.py sdist
    twine upload dist/* -r testpypi
    ```

8. Test install from testpypi

   a. on virgin instance

   b. on mac and linux

   c. See if windows works

   d. from git clone

   ```
   pip3 install --extra-index-url https://test.pypi.org/project visidata
   ```

9. Merge `develop` to stable

10. Merge `stable` back into other branches

    a. if the branch works with minimal conflicts, keep the branch

    b. otherwise, clean out the branch


11. Push code to stable

12. Push stable to pypi

```
twine upload dist/*
```

13. Test install/upgrade from pypi

  a. Build and deploy the website

   b. Ask someone else to test install

14. Create a tag `v#.#.#` for that commit

```
git tag v#.#.#
git push --tags
```

15. Write up the release notes and add it to `www/releases.md`

16. Upload new motd

17. Run dev/mkwww.sh to rebuild the website and deploy with dev/deploy_www.sh

18. Comb through issues and close the ones that have been solved, referencing the version number

19. Post github release notes on tinyletter.

20. Update the other distributions.

# conda

1. Fork https://github.com/conda-forge/visidata-feedstock

2. Update the VisiData version and sha256.

3. Make any necessary removals, additions or modifications to the dependencies -> note that a dependency must be part of conda.

4. Make a PR.

5. Comment `@conda-forge-admin, please rerender` in the PR.


# Homebrew

1. Update the link in url to the new visidata tar.gz file.
2. Download the tarfile and obtain its new sha256
```
shasum -a 256
```
3. Check each dependency and see if it has been updated. If so, update the url and sha256 for the newest version.
4. Install visidata using `pip3 install visidata --upgrade` and note down all of the new dependencies. 
5. Obtain their urls and sha256 and add them to the formula
6. Change their urls from `pypi.python.org` to `files.pythonhosted.org`.
7. Test the formula with `brew install --build-from-source visidata`. Fix as needed.
8. Audit the formula with `brew audit --new-formula visidata`
9. Add and commit the formula.

## Debian
1. Obtain the visidata tar.gz file from pypi
2. tar -xzmf visidata.tar.gz
3. cp visidata.ver.tar.gz visidata_ver.orig.tar.gz
4. cd visidata/
5. Place there the contents of the debian directory from github.com/saulpw/visidata
6. Update changelog
```
dch -v version-revision
```
7. Run debuild. Fix errors as they come up
8. If a package fails to import a module, it must be added to the build dependencies as python3-modules
9. cd ..
10. Sign the changes files
```
debsign -k keycode visidata_ver.changes
```
11. Upload to debian mentors
```
dput mentors visidata_ver.changes
```

## deb-vd
9. Enter saulpw/deb-vd.
10. Run the command reprepro includedeb sid new-vd.deb
