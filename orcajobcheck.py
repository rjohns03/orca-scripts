#!/usr/bin/env python3
# Orcajobcheck 3.0 (Python 3 version)
# Ragnar Bjornsson (ragnar.bjornsson@gmail.com), University of Iceland.
# Script to read ORCA output conveniently
# This script was taken from the Orca Input Library by Ryan Johnson on May 8, 2017
#
#   Usage:
# 	orcajobcheck file.out       # Analyzes file.out
# 	orcajobcheck  .                 # Analyzes all files in current directory.
#   orcajobcheck  all             # Analyzes all files in current directory and its subdirectories
#   orcajobcheck  timex           # Analyzes all files in current directory and its subdirectories that have been modified/added within a given number of days x. example: orcajobcheck time4 where all output files modified within the last four days will be analyzes.
# 	orcajobcheck  . -short       # Analyzes all files in current directory in short mode
#
#   Special flags can be used to print out special information:
# 	-p         to print optimized geometry/last geometry/input geometry
# 	-t         to print thermochemical corrections from freq job
# 	-l N       to print last N lines from output files.
# 	-grad      to print the RMS gradient per step from a running optimization job.
#
###############################

debug="no"

import time
import numpy
import math
import sys
import os
import datetime
import re

start_time = time.time()

def reverse_lines(filename, BUFSIZE=20480):
    filename.seek(0, 2)
    p = filename.tell()
    remainder = ""
    while True:
        sz = min(BUFSIZE, p)
        p -= sz
        filename.seek(p)
        buf = filename.read(sz) + remainder
        if '\n' not in buf:
            remainder = buf
        else:
            i = buf.index('\n')
            for L in buf[i+1:].split("\n")[::-1]:
                yield L
            remainder = buf[:i]
        if p == 0:
            break
    yield remainder

scriptversion=3.0



class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

#Conversion factors hartree to kcal/mol
harkcal = 627.50946900

##########################################
# Read in filename or dir as argument
filelist=[]
try:
    if sys.argv[1]==".":
        dirmode="on"
        for file in sorted(os.listdir(sys.argv[1])):
            if file.endswith(".out"):
                filelist.append(file)
    #If using full or relative path for file or dir
    elif "/" in sys.argv[1]:
        #Checking if a single file with path
        if ".out" in sys.argv[1]:
            dirmode="off"
            filename=sys.argv[1]
            filelist.append(filename)
            print("filename is", filename)
        #Or a directory
        else:
            dirmode="on"
            for file in os.listdir(sys.argv[1]):
                if file.endswith(".out"):
                    filelist.append(sys.argv[1]+"/"+file)
    #If parent folder
    elif sys.argv[1]=="..":
        dirmode="on"
        for file in sorted(os.listdir(sys.argv[1])):
            if file.endswith(".out"):
                filelist.append(sys.argv[1]+"/"+file)
    ####################################################################################################################
    elif sys.argv[1]=="all":  # all output files the currenty directory and any subdirectories 
        dirmode="on"       
        path = os.getcwd()                                
        for root, dirs, files in os.walk(path):
            for file in files:                  
                if file.endswith(".out"):
                    filepath = os.path.join(root,file) 
                    filelist.append(filepath) 
                    print(filelist)
########################################################################################################################
    elif "time" in sys.argv[1]:        # like "all" but with a time restriction ( files edited within x days)
        dirmode="on"
        time_numdays = sys.argv[1]
        numdays = int(time_numdays[-1]) 
        #print(numdays) 
        today = datetime.datetime.today()
        margin = datetime.timedelta(days = numdays)
        path = os.getcwd()
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".out"):
                    filepath = os.path.join(root,file) 
                    filetime = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
                    if (today - margin) <= filetime <= today:
                        filelist.append(filepath)
########################################################################################################################
    else:
        dirmode="off"
        filename=sys.argv[1]
        if '.out' in filename == None :
            print("Not an ORCA outputfile?")
            exit()
        filelist.append(filename)
except IndexError:
    print("ORCA JobCheck Utility version", scriptversion, "(Python 3 version)")
    print("---------------------------------")
    print("Script usage:")
    print("On single file: orcajobcheck.sh orcafile.out")
    print("On directory: orcajobcheck.sh .")
    print("Short printing mode: orcajobcheck.sh . -short") 
    quit()

shortmode="unset"
try:
    if sys.argv[2]=="-short" :
        shortmode="yes"
except IndexError:
    pass    

#Here begins jobspecific section
####################################################################
if debug=="yes":
    if dirmode=="on":
        print("filelist is", filelist)
        print("Exiting dirmode")

#print('Here1. Script took %s' % (time.time() - start_time))
for filename in filelist:
    if debug=="yes":
        print("filename is", filename)
    earlycrash="unset"
    xyzfileerror="unset"
    runcomplete="unset"
    orcacrash="unset"
    conbf="unset"
    cpscferror="unset"
    scferrorgeneral="unset"
    scfstillrunning="unset"
    scfalmostconv="unset"
    parproc="unset"
    jobtype="unset"
    scfmethod="unset"
    dft="unset"
    optrunconverged="unset"
    linearcheck="unset"
    optenergy="unset"
    finaltopenergy="unset"
    opterror="unset"
    optnotconv="unset"
    optcycle="unset"
    intelectrons="unset"
    freqjob="unset"
    freqsection="unset"
    freqsearch="unset"
    optjob="unset"
    scfconv="unset"
    noiter="unset"
    moread="unset"
    autostart="unset"
    postHFmethod="unset"
    postHF="unset"
    frozel="unset"
    correl="unset"
    refenergy="unset"
    correnergy="unset"
    caseinputline="unset"
    inputline="unset"
    nofrozencore="unset"
    casscf="unset"
    lastmacroiter="unset"
    casscfconv="unset"
    nevpt2correnergy="unset"
    version="unset"
    semiempirical="unset"
    functional="unknown"
    engrad="unset"
    freqinrun="unset"
    charge="unset"
    endofinput="unset"
    numatoms="unset"
    spin="unset"
    actualelec="unset"
    temprcount="unset"
    diagerror="unset"
    brokensym="unset"
    flipspin="unset"
    scfcycleslist=[]
