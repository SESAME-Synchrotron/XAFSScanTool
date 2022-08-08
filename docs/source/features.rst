Current features and future plans
=================================

Current featues
---------------
At the moment, the scanning tool has the follwoing features: 

* User friendly GUI 
* Collect data from detectors simultaneously (currently from three detectors ICs, KETEK and FICUS)
* Runs as “unattended scanning mode”
* Moves the DCM energy in eV or K units. 
* The tool is smart enough to **pause** in case of problems (e.g. current goes below certain limits, shutter is closed, problem in the vacuum, ...etc )
* Enable data writing in xdi files
* Online data visualization
* Online / offline logging
* Automatic data transfer to data center (after each scan)
* Input data validation
* Public documentation targeting end-users (how-to)

Scanning tool | future plan
----------------------------

* Adapt Bruker XFlash detector.
* Finalize automatic proposal and user metadata extraction from users DB.
* Store the data in HDF5 dxFile format
* Develop a tool to convert HDF5 dxFile to xdi files