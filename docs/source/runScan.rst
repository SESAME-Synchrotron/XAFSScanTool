Run experiment and collect data 
===============================
.. note:: All beamline EPICS IOCs should be up and running before using the scanning tool.

.. note:: In order to run the scanning tool, you need to activate python environment that you have already setup. 

The scanning tool home directory is located in the home directory of the control user. To access it: 
::

	$ cd ~ 
	$ cd XAFSScanTool
	

to run the scanning tool: 
::

	$ python main.py 

the main function will validate and execute some procedures and functions, if all is fine GUI will appear: 

.. figure:: /images/start.png
   :align: center
   :alt: first popup GUI

   *Figure 1: First popup GUI that allows you to choose experiment type*

.. warning:: if a PV is disconnected, the scanning tool will show such PV in "red" color (instead of green as shown ubove), this will cause the tool to not run!!.

From the GUI above you can choose the experiment type. Choose **Users Experiment** if there is a schedule beamtime for an accepted proposal. 

Upon choosing Users Experiment, you will be asked to provide scheduled proposal ID as shown in Figure 2 below: 

.. figure:: /images/propID.png
   :align: center
   :alt: proposal ID 
   :scale: 70%

   *Figure 2: proposal ID*

By choosing "Users Experiment", the scan tool will: 

* Ask you to provide the proposal number. 
* Validate whether the provided proposal number is correct and valid for this beam time. 
* If the validation result is okay, the tool will import the proposal metadata and include them in the experimental file. If not, user will be alerted and the tool will not be able to continue!!

.. note:: metadata of validated proposal number includes but not limited to proposal title, principal investigator name, number of allocated shifts,  