#spsection used to stop when SP output is done from bottom
    spsection="unset"
#optsection used to stop when output found
    optsection="unset"
    finalgeo="unset"
    coord="unset"
    geomconvtable="unset"
    geomconvgrab="unset"
    lastgeomark="unset"
    numatomcountstart="unset"
    scantest="unset"
    findenergy="unset"
    scanenergies=[]
    lastenergy="unset"
    allscanstepnums=[]
    bsenergies=[]
#
    imaginmodes=[]
    atomcoord=[]
    optgeo=[]
    lastgeo=[]
    inputgeo=[]
    geomconv=[]
    count=0
    rmsgradlist=[]

#funcional list
    funclist=["b3lyp", "bp", "pbe", "tpss", "tpssh", "pbe0", "bp86", "blyp", "LDA", "BHLYP", "B2PLYP", "cam-b3lyp", "m06-2x", "pw6b95"]

#Reading first lines of file normally until "Nuclear Repulsion      ENuc"
    with open(filename, errors='ignore') as bfile:
        for line in bfile:
            count=count+1
            if version =="unset":
                if 'Program Version' in line:
                    version=line.split()[2]
            if caseinputline=="unset" and version !="unset":
                if 'WARNING: The NDO methods cannot have' in line:
                    semiempirical="yes"
            #Grabbing simpleinputline
            if caseinputline=="unset" and version !="unset":
                if 'INPUT FILE' in line:
                        temp=next(bfile);temp=next(bfile);temp=next(bfile)
                        if '!' in temp:
                            inputline=temp
                            caseinputline=inputline.lower()
                        else:
                            temp=next(bfile);
                            inputline=temp
                            caseinputline=inputline.lower()
                        #SCF and CASSCF job
                        #CASEINPUTLINE
                        if caseinputline!="unset":
                            #Checking for functional
                            for i in funclist:
                                if i in caseinputline:
                                    functional=i
                            #Checking for noiter
                            if "noiter" in caseinputline:
                                noiter="yes"
                            #Checking for moread
                            if "moread" in caseinputline:
                                moread="yes"
                            #Checking for nofrozencore
                            if "nofrozencore" in caseinputline:
                                nofrozencore="yes"
                            #Checking for post-HF keywords
                            #print("caseinputline is", caseinputline)
                            if "ccsd" in caseinputline or "mp2" in caseinputline or "qcisd" in caseinputline:
                                postHF="yes"
                                if "ccsd" in caseinputline:
                                    postHFmethod="CC"
                                if "qcisd" in caseinputline:
                                    postHFmethod="QCI"
                                if "mp2" in caseinputline:
                                    postHFmethod="MP2"
                            # Checking for opt or freq here
                            if " optts " in caseinputline:
                                jobtype="optts"
                                if " freq " in caseinputline or " numfreq " in caseinputline or " freq" in caseinputline or " numfreq" in caseinputline:
                                    jobtype="opttsfreq"; freqsection="notyetdone"
                            elif " opt" in caseinputline or " tightopt" in caseinputline or "copt" in caseinputline:
                                jobtype="opt"
                                #print("jobtype is", jobtype)
                                if " freq" in caseinputline or " numfreq" in caseinputline:
                                    jobtype="optfreq"; freqsection="notyetdone"
                            elif " md " in caseinputline:
                                jobtype="md"
                            elif " freq " in caseinputline:
                                jobtype="freqsp"; freqsection="notyetdone"
                            elif " engrad " in caseinputline:
                                jobtype="sp"
                                engrad="yes" 
                            else:
                                jobtype="sp"
#Here checking for stuff in listed inputfile until 'END OF INPUT'
            if 'INPUT LINE' != "unset" and endofinput=="unset":
                if 'END OF INPUT' in line:
                    endofinput="yes"
                if casscf=="unset":
                    if '%casscf' in line:
                        casscf="yes"
                        #print("CASSCF is true!")
                #Checking if brokensym job
                if 'flipspin' in line.lower():
                    flipspin="yes"
                if 'finalms' in line.lower():
                    bsms=float(line.split()[-1])
                if 'brokensym' in line.lower():
                    brokensym="yes"
            if endofinput=="yes":
                if scantest=="unset":
                    temp=next(bfile);temp=next(bfile);temp=next(bfile);temp=next(bfile);
                    if "Relaxed" in temp:
                        scantest="over"
                        jobtype="scan"
                        temp=next(bfile);temp=next(bfile);temp=next(bfile)
                        scansteps=temp.split()[-1]
                        scanatomA=temp.split()[2][:-1]
                        scanatomB=temp.split()[3][:-2]
                        scanvalA=temp.split()[5]
                        scanvalB=temp.split()[7]
                        scanchange=(float(scanvalB) - float(scanvalA)) / (float(scansteps) - 1)
                    else:
                        scantest="over"
                if autostart=="unset" and conbf=="unset":
                    if 'Checking for AutoStart:' in line:
                        autostart="yes"
                if conbf=="unset" and semiempirical=="unset":
                    if '# of contracted basis functions' in line:
                        conbf=line.split()[-1]
                    if 'Number of basis functions' in line:
                        conbf=line.split()[5]
                    if casscf=="yes":
                        if 'Number of basis functions' in line:
                            conbf=line.split()[5]
                #Checking if Relaxed surface scan
                if numatomcountstart=="unset" and scantest=="over":
                    if 'CARTESIAN COORDINATES (ANGSTROEM)' in line:
                        numatomcountstart="on"
                        numatomcount=0
                if numatomcountstart=="on":
                    numatomcount += 1
                    inputgeo.append(line.strip())
                if 'CARTESIAN COORDINATES (A.U.)' in line and numatomcountstart=="on" and numatoms=="unset":
                    numatomcountstart="off"
                    inputgeo.pop(0);inputgeo.pop(0);inputgeo.pop();inputgeo.pop();inputgeo.pop()
                    numatoms=numatomcount-5
                    if numatoms > 3:
                        pausecount=int((numatoms*3)-6+10+((numatoms*3)/6)*(numatoms*3)+20+numatoms*3-20)
                        if debug=="yes":
                            print("pausecount is", pausecount)
                    else:
                        pausecount=33
            #Finding parallel and SCF output after basis output
            if conbf !="unset" or semiempirical=="yes":
                if parproc =="unset":
                    if 'parallel MPI-processes' in line:
                        parproc=line.split()[4]
            # SCF method #NOTE. MULTIPLE OCCURENCE
                if 'SCF SETTINGS' in line:
                        temp=next(bfile);temp=next(bfile);temp=next(bfile)
                        scftemp=temp.split()
                        if scftemp[0]=="ZDO-Hamiltonian":
                            semiempirical="yes"
                            scfmethod=scftemp[3]
                        else:
                            scfmethod=scftemp[4]
                        if 'DFT' in scfmethod:
                            dft="yes"
                 #Charge and spin
                if scfmethod!="unset":
                    if ' Total Charge           Charge' in line:
                        charge=line.split()[4]
                    if charge !="unset":
                        if ' Multiplicity           Mult            ....' in line:
                            mult=int(line.split()[3])
                            spin=(mult-1)/2.0
                        if 'Number of Electrons    NEL             ....' in line:
                            actualelec=line.split()[5]
                        if 'Nuclear Repulsion      ENuc' in line:
                            nucrepuls=line.split()[5]
                            break


