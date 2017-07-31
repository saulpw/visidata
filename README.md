# Installation instructions

As per http://www.pygit2.org/install.html:

        wget https://github.com/libgit2/libgit2/archive/v0.26.0.tar.gz
        tar xzf v0.26.0.tar.gz
        cd libgit2-0.26.0/
        cmake .
        make
        sudo make install

        sudo pip3 install pygit2

        python -c 'import pygit2'  # to test
