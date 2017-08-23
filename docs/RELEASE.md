# Release process for the next `stable` version

1. Merge `stable` to `develop` (if necessary)

2. Ensure `develop` automated tests run correctly

3. Verify that documentation/docstrings are up-to-date on features and functionality

4. Set version number to next most reasonable number (v#.#.#)

   a. add to front of CHANGELOG, along with the release date and bullet points of major changes
   
   b. update version number on README and docs
   
   c. bump version in `__version__` in source code and setup.py
   
5. Push `develop` to testpypi

    a. set up a ~/.pypirc
    
    ```
    [distutils]
    index-servers=
        pypi
        testpypi
    [pypi]
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

6. Test install from testpypi

   a. on virgin instance
   
   b. on mac and linux
   
   c. See if windows works
   
   d. from git clone
   
   ```
   pip3 install --extra-index-url https://test.pypi.org/project visidata
   ```
   
7. Build/check `develop` docs on readthedocs

8. Merge `develop` to stable

9. Merge `stable` back into other branches

    a. if the branch works with minimal conflicts, keep the branch

    b. otherwise, clean out the branch

10. Comb through issues and close the ones that have been solved, referencing the version number

11. Push stable to pypi

```
twine upload dist/*
```

12. Test install/upgrade from pypi

   a. build and check readthedocs/stable
   
   b. Ask someone else to test install

13. Create a tag `v#.#.#` for that commit
```
git tag v#.#.#
git push --tags
```
14. Announce the release and have some ice cream