#Now we have read through the first few hundred lines (until nuc repulsion) of file that determines the jobtype and basic molecule info.
#If the ORCA job died prematurely (before nuc repulsion was printed) then that is fine (reversed read below will find the error)
    if debug=="yes":
        print('First read complete. Read', count, 'lines. Script took %s' % (time.time() - start_time))
        print("Last line was", line)
#Now Reading lines of file backwards. This should detect errors immediately etc. or find where job died.
    rcount=0
    with open(filename, errors='ignore') as file:
        for line in reverse_lines(file):
            rcount=rcount+1
            #Error messages. Only last 50 lines checked
            if rcount < 50:
                if 'Zero distance between atoms' in line:
                    orcacrash="yes";earlycrash="yes"
                if 'Cannot open input file:' in line:
                    orcacrash="yes";earlycrash="yes"
                if 'You must have a' in line:
                    orcacrash="yes";earlycrash="yes"
                if 'INPUT ERROR' in line:
                    inputerror="yes";orcacrash="yes";earlycrash="yes"
                if 'ERROR CODE RETURNED FROM CP-SCF PROGRAM' in line:
                    cpscferror="yes";orcacrash="yes"
                if 'ABORTING THE RUN' in line:
                    abortcode="yes";orcacrash="yes";earlycrash="yes"
                if 'Invalid assignment in' in line:
                    abortcode="yes";orcacrash="yes";earlycrash="yes"
                if 'Aborting the run' in line:
                    abortcode2="yes";orcacrash="yes";earlycrash="yes"
                if 'Skipping actual calculation' in line:
                    abortcode3="yes";orcacrash="yes";earlycrash="yes"
                if 'Error : multiplicity' in line:
                    errormult="yes";orcacrash="yes";earlycrash="yes"
                if 'Element name/number, dummy atom or point charge expected in COORDS' in line:
                    coorderror="yes";orcacrash="yes";earlycrash="yes"
                if 'FATAL ERROR ENCOUNTERED' in line:
                    fatalerrorcode="yes";orcacrash="yes";earlycrash="yes"
                if 'There is no basis function on atom' in line:
                    basiserror="yes";orcacrash="yes";earlycrash="yes"
                if 'ORCA finished by error termination' in line:
                    errortermin="yes";orcacrash="yes"
                if 'An error has occured in the SCF module' in line:
                    scferrorgeneral="yes";orcacrash="yes"
                if 'An error has occured in the CASSCF module' in line:
                    casscferrorgeneral="yes";orcacrash="yes"
                if 'mpirun has exited due to process' in line:
                    mpiruncode="yes";orcacrash="yes"
                if 'mpirun noticed that process rank 0' in line:
                    mpiruncode2="yes";orcacrash="yes"
                if 'Job terminated from outer' in line:
                    jobtermin="yes";orcacrash="yes"
                if 'CANNOT OPEN FILE' in line:
                    cannotopenfile="yes";orcacrash="yes";earlycrash="yes"
                if '!!!               Filename:' in line:
                    xyzfileerror="yes";orcacrash="yes";earlycrash="yes"
                if 'Unknown identifier in' in line:
                    unknownidentifier="yes";orcacrash="yes";earlycrash="yes"
                if 'ERROR: expect a' in line:
                    commanderror="yes";orcacrash="yes";earlycrash="yes"
                if 'ERROR: found a coordinate defintion' in line:
                    coordinateerror="yes";orcacrash="yes";earlycrash="yes"
                if 'Diagonalization failure because of NANs in input matrix' in line:
                    diagerror="yes"; orcacrash="yes"
                if 'ERROR       : GSTEP Program returns an error' in line:
                    gsteperror="yes";orcacrash="yes"
                if 'ORCA TERMINATED NORMALLY' in line:
                    runcomplete="yes"
                if 'TOTAL RUN TIME:' in line:
                    runtime=line.split()[3:]
# Here need to add some kind of break so that we stop if errors above are encountered
            #if orcacrash="yes":
            #    break
            if rcount==50:
                if debug=="yes":
                    print('Here,rcount50. Script took %s' % (time.time() - start_time))
#Relaxed surface scan section
            if jobtype=="scan":
                if 'RELAXED SURFACE SCAN STEP' in line:
                    scanstep=line.split()[5]
                    allscanstepnums.append(scanstep)
                if lastgeomark=="unset":
                    if 'CARTESIAN COORDINATES (A.U.)' in line and lastgeomark=="unset" :
                        coord="active"
                        if debug=="yes":
                            print('Here. Starting coord grab  Read', rcount, 'lines. %s' % (time.time() - start_time))
                    if coord=="active":
                        lastgeo.append(line.strip())
                        if 'CARTESIAN COORDINATES (ANGSTROEM)' in line:
                            coord="inactive"
                            lastgeomark="done"
                            lastgeo.pop(0);lastgeo.pop(0);lastgeo.pop(0);lastgeo.pop();lastgeo.pop()
                if lastenergy =="unset":
                    if 'FINAL SINGLE POINT ENERGY' in line:
                        lastenergy=line.split()[4]
                if 'OPTIMIZATION RUN DONE' in line:
                    findenergy="yes"
                if findenergy=="yes":
                    if 'FINAL SINGLE POINT ENERGY' in line:
                        scanenergies.append(line.split()[4])
                        findenergy="no"
