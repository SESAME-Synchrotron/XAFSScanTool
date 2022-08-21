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

From the GUI above you can choose the experiment type:

A. Choose **Users Experiment** if there is a scheduled beamtime for an accepted proposal. 

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

.. note:: The scanning tool is already integrated with the users database. All validation and metadata importing processes are done through such integration. metadata of a validated proposal includes but not limited to proposal title, principal investigator information, number of allocated shifts, proposal review committee.

B. Choose **Local Experiment** to run in-house experiment that is not associated with a proposal. 

This scan mode is intended to run “not proposal based” experiments, example of such experiments: 

* Director general beamtime
* In-house research experiment
* Testing / commissioning new components at the Beamline 


.. warning:: Normally, this option is restricted to beamline scientists.
.. warning:: Access to experimental data generated out of this kind of experiment is restricted to beamline scientists and authorized SESAME staff only. On the other hand, the generated data will not be **mapped/linked** with any proposal or PI work. 

C. Choose **Energy Calibration** to calibrate the beam energy in reference to the DCM crystal and metal foil you are using. 

The beam energy is linked to the monochromator via the Bragg formula, calibrating the energy means adjusting the Bragg angle (Θ theta) of the monochromator in reference to the crystal and the metal foil you are using.

Currently, the following crystals are available: 

* Si(111) 
* Si(311)

Also, the following metal foils: 
  
1. Ti (4966)
2. V (5465))
3. Cr (5989)
4. Mn (6539)
5. Fe (7112)
6. Co (7709)
7. Ni (8333)
8. Cu (8979)
9. Zn (9659)
10. Se (12658)
11. Zr (17998)
12. Nb (18986)
13. Mo (20000)
14. Pd (24350)
15. Ag (25514)
16. Sn (29200)
17. Sb (30491)
18. Ta (9881)
19. Pt (11564)
20. Au (11919)
21. Pb (13035)

The scanning tool allows you to either enter new configuration and thus generate a new configuration file or load an already existed configuration file. These two options can be chosen from this GUI:

.. figure:: /images/choseCFG.png
   :align: center
   :alt: proposal ID 
   :scale: 70%

   *Figure 3: configration mode choosing GUI, either to create new config file or load already existed one*

   Next GUI is meant to enter new experiment configurations or see/edit a loaded one. This GUI allows you to move the energy over a range by driving the theta motor of the Double Crystal Monochromator (DCM).

   