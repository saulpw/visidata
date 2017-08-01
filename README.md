# Installation instructions

As per http://www.pygit2.org/install.html:

        wget https://github.com/libgit2/libgit2/archive/v0.26.0.tar.gz
        tar xzf v0.26.0.tar.gz
        cd libgit2-0.26.0/
        cmake .
        make
        sudo make install

        sudo apt install libffi-dev

        sudo pip3 install pygit2

        export LD_LIBRARY_PATH=/usr/local/lib
        python3 -c 'import pygit2'  # to test
