import random
import sys
from disk_struct import Disk
from page_replacement_algorithm import  page_replacement_algorithm
from CacheLinkedList import  CacheLinkedList
import numpy as np

import PyIO
import PyPluMA

import LeCaR10_LeCaR
import LeCaR10
import LeCaR2_adaptive
import LeCaR2_cache
import LeCaR2_gviet2
import LeCaR2
import LeCaR3_adaptive
import LeCaR3_gviet
import LeCaR3
import LeCaR4_cache
import LeCaR4
import LeCaR5_gviet
import LeCaR5
import LeCaR8_adaptive
import LeCaR8_cache
import LeCaR8
import LeCaR9_adaptive
import LeCaR9_LeCaR
import LeCaR9
import LeCaR
import LeCaR_adaptive
import LeCaR_clock
import LeCaR_fixed
import LeCaR_gviet2
import LeCaR_gviet
import LeCaR_new
import LeCaR_temp_1
import LeCaR_unnorm


class LeCaRPlugin:
  def input(self, inputfile):
        self.parameters = PyIO.readParameters(inputfile)

  def run(self):
        pass

  def output(self, outputfile):
    n = int(self.parameters["n"])
    infile = open(PyPluMA.prefix()+"/"+self.parameters["infile"], 'r')
    kind = self.parameters["kind"]
    outfile = open(outputfile, 'w')
    outfile.write("cache size "+str(n))
    if (kind == "LeCaR10_LeCaR"):
       lecar = LeCaR10_LeCaR.LeCaR10(n)
    elif (kind == "LeCaR10"):
       lecar = LeCaR10.LeCaR10(n)
    elif (kind == "LeCaR2_adaptive"):
       lecar = LeCaR2_adaptive.LeCaR2(n)
    elif (kind == "LeCaR2_cache"):
       lecar = LeCaR2_cache.LeCaR2(n)
    elif (kind == "LeCaR2_gviet2"):
       lecar = LeCaR2_gviet2.LeCaR2(n)
    elif (kind == "LeCaR2"):
       lecar = LeCaR2.LeCaR2(n)
    elif (kind == "LeCaR3_adaptive"):
       lecar = LeCaR3_adaptive.LeCaR3(n)
    elif (kind == "LeCaR3_gviet"):
       lecar = LeCaR3_gviet.LeCaR3(n)
    elif (kind == "LeCaR3"):
       lecar = LeCaR3.LeCaR3(n)
    elif (kind == "LeCaR4_cache"):
       lecar = LeCaR4_cache.LeCaR4(n)
    elif (kind == "LeCaR4"):
       lecar = LeCaR4.LeCaR4(n)
    elif (kind == "LeCaR5_gviet"):
       lecar = LeCaR5_gviet.LeCaR5(n)
    elif (kind == "LeCaR5"):
       lecar = LeCaR5.LeCaR5(n)
    elif (kind == "LeCaR8_adaptive"):
       lecar = LeCaR8_adaptive.LeCaR8(n)
    elif (kind == "LeCaR8_cache"):
       lecar = LeCaR8_cache.LeCaR8(n)
    elif (kind == "LeCaR8"):
       lecar = LeCaR8.LeCaR8(n)
    elif (kind == "LeCaR9_adaptive"):
       lecar = LeCaR9_adaptive.LeCaR9(n)
    elif (kind == "LeCaR9_LeCaR"):
       lecar = LeCaR9_LeCaR.LeCaR9(n)
    elif (kind == "LeCaR9"):
       lecar = LeCaR9.LeCaR9(n)
    elif (kind == "LeCaR_adaptive"):
       lecar = LeCaR_adaptive.LeCaR(n)
    elif (kind == "LeCaR_clock"):
       lecar = LeCaR_clock.LeCaR_clock(n)
    elif (kind == "LeCaR_fixed"):
       lecar = LeCaR_fixed.LeCaR_fixed(n, float(self.parameters["fixedweight"]))
    elif (kind == "LeCaR_gviet2"):
       lecar = LeCaR_gviet2.LeCaR(n)
    elif (kind == "LeCaR_gviet"):
       lecar = LeCaR_gviet.LeCaR(n)
    elif (kind == "LeCaR_new"):
       lecar = LeCaR_new.LeCaR_new(n)
    elif (kind == "LeCaR"):
       lecar = LeCaR.LeCaR(n)
    elif (kind == "LeCaR_temp_1"):
       lecar = LeCaR_temp_1.LeCaR_temp_1(n)
    else:
       lecar = LeCaR_unnorm.LeCaR_unnorm(n)
    page_fault_count = 0
    page_count = 0
    for line in infile:
        line = int(line.strip())
        outfile.write("request: "+str(line))
        if lecar.request(line) :
            page_fault_count += 1
        page_count += 1

    
    outfile.write("page count = "+str(page_count))
    outfile.write("\n")
    outfile.write("page faults = "+str(page_fault_count))
    outfile.write("\n")
