# OnionPerf

OnionPerf is a utility to track Tor and onion service performance.

OnionPerf uses multiple processes and threads to download random data
through Tor while tracking the performance of those downloads. The data is
served and fetched on localhost using two TGen (traffic generator)
processes, and is transferred through Tor using Tor client processes and
an ephemeral Tor Onion Service. Tor control information and TGen
performance statistics are logged to disk, analyzed once per day to
produce a json stats database and files that can feed into Torperf, and
can later be used to visualize changes in Tor client performance over time.

For more information, see https://github.com/robgjansen/onionperf.

### Get OnionPerf

```
git clone https://github.com/robgjansen/onionperf.git
cd onionperf
```

### Install System Dependencies

  + **Tor** (>= v0.2.7.3-rc): libevent, openssl
  + **TGen** (Shadow >= v1.11.1): cmake, glib2, igraph
  + **OnionPerf**: python

The easiest way to satisfy all system dependencies is to use a package manager.

```
#Fedora/RedHat:
sudo yum install gcc cmake make glib2 glib2-devel igraph igraph-devel libevent libevent-devel openssl openssl-devel python
# Ubuntu/Debian:
sudo apt-get install gcc cmake make libglib2.0 libglib2.0-dev libigraph0 libigraph0-dev libevent libevent-dev openssl openssl-dev python
```

**Note**: in newer distributions, `libevent` may be called `libevent-2.0` and `openssl-dev` may be called `libssl-dev`.

### Install Python modules

  + **OnionPerf** python modules: stem (>= v1.4.0), twisted, lxml, networkx, numpy, matplotlib.

#### Option 1: Package Manager

The easiest way to satisfy all system dependencies is to use a package manager.

```
# Fedora/RedHat:
sudo yum install python-stem python-twisted python-lxml python-networkx python-matplotlib numpy scipy
# Ubuntu/Debian:
sudo apt-get install python-stem python-twisted python-lxml python-networkx python-matplotlib python-numpy python-scipy
```

#### Option 2: pip

Python modules can also be installed using `pip`. The python modules that are required for each
OnionPerf subcommand are as follows:

  + `onionperf monitor`: stem
  + `onionperf measure`: stem, lxml, twisted, networkx
  + `onionperf analyze`: stem
  + `onionperf visualize`: scipy, numpy, pylab, matplotlib

You must first satisfy the system/library requirements of each of the python modules.

**Note**: the following commands may not contain all requirements; please update if you find more!

```
# Fedora/RedHat:
sudo yum install python-devel libxml2 libxml2-devel libxslt libxslt-devel libpng libpng-devel freetype freetype-devel
# Ubuntu/Debian:
sudo apt-get install python-devel libxml2 libxml2-dev libxslt1 libxslt1-dev libpng libpng-devel freetype freetype-devel 
```

It is recommended to use virtual environments to keep all of the dependencies self-contained and
to avoid conflicts with your other python projects.

```
pip install virtualenv
virtualenv --no-site-packages venv
source venv/bin/activate
pip install -r requirements.txt # installs all required python modules for all OnionPerf subcommands
deactivate
```

If you don't want to use virtualenv, you can install with:

```
pip install stem lxml twisted networkx scipy numpy matplotlib
```

**Note**: You may want to skip installing numpy and matplotlib if you don't
plan to use the `visualize` subcommand, since those tend to require several
large dependencies.

### Build Tor

**Note**: You can install Tor via the package manager as well, though the
preferred method is to build from source.

We need at least version 0.2.7.3-rc

```
git clone https://git.torproject.org/tor.git -b release-0.2.7
cd tor
./autogen.sh
./configure --disable-asciidoc
make
```

### Build TGen Traffic Generator

The traffic generator currently exists in the Shadow simulator repository,
but we will build TGen as an external tool and skip building both the full
simulator and the TGen simulator plugin.

```
git clone https://github.com/shadow/shadow.git
cd shadow/src/plugin/shadow-plugin-tgen
mkdir build
cd build
cmake .. -DSKIP_SHADOW=ON -DCMAKE_MODULE_PATH=`pwd`/../../../../cmake/
make
```

### Build and Run OnionPerf

If using pip and virtualenv (run from onionperf base directory):

```
source venv/bin/activate
pip install -I .
deactivate
```

If using just pip:

```
pip install -I .
```

Otherwise:

```
python setup.py build
python setup.py install
```

OnionPerf has several modes of operation and a help menu for each. For a
description of each mode, use:

```
onionperf -h
```

  + monitor: Connect to Tor and log controller events to file
  + measure: Measure Tor and Onion Service Performance using TGen
  + analyze: Analyze Tor and TGen output
  + visualize: Visualize OnionPerf analysis results

### Measure Tor

To run in measure mode, you will need to give OnionPerf the path to your custom
'tor', 'tgen', and 'twistd' binary files if they do not exist in your PATH
environment variable.

```
./onionperf measure --tor=/home/rob/tor/src/or/tor \
--tgen=/home/rob/shadow/src/plugin/shadow-plugin-tgen/build/tgen --twistd=/usr/bin/twistd
```

This will run OnionPerf in measure mode with default ports; a TGen server runs on
port 8080 and a Twisted web server runs on port 8081. Port 8080 **must** be open on
your firewall if you want to do performance measurements with downloads that exit
the Tor network. You should also open port 8081 if you want the data that OnionPerf
gathers to be publicly accessible.

By default, OnionPerf will will run a TGen client/server pair that transfer traffic
through Tor and through an ephemeral onion service started by OnionPerf. TGen and Tor
log data is collected and stored beneath the `onionperf-data` directory, and other
information about Tor's state during the measurement process is collected from Tor's
control port and logged to disk. Every night at 11:59 UTC, OnionPerf will rotate all
log files, and analyze the latest results to produce a `type torperf 1.0` stats file,
as well as an `onionperf.analysis.json` stats file. These are placed in the twistd docroot
and are available through the web interface or at `onionperf-data/twistd/docroot`.

### Analyze/Visualize Results

OnionPerf runs the data it collects through `analyze` mode every night at midnight to
produce the `onionperf.analysis.json` stats file. This file can be reproduced by using
`onionperf analyze` mode and feeding in a TGen log file from the
`onionperf-data/tgen-client/log_archive` directory and the matching Torctl log file from
the `onionperf-data/tor-client/log_archive` directory.

For example:

```
onionperf analyze --tgen onionperf-data/tgen-client/log_archive/onionperf_2015-11-15_15\:59\:59.tgen.log \
--torctl onionperf-data/tor-client/log_archive/onionperf_2015-11-15_15\:59\:59.torctl.log
```

This produces the `onionperf.analysis.json` file, which can then be plotted like so:

```
onionperf visualize --data onionperf.analysis.json "onionperf-test"
```

This will save new PDFs containing several graphs in the current directory.

### Contribute

GitHub pull requests are welcome and encouraged!
