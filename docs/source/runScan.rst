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

   *Figure 3: configration mode choosing GUI, either to create new config file or load already existed one*

Next GUI is meant to enter new experiment configurations or see/edit a loaded one. This GUI allows you to move the energy over a range by driving the theta motor of the Double Crystal Monochromator (DCM).

.. figure:: /images/config.png
   :align: center
   :alt: proposal ID 

   *Figure 4: Main experiment configration GUI*

The user can enter many intervals, each interval has start energy(eV), end energy(eV), energy move step size, Ionization Chamber (IC) integration time, fluorescence detector integration time, external trigger and step unit. 

.. figure:: /images/interval.png
   :align: center
   :alt: proposal ID 

   *Figure 5: DCM energy equations with K step unit*

The step unit can be either in eV or K. When eV is chosen, the "step" is used as energy incerment value across the interval starting from "start" until reaching the "end" energies. By choosing K as step unit, the energy increase size (step size) increases as the scan moves further above the edge.  

.. note:: "The XAFS region is most naturally thought of as a function of k. Because E is proportional to the square of K, features will tend to broaden and reduce in amplitude as getting further above the edge. In addition, the signal falls off with increasing energy, further reducing the amplitude of features high above the edge."" reference: XAFS for every one, page 161, point# 3

The equations of calulating DCM energy with K step unit are shown below: 

.. figure:: /images/kEnergy_Eq.png
   :align: center
   :alt: proposal ID 

   *Figure 6: DCM energy equations with K step unit*

Where ΔK is energy step size in K, E\ :sub:`a` is the current DCM energy in K, E\ :sub:`c` is the calibrated energy in K and E\ :sub:`n` is the next energy value that the DCM is going to. 


You can define many samples and align them with respect to the beam (depending on the number of holders installed on the sample stage). Through this GUI you can change the sample position horizontally and vertically in order to target the right position of the sample. Also, for each sample you must assign name where it will be used as part of the experimental file name.

.. figure:: /images/sampleName.png
   :align: center
   :alt: proposal ID 

   *Figure 7: Sample position & name GUI*

.. note:: sample name is added as part of the experimental file name


Detectors GUI allows you to choose among the available transmission and florescence detectors. ICs detectors are already chosen by default, you just need to enter the gas mixture that you use in each IC. For the fluorescence detectors, either FICUS or KETEK. For more information about the detectors, please see this page: https://www.sesame.org.jo/beamlines/xafs-xrf#tabs-7

.. figure:: /images/det.png
   :align: center
   :alt: proposal ID 

   *Figure 8: Detectors choosing GUI*

Other scan parameters in the main confirmation GUI like “Experiment metadata”, “Mirror coating” and “Comments” sub-boxes are used to provide some experimental meta data. 

.. note:: Some experiment metadata fields are mandatory because they are needed to comply with xdi file format.

Fields that are highlighted in green (refer to Figure 4) are write protected when you run Users Experiment or Local Experiment (refer to Figure 1). This means that the DCM has been already calibrated and has got these values in which can't be changed for this kind of experiments. 

However, to re-calibrate the DCM with different metal foil element and crystal you can choose Energy Calibration (refer to Figure 1), then, such fields are not “write protected” and you will see them highlighted in orange: 

.. figure:: /images/engCalibConf.png
   :align: center
   :alt: proposal ID 

   *Figure 9: Main configration GUI that belongs to DCM energy calibration*

By clicking “Next”, if all is fine, the last GUI will pop up as shown below:

.. figure:: /images/finish.png
   :align: center
   :alt: proposal ID 

   *Figure 10: Last GUI before triggering the scan to start*

Once scan is started, interactive logs will be printed on the terminal showing exactly what is being processed. Also, an interactive data visualization tool will start plotting the experimental data.

.. figure:: /images/plot.png
   :align: center
   :alt: proposal ID 

   *Figure 11: Interactive data visualization GUI*

In addition, two main GUIs will be started as shown below:

   - Main plots as shown in Figure 12: 
      It contains the main analysis plots of xdi file:

      * Normalization (Linear Scalling).
      * Smoothing (Savitzky-Golay filter with default parameters(W,P):(5,3)).
      * 1st derivative of normalized data.
      * All of them including 2nd derviative.
   
   .. figure:: /images/mainPlots.png
      :align: center
      :alt: Main Plots 

      *Figure 12: Main plots of xdi file*

   - 1st derivative plot as shown in Figure 13:
      This tool allow the user to select the best peak energy value either by selecting the blue dot, or by selecting any suitable value on the curve.

   .. figure:: /images/1stDer.png
      :align: center
      :alt: 1st derivative tool.

      *Figure 13: 1st derivative tool of energy calibration*

   The main functions of this tool are:

   * 1st derivative plot: 1st derivative of normalized data (refer to Figure 13).
   * Smoothing Parameters: window length and polynomial order of Savitzky-Golay filter.
   * Confirm button: confirm the chosen value and close the plots.

   .. note:: According to smoothing parameters, please make sure that window length must be greater than ploynomial order, otherwise, an popup alert will be appear as shown in figure 14.

   .. figure:: /images/invalidAlert.png
      :align: center
      :alt: Invalid values.

      *Figure 15: Invalid smoothing parameters values*

   Once the peak value is chosen (either the blue dot, or any value on the curve), it will appear on terminal as shown in figure 15.

   .. figure:: /images/peakChosen.png
      :align: center
      :alt: Peak value chosen.

      *Figure 15: The chosen value*

   After clicking the confirm button, the results will be shown on the terminal as shown in figure 16.

   .. figure:: /images/energyCalibrationResults.png
      :align: center
      :alt: Energy calibration results.

      *Figure 16: Energy calibration results *

   .. warning:: If the *Confirm* button is clicked without choosing a value, an error messages will be shown in the terminal.
      
      .. figure:: /images/valueError.png
         :align: center

   .. note:: To ignore the smoothing filter, smoothing parameters should be zeros. 

   .. note:: To repeat the energy calibration process, type the following command in terminal:
      ::
         python main.py --engCalib (xdi path)
         e.g. python main.py --engCalib /home/XAFSScanTool/DATA/CalibTest_Foil_Scan1_20220725T111439.xdi




   


   

