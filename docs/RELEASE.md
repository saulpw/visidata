# Release process for the next `stable` version

1. Merge `stable` to `develop` (if necessary)

2. Ensure `develop` automated tests run correctly with ./test.sh

3. Verify that documentation/docstrings are up-to-date on features and functionality

4. Run ./mkwww.sh to build the manpage and updated website

5. Set version number to next most reasonable number (v#.#.#)

   a. add to front of CHANGELOG, along with the release date and bullet points of major changes

   b. update version number on README and front page of website

   c. bump version in `__version__` in source code (bin/vd, visidata/vdtui.py) and setup.py

6. Push `develop` to testpypi

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

7. Test install from testpypi

   a. on virgin instance

   b. on mac and linux

   c. See if windows works

   d. from git clone

   ```
   pip3 install --extra-index-url https://test.pypi.org/project visidata
   ```

10. Merge `develop` to stable

11. Merge `stable` back into other branches

    a. if the branch works with minimal conflicts, keep the branch

    b. otherwise, clean out the branch

12. Comb through issues and close the ones that have been solved, referencing the version number

13. Push stable to pypi

```
twine upload dist/*
```

14. Test install/upgrade from pypi

   a. build and check readthedocs/stable

   b. Ask someone else to test install

15. Create a tag `v#.#.#` for that commit
```
git tag v#.#.#
git push --tags
```
16. Write up the release notes and post at visidata.org/release/#.#

17. Post link to release notes on r/visidata and have some ice cream
