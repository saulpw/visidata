
# Release process for the next `stable` version

1. Merge `stable` to `develop` (if necessary)
2. Ensure `develop` automated tests run correctly
3. Set version number to next most reasonable number
   a. add to front of CHANGELOG
4. Push `develop` to testpypi
5. Test install from testpypi
   a. on virgin instance
   b. on mac and linux
   c. See if windows works
   d. from git clone
6. Build/check develop docs on readthedocs
7. Merge develop to stable
8. Push stable to pypi
9. Test install/upgrade from pypi
   a. check readthedocs/stable
   b. Ask someone else to test install and docs