#Single-point section
            if jobtype == "sp" or jobtype == "freqsp":
                #If brokensymm job
                if brokensym=="yes" or flipspin=="yes":
                    sdfds="sdf"
                    if 'E(BrokenSym)' in line:
                        bsenergy=line.split()[2]
                    if 'E(High-Spin)      =' in line:
                        hsenergy=line.split()[2]
                    if 'DFT' in scfmethod and intelectrons=="unset":
                        if 'N(Total)' in line:
                            intelectrons=line.split()[2]
                if runcomplete=="yes":
                    sdf="ds"
                    if postHF=="yes":
                        if postHFmethod=="CC":
                            if 'Number of correlated electrons' in line:
                                correl=line.split()[5]
                                frozel=int(actualelec)-int(correl)
                                if noiter=="yes":
                                    break
                            if 'Reference energy' in line:
                                refenergy=line.split()[3]
                            if 'Final correlation energy' in line:
                                correnergy=line.split()[4]
                            if 'E(CORR)(total)' in line:
                                correnergy=line.split()[2]
                            if 'E(CORR)(corrected)' in line:
                                correnergy=line.split()[2]
                            if 'E(CORR)' in line:
                                correnergy=line.split()[2]
                        if postHFmethod=="QCI":
                            if 'Number of correlated electrons' in line:
                                correl=line.split()[5]
                                frozel=int(actualelec)-int(correl)
                                if noiter=="yes":
                                    break
                            if 'Reference energy' in line:
                                refenergy=line.split()[3]
                            if 'E(CORR)(corrected)' in line:
                                correnergy=line.split()[2]
                            if 'E(CORR)' in line:
                                correnergy=line.split()[2]
                        if postHFmethod=="MP2":
                            if 'CORRELATION ENERGY' in line:
                                correnergy=line.split()[3]
                            if 'chemical core electrons' in line:
                                frozel=line.split()[1].lstrip('NCore=')
                            if nofrozencore=="yes":
                                frozel="0"
                    if 'FINAL SINGLE POINT ENERGY' in line:
                        scfenergy=line.split()[4]
                        if postHF=="unset" and noiter=="yes":
                            break
                    if 'SCF CONVERGED AFTER' in line:
                        scfconv="yes"
                        scfcycles=line.split()[4]
                        spsection="done"
                    if 'The wavefunction IS NOT YET CONVERGED! It shows however signs of' in line:
                        scfalmostconv="yes"
                    if 'SCF NOT CONVERGED AFTER' in line:
                        scfconv="no"
                        unfinscfcycles=line.split()[5]
                        spsection="done"
                #If runcomplete not true. Like if SCF is still running or if FREQ-sp job and something happened during freq run.
                else:
                    if 'FINAL SINGLE POINT ENERGY' in line:
                        scfenergy=line.split()[4]
                        if postHF=="unset" and noiter=="yes":
                            break
                    if 'SCF CONVERGED AFTER' in line:
                        scfconv="yes"
                        scfcycles=line.split()[4]
                        spsection="done"
                    if 'The wavefunction IS NOT YET CONVERGED! It shows however signs of' in line:
                        scfalmostconv="yes"
                    if 'SCF NOT CONVERGED AFTER' in line:
                        scfconv="no"
                        unfinscfcycles=line.split()[5]
                        spsection="done"
                    if 'SCF ITERATIONS' in line:
                        if scfconv=="unset":
                            scfstillrunning="yes"
                        spsection="done"
                ########
                if casscf=="yes":
                    if 'Total Energy Correction :' in line:
                        nevpt2correnergy=line.split()[6]
                    if lastmacroiter=="unset" and 'MACRO-ITERATION' in line:
                        lastmacroiter=line.split()[1].rstrip(':')
                    if 'THE CAS-SCF GRADIENT HAS CONVERGED' in line:
                        casscfconv="yes"
                    if 'THE CAS-SCF ENERGY   HAS CONVERGED' in line:
                        casscfconv="yes"
                    if 'CAS-SCF ITERATIONS' in line:
                        break
                #if 'SCF ITERATIONS' in line:
                #    scfstillrunning="yes"
                #    spsection="done"
                if spsection == "done":
                    break
