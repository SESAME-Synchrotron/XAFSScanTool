#!../../bin/linux-x86_64/XAFS

< iocBoot/iocXAFS/envPaths

epicsEnvSet("P", "XAFS:")

dbLoadDatabase "dbd/XAFS.dbd"
XAFS_registerRecordDeviceDriver pdbbase

dbLoadTemplate("$(TOP)/iocBoot/iocXAFS/XAFS.substitutions")

iocInit

