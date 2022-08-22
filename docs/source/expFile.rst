Experimental data file layout and format
========================================

The scanning tool of XAFS-XRF beamline generates experimental data in compliance with “SESAME Experimental Data Management Policy (SEDMP)” from the data acquisition point of view. The policy can be found here: https://www.sesame.org.jo/for-users/user-guide/sesame-experimental-data-management-policy.

One of the pillars of the SEDMP is to generate expiremntal data in stander and well defined data formats, thus at SESAME the stander experimental data files for XAS beamlines is XAS Data Interchange Format (XDI) version 1.0. XDI format is an open-source data format aims to standardize the XAS data format. All information about this format can be found on this page: https://github.com/XraySpectroscopy/XAS-Data-Interchange/blob/master/specification/spec.md

XDI is an ASCII file that can be opened using any text editor, also the file itself is self-descriptive. The figure below shows an example of XDI file layout: 

.. figure:: /images/xdiFile2.png
   :align: center
   :alt: proposal ID

   *Figure 1: example of xdi file*