#FREQSECTION
            #print("freqsection is", freqsection)
        #Will analyze the last freq output encountered in outputfile. But will only print it if optjob converged
            if freqsection=="notyetdone":
                if runcomplete=="yes":
                    freqjob="yes"
                    #print("freqjob is", freqjob)
                    #Once Temperature has been found, try to skip all Normal mode output without re.search lines.
                    #Until NORMAL MODES
                    if freqsearch!="on":
                        if 'Temperature         ...' in line:
                            temperature=line.split()[2]
                            temprcount=rcount
                            freqsearch="on"
                            if debug=="yes":
                                print('Here. Temperature line. rcount is:', rcount, 'Script took %s' % (time.time() - start_time))
                    if temprcount!="unset" and rcount-temprcount > pausecount :
                        #print("rcount is", rcount); print("line is", line)
                        if 'imaginary' in line:
                            freqimagtest="yes"
                            imaginmodes.append(line.split()[1])
                        if linearcheck=="yes":
                            if '5:' in line:
                                lowestvib=line.split()[1]
                        else:
                            if '6:' in line:
                                lowestvib=line.split()[1]
                            #Here we have reached the beginning of FREQ section, from bottom, hence freqsection is done
                        if 'VIBRATIONAL FREQUENCIES' in line:
                            freqsearch="off"
                            if debug=="yes":
                                print('Here. FREQdone. rcount is:', rcount, 'Script took %s' % (time.time() - start_time))
                            freqsection="done"
            #Therm stuff
                    if freqsearch!="on":
                        #print('bla Script took %s' % (time.time() - start_time))
                        if 'The molecule is recognized as being linear' in line:
                            linearcheck="yes"
                        if 'G-E(el)' in line:
                            gthermcorr=float(line.split()[2])
                        if 'Zero point' in line:
                            zeropointcorr=float(line.split()[4])
                            enthalpycorr=totthermcorr+zeropointcorr+enthalpyterm
                        if 'Final entropy term' in line:
                            entropycorr=float(line.split()[4])
                        if 'Total thermal correction' in line:
                            totthermcorr=float(line.split()[3])
                        if 'Thermal Enthalpy correction' in line:
                            enthalpyterm=float(line.split()[4])
                #If freqjob but runcomplete is unset.
                elif rcount > 50 and runcomplete=="unset":
                    #print("Here. freqsection is:", freqsection)
                    freqsection="notpresent"
                    #print("fresection not present")
        #OPT job settings
            if freqsection=="done" or freqsection=="unset" or freqsection=="notpresent":
                if jobtype == "opt" or jobtype == "optts" or jobtype == "optfreq" or jobtype == "opttsfreq":
                    optjob="yes"
                    #print("opt, line is", line)
                    #if 'Analytical frequency calculation' in line:
                    #freqinrun="yes"
                    #numatoms
                    #print("optrunconverged is", optrunconverged)
                    if optrunconverged=="unset":
                        if 'OPTIMIZATION RUN DONE' in line:
                            optrunconverged="yes"
                    if runcomplete=="yes":
                        if optrunconverged=="unset":
                            if 'OPTIMIZATION RUN DONE' in line:
                                if debug=="yes":
                                    print("XXXXXXwe are here Script took %s" % (time.time() - start_time))
                                optrunconverged="yes"
                    if optenergy=="unset":
                        if 'FINAL SINGLE POINT ENERGY' in line:
                            #print("line is", line)
                            optenergy=float(line.split()[4])
                            if optrunconverged=="yes":
                                finaloptenergy=optenergy
                            #print("this optenergy is", optenergy)
                            if debug=="yes":
                                print('In optsection. FINAL S P E line. Read', rcount, 'lines. Script took %s' % (time.time() - start_time))
                    if lastgeomark=="done":
                            #print('lastgeomark is done. Script took %s' % (time.time() - start_time))
                            if optrunconverged=="unset":
                                if 'FINAL ENERGY EVALUATION AT THE STATIONARY POINT' in line:
                                    optrunconverged="yes"
                                    if debug=="yes":
                                        print('Here. OPT HAS CONVERGED. ', rcount, 'lines. Script took %s' % (time.time() - start_time))

                    if 'CARTESIAN COORDINATES (A.U.)' in line and lastgeomark=="unset" :
                        coord="active"
                        if debug=="yes":
                            print('Here. Starting coord grab  Read', rcount, 'lines. %s' % (time.time() - start_time))
                    if coord=="active":
                        lastgeo.append(line.strip())
                        if 'CARTESIAN COORDINATES (ANGSTROEM)' in line:
                            coord="inactive"
                            lastgeomark="done"
                            lastgeo.pop(0);lastgeo.pop(0);lastgeo.pop(0);lastgeo.pop();lastgeo.pop()

            #Finds optcycle number if optimization converged
                    #if re.search('***               (AFTER', line):
                    if runcomplete=="yes" and optrunconverged=="yes" and lastgeomark=="done":
                        if '***               (AFTER' in line:
                            optcycle=int(line.split()[2])
            # Signals that optsection is over for a converged done. Breaks later if optsection is set
                    if optcycle!="unset":
                        if 'FINAL ENERGY EVALUATION AT THE STATIONARY POINT' in line:
                            #print("Optsection is now done")
                            optsection="done"
                    #ONly search for opt not conv in last 100 lines
                    if rcount < 100:
                        if 'The optimization did not converge but reached the maximum number of' in line:
                            optnotconv="yes"
            #This finds optcycle number if optimization did not converge. Should break at some point though
                    if lastgeomark=="done":
                        if 'GEOMETRY OPTIMIZATION CYCLE' in line and optcycle=="unset":
                            optcycle=int(line.split()[4])
                            prevoptcycle=optcycle-1
                            #3jan. Disabling optsection here and putting in geomconvtable section instead
                            #optsection="done"
                            #print("runcomplete is", runcomplete)
                            #print("optnotconv is", optnotconv)
                    if optnotconv=="yes" or runcomplete=="unset":
                        if optcycle!="unset":
                            if 'The optimization has not yet converged - more geometry cycles are needed' in line:
                                geomconvtable="active"
                                #print("geomconvtable ACTIVE")
                    if geomconvtable=="active":
                        #if 'RMS gradient' in line:
                        #    print("RMS line is", line)
                        #    rmsgradlist.append(line.strip()[2])
                        geomconv.append(line.strip())
                        if '|Geometry convergence|' in line:
                        #print("line is", line)
                            geomconv.pop(0);geomconv.pop(0)
                            geomconvtable="inactive"
                            geomconvgrab="done"
                            #optsection="done"
                    if geomconvgrab=="done":
                        if 'FINAL SINGLE POINT ENERGY' in line:
                            optenergy=float(line.split()[4])
                            optsection="done"

                if 'DFT' in scfmethod and optrunconverged=="yes" and intelectrons=="unset":
                    if 'N(Total)' in line:
                        intelectrons=line.split()[2]

                if optsection=="done":
                    if debug=="yes":    
                        print('Optsection done, breaking. Script took %s' % (time.time() - start_time))
                    break
        #Integration of electrons. Only necessary for DFT.
    if debug=="yes":
        print('Here. End of reverse loop. Script took %s' % (time.time() - start_time))

########################
# Now all read through file done. Printing below.
########################

