# Release process for the next `stable` version

1. Merge `stable` to `develop` (if necessary)

2. Verify that documentation/docstrings are up-to-date on features and functionality

    a. CHANGELOG;

    b. manpage;

    c. visidata.org; (formats?)

3. Verify that VisiData is up-to-date:
    * help menu
    * plugins.jsonl

3. Ensure `develop` automated tests run correctly with dev/test.sh

4. Go through the manual tests checklist

5. Verify that setup.py is up-to-date with requirements.

    a. Review current dependency versions and if a new version of Python has been released.

    b. Update any new plugins or extras in setup.py

5. Set version number to next most reasonable number (v#.#.#)

   a. add to front of CHANGELOG, along with the release date and bullet points of major changes;

   b. update the date in the manpage;

   c. update version number on README

   d. bump version in `__version__` in source code (visidata/main.py, visidata/__init__.py) and setup.py;

6. Run dev/mkman.sh to build the manpage and updated website
    - Run ./mkmanhtml.sh, and move that to visidata.org:site/docs/man, and to visidata:docs/man.md

7. Merge `develop` to stable

8. Merge `stable` back into other branches

    a. if the branch works with minimal conflicts, keep the branch

    b. otherwise, clean out the branch


9. Push code to stable

10. Push `develop` to pypi

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


  Push to pypi
    ```
    python3 setup.py sdist bdist_wheel
    twine upload dist/*
    ```

11. Test install/upgrade from pypi

  a. Build and deploy the website

   b. Ask someone else to test install

12. Create a tag `v#.#.#` for that commit

```
git tag v#.#.#
git push --tags
```

13. Write up the release notes and add it to `www/releases.md`. Add it to index.md.

14. Upload new motd

15. Update the website by pushing to master. Update with new manpage. Update redirect to point to new manpage.
    - release notes

16. Comb through issues and close the ones that have been solved, referencing the version number

17. Post github release notes on patreon.

18. Update the other distributions.

# conda

Registry: https://github.com/conda-forge/visidata-feedstock/

1. Fork https://github.com/conda-forge/visidata-feedstock. Open the recipe/meta.yaml.

2. Update the VisiData version and sha256.

3. Make any necessary removals, additions or modifications to the dependencies -> note that a dependency must be part of conda.

4. Make a PR.

5. Comment `@conda-forge-admin, please rerender` in the PR.

6. Merge the PR, when everything is green.


# Homebrew

Registry: https://github.com/saulpw/homebrew-vd

1. Open the Formula/visidata.rb file. Update the link in url to the new visidata tar.gz file.
2. Update the sha256 and version in visidata.rb. Update the version in README.md.
3. For major version ships, check each dependency and see if it has been updated. If so, update the url and sha256 for the newest version.
4. On a mac, test the formula with `brew install --build-from-source visidata`. Fix as needed.
5. Audit the formula with `brew audit --new-formula visidata`
6. Add and commit the formula.

## Debian
1. Download the visidata tar.gz file from pypi
2. tar -xzmf visidata.tar.gz
3. cp visidata.ver.tar.gz visidata_ver.orig.tar.gz
4. cd visidata-ver/
5. Place there the contents of the debian directory from github.com/saulpw/visidata/dev/debian/
6. Update changelog
```
dch -v new_version
```

where new_version = "$version"-1

Edit as necessary. I usually set stability to unstable, and urgency to low, and add a small changelog.
7. Run debuild. Fix errors as they come up.
8. If a package fails to import a module, it must be added to the build dependencies as python3-modules
9. cd ..
10. If unsigned by debuild, sign the changes files
```
debsign -k keycode visidata_ver.changes
```

anjakefala has the key and password.
11. Upload to debian mentors and contact the mentor, [Martin](https://qa.debian.org/developer.php?email=debacle%40debian.org).
```
dput mentors visidata_ver.changes
```

12. Copy the fresh contents of the debian folder back into visidata/dev/debian and in debian-visidata (https://salsa.debian.org/anjakefala/visidata).

## deb-vd
Private registry: https://github.com/saulpw/deb-vd
1. Enter saulpw/deb-vd.
2. Run the command reprepro includedeb sid new-vd.deb
3. Update the README.md with the new version, commit *all* the changes and push to master.
