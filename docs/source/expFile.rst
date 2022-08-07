Experimental data file layout and format
========================================
The scanning tool of HESEB beamline generates experimental data in compliance with “SESAME Experimental Data Management Policy (SEDMP)” from data acquisition point of view. The policy can be found here: 
https://www.sesame.org.jo/for-users/user-guide/sesame-experimental-data-management-policy. 

One of the pillars of the SEDMP is to generate expiremntal data in stander and well defined data formats, thus at SESAME the stander experimental data files for XAS beamlines is  XAS Data Interchange Format (XDI) version 1.0. XDI format is an open-source data format aims to standardize the XAS data format. All information about this format can be found on this page: https://github.com/XraySpectroscopy/XAS-Data-Interchange/blob/master/specification/spec.md


.. figure:: /images/xdi.png
   :align: center
   :alt: XDI file format example

   *Figure 1: XDI file format data example*

.. note:: The file contains mainly two parts, metadata and experimental data. The metadata comes first at the top of the file. The default stander at SESAME to produce one xdi file for each scan, i.e. if the number of scans in the scan tool is 3 then three xdi files will be created. 