#################
#SHORT PRINTING MODE
    if shortmode=="yes":
        #print("--------------")
        #print("filename is", filename)
        if runcomplete=="yes":
            if jobtype=="sp" or jobtype=="freqsp" and postHF=="unset":
                if jobtype=="freqsp":
                    if len(imaginmodes)==0:
                        print('{0:40}   {1:40}'.format(bcolors.HEADER + filename+":", bcolors.OKGREEN + scfenergy), bcolors.ENDC)
                    else:
                        print('{0:40}   {1:10}   {2:40}'.format(bcolors.HEADER + filename+":", bcolors.OKGREEN + scfenergy, bcolors.FAIL + "Imaginary modes"), bcolors.ENDC)
                if jobtype=="sp":
                    if scfconv=="yes" or casscfconv=="yes":
                        print('{0:40}   {1:40}'.format(bcolors.HEADER + filename+":", bcolors.OKGREEN + scfenergy), bcolors.ENDC)
                    else:
                        print('{0:40}   {1:40}'.format(bcolors.HEADER + filename+":", bcolors.FAIL + "Not converged!"), bcolors.ENDC)
            elif jobtype=="sp" and postHF!="unset":
                print('{0:40}   {1:40}'.format(bcolors.HEADER + filename+":", bcolors.OKGREEN + scfenergy), bcolors.ENDC)
            elif optjob=="yes" or jobtype=="optfreq" or jobtype=="opttsfreq":
                if optrunconverged=="yes":
                    #print("optenergy is", optenergy)
                    print('{0:40}   {1:40}'.format(bcolors.HEADER + filename+":", bcolors.OKGREEN + str(optenergy)), bcolors.ENDC)
                else:
                    print('{0:40}   {1:40}'.format(bcolors.HEADER + filename+":", bcolors.FAIL + "Optimization failed!"), bcolors.ENDC)
        elif orcacrash=="yes":
            print('{0:40}   {1:40}'.format(bcolors.HEADER + filename+":", bcolors.FAIL + "ORCA Crash!"), bcolors.ENDC)
        else:
            print('{0:40}   {1:40}'.format(bcolors.HEADER + filename+":", bcolors.WARNING + "Running?"), bcolors.ENDC)
# LONG PRINTING MODE
    else:
        print("")
        print("ORCA JobCheck Utility version", scriptversion, "(Python 3 version)")
        print("-----------------------------------------------------------------------")
        print(bcolors.HEADER +"File:", filename, bcolors.ENDC)
        if parproc!="unset":
            print("ORCA version", version, "ran", parproc,"MPI-process job.")
        else:
            print("ORCA version", version, "ran serial job")
        if runcomplete=="yes":
            print(bcolors.OKGREEN +"ORCA terminated normally (",' '.join(runtime),")", bcolors.ENDC)
        elif orcacrash=="yes":
            print(bcolors.FAIL +"ORCA JOB Crashed!", bcolors.ENDC)
            print("Error message:")
            #print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            with open(filename, errors='ignore') as cfile:
                scount=0
                bla=[]
                nlines=5
                for dline in reverse_lines(cfile):
                    scount += 1
                    bla.append(dline.strip('\n'))
                    if scount==nlines:
                        break
                    for bline in reversed(bla):
                        print(bcolors.FAIL +bline, bcolors.ENDC),
                        break
            #Will now allow last geometry printout as well
            try:
                if optjob=="yes":
                    if optrunconverged=="unset" and sys.argv[2]=="-p":
                        print("Cycle", optcycle, "Cartesian coordinates (", numatoms, "atoms) in Angstrom:")
                        for atom in reversed(lastgeo):
                            print(*atom, sep='')
            except IndexError:
                print("Do orcajobcheck output -p  to print last geometry (Cycle", optcycle, ")")

            #print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            if xyzfileerror=="yes":
                print(bcolors.FAIL +"Fatal error: Job could not open xyz file", bcolors.ENDC)
            if cpscferror=="yes":
                print(bcolors.FAIL +"CPSCF error", bcolors.ENDC)
        else:
            print(bcolors.WARNING +"ORCA has not terminated with message and may still still be running this job", bcolors.ENDC)

    # If earlycrash do not show more output. Else continue
        if earlycrash=="yes":
            pass
        else:
            print("")
            if semiempirical=="yes":
                print(numatoms, "atoms.", "Charge:", charge, " Spin:", spin)
            else:
                print(numatoms, "atoms.", "Charge:", charge, " Spin:", spin, " Contracted basis functions:", conbf)
            if moread=="yes":
                print("Initial orbitals via MOREAD")
            elif autostart=="yes":
                print("Initial orbitals via Autostart")
            else:
                print("Initial orbitals via Guess")
            #print("This is an", jobtype.upper(), "job.")
            if jobtype=="scan":
                scanenergies.reverse()
                refenergy=scanenergies[0]
                scanatomelA=inputgeo[int(scanatomA)].split()[0]
                scanatomelB=inputgeo[int(scanatomB)].split()[0]
                print("This is a Relaxed Surface Scan. Scanning Bond between atoms", scanatomA+scanatomelA, "and", scanatomB+scanatomelB, ". There will be", scansteps, "steps")
                print("Scanning from", scanvalA, "to ", scanvalB, "(change is", round(scanchange,6), " )")
                print("         Scan step       Scan parameter      Energy (hartree)        Rel. energy (kcal/mol)")
                print("====================================================================================================")
                count=0
                scanpar=float(scanvalA)
                for energy in scanenergies:
                    count += 1
                    energy=float(energy)
                    delta=(float(energy)-float(refenergy))*harkcal
                    #print(count, scanpar, energy, delta)
                    print('{0:10} {1:25f} {2:25f} {3:25f}'.format(count, scanpar, energy, delta))
                    scanpar=float(scanpar)+float(scanchange)
                
                print("")
                if runcomplete!="yes":
                    allscanstepnums.reverse()
                    print("Currently running: Scan step", allscanstepnums[-1], ", Optcycle XX. Energy is", lastenergy, "and Rel. Energy is", round((float(lastenergy)-float(refenergy))*harkcal, 6), "kcal/mol")
                    try:
                        if sys.argv[2]=="-p":
                            print("Last geometry (", numatoms, "atoms) in Angstrom:")
                            for atom in reversed(lastgeo):
                                print(*atom, sep='')
                    except IndexError:
                            print("Do orcajobcheck output -p to print current/last geometry.")
                else:
                    print("Scan completed!")
