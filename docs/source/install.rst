Installing XAFS/XRF scanning tool
=================================

This page includes information about the needed packages to run the scan tool. 

Prerequisites
--------------

The following should be installed on the computer before running the scanning tool: 

* Linux redhat based OS (This work has been done under CentOS 7.4, however, there should be no reason to not work on other distributions)
* EPICS XAFS/XRF IOCs (motion and scan IOCs)
* Python 3.9 
* QT 4.1.0 based on 5.9.7.


Python virtual environment
---------------------------
venv module of Python is being used as a virtual environment for this setup. 

The venv module of python provides support for creating **virtual environments** that is isolated from system site directories. Normally, each virtual environment has its own Python binary (which matches the version of the binary that was used to create this environment) and can have its own independent set of installed Python packages in its site directories. 

to install and create venv: 
::

	$ pip3.9 install virtualenv
	$ python3.9 -m venv /opt/DAQ/venv

to create alias of you environment: 
::

	$ vi ~/.bashrc

add the following line to the file:
:: 

	alias p3='source /opt/DAQ/venv/bin/activate'

resource your bashrc: 
::

	source ~/.bashrc

Packages and libraries
-----------------------

The tool needs set of python packages and Qt libraries installed and configured.

Pyhon packages: 
...............

The list below contains the list of python packages needed for the scanning tool to run. After activating the python virtual environment (by typing **p3** in the terminal), you can use **pip** to install them in the virtual environment or you can copy this list in a text file (requirements.txt) and install them at once using this command (pip install -r requirements.txt)  

::
	
	backports.entry-points-selectable==1.1.0
	bcrypt==3.2.0
	cffi==1.15.0
	colorama==0.4.4
	cryptography==35.0.0
	cycler==0.10.0
	distlib==0.3.2
	filelock==3.0.12
	h5py==2.10.0
	importlib-metadata==4.8.1
	importlib-resources==5.2.2
	kiwisolver==1.2.0
	matplotlib==3.2.1
	numpy==1.18.5
	pandas==1.0.4
	paramiko==2.8.0
	Pillow==7.1.2
	platformdirs==2.3.0
	progressbar==2.5
	pycparser==2.20
	pyepics==3.4.1
	PyNaCl==1.4.0
	pyparsing==2.4.7
	PyQt5==5.12
	PyQt5_sip==4.19.19
	pyqtgraph==0.10.0
	python-dateutil==2.8.1
	pytz==2020.1
	scipy==1.4.1
	six==1.15.0
	typing-extensions==3.10.0.2
	virtualenv==20.7.2
	zipp==3.5.0



Qt and its libraries: 
.....................

	
	1. Install epics from SESAME's local repo.
	2. Download Qt creator: https://drive.sesame.org.jo/owncloud/index.php/s/LO3GLyDkPMWZKU9.
	3. Install qt-creator-opensource-linux-x86_64-4.13.3.run. 
	4. Install epics-qt, qt5, qwt, or anything related to *qt* packages by ``yum`` command.
	5. Go to ``.bashrc`` and copy the following:

	::

		export EPICS_BASE='/opt/epics/base'
		export EPICS_HOST_ARCH=linux-x86_64
		export PATH=${PATH}:/opt/qtcreator-4.13.3/bin/
		export QWT_ROOT=/usr/local/qwt-6.1.3
		export QWT_INCLUDE_PATH=${QWT_ROOT}/include
		export QE_TARGET_DIR=/usr/local/epics-qt
		export PATH=${EPICS_BASE}/bin/$EPICS_HOST_ARCH:${QE_TARGET_DIR}/bin/${EPICS_HOST_ARCH}:/usr/lib64/qt5/bin:${PATH}
		export LD_LIBRARY_PATH=${EPICS_BASE}/lib/${EPICS_HOST_ARCH}:/usr/local/qwt-6.1.3/lib:${QE_TARGET_DIR}/lib/${EPICS_HOST_ARCH}:${QE_TARGET_DIR}/lib/${EPICS_HOST_ARCH}/designer
		export QT_PLUGIN_PATH=${QT_PLUGIN_PATH}:${QWT_ROOT}/plugins:$QE_TARGET_DIR/lib/$EPICS_HOST_ARCH

	6. ``source .bashrc`` 
	7. To validate your setup, create a new project and open the designer, you should get qwt and epics qt widgets shown.


Clone and run the scanning tool
--------------------------------

.. note:: Make sure that the python environment is activated before proceeding with this section 

The scanning tool (XAFSXRFScanTool) is available on github. The most recent version can be found on this link: https://github.com/SESAME-Synchrotron/XAFSScanTool.git. To clone and run, launch your terminal then do the follwoing: 

::

	$ cd ~ 
	$ git git@github.com:SESAME-Synchrotron/XAFSScanTool.git
	$ cd XAFSScanTool
	$ python main.py --testingMode yes

.. warning:: If all is fine, you should see the GUI pops up, otherwise, error messages and alerts should be shown in the terminal.
	