# -*- coding: utf-8 -*-
import os
import signal
import sys
from subprocess import Popen, PIPE, STDOUT

def php(code):        # open process
    p = Popen(['php'], stdout=PIPE, stdin=PIPE, stderr=STDOUT, close_fds=False)
    # read output
    o = p.communicate(code)[0]
    # kill process
    try:
        os.kill(p.pid, signal.SIGTERM)
    except:
        pass
    # return
    return o

msg = "\"تم فتح المعاملة رقم سوف يتم التواصل معك قريبا\""
code = """<?php

  include("D:/mobilyws.php");
  echo Convert2UTF16(""" + msg + """);

?>
"""
print code
res = php(code)
print res