#........................................................................
            if jobtype=="sp" or jobtype=="freqsp" and postHF=="unset":
                if dft=="yes":
                    if engrad=="yes":
                        print("This is a single-point (Engrad) DFT calculation. Functional:", functional)
                    else:
                        if brokensym=="yes" or flipspin=="yes":
                            print("This is a single-point Broken-symmetry DFT calculation. Functional:", functional)
                            print("First doing single-point High-spin S=", (mult-1)/2, "calculation, then converging to BS MS=", bsms)
                            print("HIGH-SPIN ENERGY:", hsenergy)
                            print("BROKEN-SYMMETRY ENERGY:", bsenergy)
                        else:
                            print("This is a single-point DFT calculation. Functional:", functional)
                elif casscf=="yes":
                    print("This is a single-point CASSCF calculation.")
                elif jobtype=="freqsp":
                    print("This is a single-point HF Freq calculation.")
                else:
                    if engrad=="yes":
                        print("This is a single-point (Engrad) HF calculation.")
                    else:
                        print("This is a single-point HF calculation.")
                if runcomplete=="yes" and scfconv=="yes":
                    print(bcolors.OKGREEN +"SCF CONVERGED AFTER", scfcycles, "CYCLES", bcolors.ENDC)
                    print(bcolors.OKBLUE +"FINAL SINGLE POINT ENERGY IS", scfenergy, bcolors.ENDC) 
                    if dft=="yes":
                        print("Integrated no. electrons:", intelectrons, "(should be", actualelec, ")")
                elif runcomplete=="yes" and scfconv=="no":
                    print(bcolors.FAIL +"SCF DID NOT CONVERGE in", unfinscfcycles, "cycles. Check your SCF settings.", bcolors.ENDC)
                    if scfalmostconv=="yes":
                        print(bcolors.WARNING +"SCF was close to convergence though (\"signs of convergence\").", bcolors.ENDC)
                        print(bcolors.WARNING +"Energy is", scfenergy, bcolors.ENDC)
                elif runcomplete=="yes" and noiter=="yes":
                    print(bcolors.OKGREEN +"SCF mode: No iterations", bcolors.ENDC)
                    print(bcolors.OKBLUE +"FINAL SINGLE POINT ENERGY IS", scfenergy, bcolors.ENDC)
                    if dft=="yes":
                        print("Integrated no. electrons:", intelectrons, "(should be", actualelec, ")")
                #Runcomplete not true but SCFconv is yet. Probably freqsp job that failed in freq step
                elif runcomplete=="unset" and scfconv=="yes":
                    print(bcolors.OKGREEN +"SCF CONVERGED AFTER", scfcycles, "CYCLES", bcolors.ENDC)
                    print(bcolors.OKBLUE +"FINAL SINGLE POINT ENERGY IS", scfenergy, bcolors.ENDC)
                    if orcacrash=="yes":
                        print(bcolors.FAIL +"Freqjob failed", bcolors.ENDC)
                elif scferrorgeneral=="yes":
                    print(bcolors.FAIL +"SCF has crashed. Sad...", bcolors.ENDC)
                elif scfstillrunning=="yes":
                    print(bcolors.WARNING +"SCF is probably still be running", bcolors.ENDC)
                elif casscf=="yes" and casscfconv=="yes":
                    print(bcolors.OKGREEN +"CASSCF CONVERGED AFTER", lastmacroiter, "CYCLES", bcolors.ENDC)
                    if nevpt2correnergy!="unset":
                        print("NEVPT2 calculation performed")
                        print("NEVPT2 correlation energy is", nevpt2correnergy)
                    print(bcolors.OKBLUE +"FINAL SINGLE POINT ENERGY IS", scfenergy, bcolors.ENDC)
                else:
                    if casscf=="yes":
                        print(bcolors.WARNING +"CASSCF still running?", bcolors.ENDC)
                    else:
                        print(bcolors.WARNING +"SCF still running?", bcolors.ENDC)
            if jobtype=="sp" and postHF=="yes":
                print("This is a single-point", postHFmethod, "calculation")
                if runcomplete=="yes" and scfconv=="yes":
                    print(bcolors.OKGREEN +"SCF CONVERGED AFTER", scfcycles, "CYCLES", bcolors.ENDC)
                    print("Frozen core is", frozel, "electrons")
                    if postHFmethod=="CC" or postHFmethod=="QCI":
                        print("Reference energy is:", refenergy)
                    print("Correlation energy is:", correnergy)
                    print(bcolors.OKBLUE +"FINAL SINGLE POINT ENERGY IS", scfenergy, bcolors.ENDC)
                elif runcomplete=="yes" and scfconv=="no":
                    print(bcolors.FAIL +"SCF DID NOT CONVERGE in", unfinscfcycles, "cycles. Check your SCF settings.", bcolors.ENDC)
                    if scfalmostconv=="yes":
                        print(bcolors.WARNING +"SCF was close to convergence though (\"signs of convergence\").", bcolors.ENDC)
                        print(bcolors.WARNING +"Energy is", scfenergy, bcolors.ENDC)
                elif runcomplete=="yes" and noiter=="yes":
                    print(bcolors.OKGREEN +"SCF mode: No iterations", bcolors.ENDC)
                    print("Frozen core is", frozel, "electrons")
                    if postHFmethod=="CC" or postHFmethod=="QCI":
                        print("Reference energy is:", refenergy)
                    print("Correlation energy is:", correnergy)
                    print(bcolors.OKBLUE +"FINAL SINGLE POINT ENERGY IS", scfenergy, bcolors.ENDC)
                elif scferrorgeneral=="yes":
                    print(bcolors.FAIL +"SCF has crashed. Sad...", bcolors.ENDC)
                elif scfstillrunning=="yes":
                    print(bcolors.WARNING +"SCF is probably still be running", bcolors.ENDC)
                else:
                    print(bcolors.WARNING +"SCF still running?", bcolors.ENDC)
            if jobtype=="optfreq":
                print("This is an OPT+FREQ job")
            if optjob=="yes":
                if optrunconverged=="yes":
                    print(bcolors.OKGREEN +"Optimization converged! in (", optcycle, "iterations). YAY!", bcolors.ENDC) 
                    print(bcolors.OKBLUE + "FINAL OPTIMIZED ENERGY:", finaloptenergy, bcolors.ENDC)
                    if jobtype=="optfreq":
                        if freqsection!="done":
                            print(bcolors.WARNING +"Frequency job did not finish", bcolors.ENDC)
                    if dft=="yes":
                        print("Integrated no. electrons:", intelectrons, "(should be", actualelec, ")")
                elif optnotconv=="yes":
                    print(bcolors.FAIL +"Optimization did not converge in", optcycle, "optimization steps", bcolors.ENDC)
                    for gline in reversed(geomconv):
                        print("        ",gline, sep='')
                elif optnotconv=="unset" :
                    print(bcolors.WARNING +"Optimization may still be running", bcolors.ENDC)
                    if optcycle==1:
                        print("Optimization Cycle", optcycle, "running.")
                    else:
                        print("Optimization Cycle", prevoptcycle, "energy:", optenergy)
            #print(geomconv)
                    for gline in reversed(geomconv):
                        print("        ",gline, sep='')
                    print("")
                    print("Do orcajobcheck output -grad to print RMS gradient for all cycles")
                    print("Optimization Cycle", optcycle, "in progress")
            if freqjob=="yes":
                if jobtype=="opttsfreq":
                    if optrunconverged!="yes":
                        ssdfs="sdfs"
                    else:
                        if freqsection=="done":
                            if len(imaginmodes)==1:
                                print(bcolors.OKGREEN +"We have 1 imaginary mode (",imaginmodes[0], "cm^-1) for saddlepoint. Good!", bcolors.ENDC)
                            if len(imaginmodes)==0:
                                print(bcolors.FAIL +"We have no imaginary modes for saddlepoint. Bad...", bcolors.ENDC)
                            if len(imaginmodes)>1:
                                print(bcolors.FAIL +"We have many imaginary modes for saddlepoint. Bad...", bcolors.ENDC)
                        else:
                            print(bcolors.WARNING +"Frequency job did not finish", bcolors.ENDC)
                if jobtype=="optfreq" or jobtype=="freqsp":
                    if optrunconverged!="yes":
                        if jobtype=="freqsp":
                            print("Frequencies were calculated")
                            if freqsection=="done":
                                if len(imaginmodes)==1:
                                    print(bcolors.FAIL +"We have 1 imaginary mode for minimum. Bad...:", imaginmodes[0], bcolors.ENDC)
                                if len(imaginmodes)==0:
                                    print(bcolors.OKGREEN + "We have no imaginary modes for minimum. Good. Lowest mode is", lowestvib, bcolors.ENDC)
                                    if float(lowestvib) < 0:
                                        print(bcolors.WARNING + "Probably some numerical noise present, however.", bcolors.ENDC)
                                if len(imaginmodes)>0:
                                    print(bcolors.FAIL +"We have several imaginary modes for minimum. Bad...", bcolors.ENDC)
                        else:
                            print(bcolors.WARNING +"Frequency job did not finish", bcolors.ENDC)
                    else:
                        if freqsection=="done":
                            if len(imaginmodes)==1:
                                print(bcolors.FAIL +"We have 1 imaginary mode for minimum. Bad...:", bcolors.ENDC)
                            if len(imaginmodes)==0:
                                print(bcolors.OKGREEN + "We have no imaginary modes for minimum. Good. Lowest mode is", lowestvib, bcolors.ENDC)
                                if float(lowestvib) < 0:
                                    print(bcolors.WARNING +"Probably some numerical noise present, however.", bcolors.ENDC )
                            if len(imaginmodes)>0:
                                print(bcolors.FAIL +"We have several imaginary modes for minimum. Bad...", bcolors.ENDC)
                        else:
                            print(bcolors.WARNING +"Frequency job did not finish", bcolors.ENDC)
                try:
                    if sys.argv[2]=="-t" and freqsection=="done":
                        print("")
                        print("Thermochemistry corrections:")
                        print("Zero-point energy correction, ZPE:", zeropointcorr, "Eh")
                        print("Total Enthalpy correction, Hcorr:", enthalpycorr, "Eh")
                        print("Total Entropy correction, TS:", entropycorr,"Eh")
                        print("Total Free energy correction (Hcorr - TS), Gcorr:", gthermcorr, "Eh")
                #else:
                #    if optrunconverged=="yes":

                #        print("Do orcajobcheck output -t  to print thermochemical corrections")
                except IndexError:
                        if optrunconverged=="yes" and freqsection=="done":
                            print("Do orcajobcheck output -t  to print thermochemical corrections")
            
            try:
                if jobtype=="sp":
                    if sys.argv[2]=="-l":
                        nlines=int(sys.argv[3])
                        with open(filename, errors='ignore') as cfile:
                            scount=0
                            bla=[]
                            for dline in reverse_lines(cfile):
                                scount += 1
                                bla.append(dline.strip('\n'))
                                if scount==nlines:
                                    print(bcolors.UNDERLINE +"Last", nlines, "lines of output:",bcolors.ENDC)
                                    for bline in reversed(bla):
                                        print(bline),
                                    break
            except IndexError:
                print("Do orcajobcheck output -l N  to print last N lines.")
            try:
                if optjob=="yes":
                    if optrunconverged=="yes" and sys.argv[2]=="-p":
                        print("Optimized Cartesian coordinates (", numatoms, "atoms) in Angstrom:")
                        for atom in reversed(lastgeo):
                            print(*atom, sep='')
                    if optrunconverged=="unset" and sys.argv[2]=="-p":
                        print("Cycle", optcycle, "Cartesian coordinates (", numatoms, "atoms) in Angstrom:")
                        for atom in reversed(lastgeo):
                            print(*atom, sep='')
                    if optrunconverged=="unset" and sys.argv[2]=="-grad":
                        print("RMS gradient per Cycle (using grep)")
                        import subprocess
                        subprocess.call(['grep', ' RMS gradient', filename])
 
                elif jobtype=="sp":
                    if sys.argv[2]=="-p":
                        print("Cartesian coordinates of input geometry (", numatoms, "atoms) in Angstrom:")
                        for atom in inputgeo:
                            print(*atom, sep='')
            except IndexError:
                if optrunconverged=="yes":
                    print("Do orcajobcheck output -p  to print optimized geometry")
                elif jobtype=="sp":
                    print("Do orcajobcheck output -p  to print input geometry")
                else:
                    print("Do orcajobcheck output -p  to print last geometry (Cycle", optcycle, ")")
            print("")

if debug=="yes":
    print('Script took %s' % (time.time() - start_time))
    print("Last line read in file is:", line)
