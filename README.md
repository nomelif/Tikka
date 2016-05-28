# Tikka

Tikka is a small statically typed language that transpiles into C.
It is available as MIT (see at the end of this file)

For now it supports anything reasonably Unixey. This has only been tested on OS X 10.11.5 (OS X El Capitan) and Arch Linux (2016).

# Installation

## Dependencies

Tikka depends on three things: `GCC`, `Python 3` and `git`. If your Unix-like platform isn't listed above, you can try to install the packages.

### OSX

Install the Xcode Command Line tools. If they are not yet installed, you should be automatically prompted in the next step. _Uninstalling them can be difficult._

### Linux

The actual procedure depends on your distribution. If it is not listed below, don't despair. You should be able to find packages for `GCC`, `Python 3` and `git`. The main catch is that you must have `Python 3`. `Python 2` won't work.

#### Arch Linux

You can simply install the dependencies with

    $ sudo pacman -S gcc python git

#### Ubuntu / Debian / Mint / Elementary

You can simply install the dependencies with

    $ sudo apt-get install gcc python3 git

## Installing Tikka itself

Supposing `git` is installed, simply run:

    $ git clone https://github.com/nomelif/Tikka.git
    $ cd Tikka
    $ sudo ./setup

This will add a `tikka` command to `/usr/local/bin` and the bulk of the compiler to `/usr/local/share/tikka`. See uninstall for automatically removing them. If it for some reason fails, you can always remove the files by hand.

## Uninstalling

You simply have to uninstall Tikka by running `sudo ./uninstall` from the directory Tikka is in. Then uninstall the dependencies.

#### OSX

Do this at your own risk. See [this article](https://www.cocoanetics.com/2012/07/you-dont-need-the-xcode-command-line-tools/) for guidance.

### Linux

Again, the process is distribution dependent.

#### Arch Linux

Run one by one

    $ sudo pacman -R python

    $ sudo pacman -R gcc

    $ sudo pacman -R git

It is more than probable that something will depend on some of these. If `pacman` complains, just skip to the next one. I leave cleaning of the package cache to the readers' best judgement.

#### Ubuntu / Debian / Mint / Elementary

Run this command.

    $ sudo apt-get purge python gcc git

You may wish to remove the dependencies with

    $ sudo apt-get aurotemove

Again, I leave this to the readers' best judgement.

# Usage

During installation Tikka adds itself to the path. Thus, you need to simply invoke Tikka as

    $ tikka source_file.ti

This will create a binary (already marked as executable) called `a.out` in the directory it was called in.

# Syntax

[TODO]