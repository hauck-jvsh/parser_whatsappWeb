import os
import sys
import fnmatch
import re
import base64
import numpy as np

def entropy(labels):
    ps = np.bincount(labels) / len(labels)
    return -np.sum([p * np.log2(p) for p in ps if p > 0])

def entropy2(labels, base=None):
  """ Computes entropy of label distribution. """

  n_labels = len(labels)

  if n_labels <= 1:
    return 0

  value,counts = np.unique(labels, return_counts=True)
  probs = counts / n_labels
  n_classes = np.count_nonzero(probs)

  if n_classes <= 1:
    return 0

  ent = 0.

  # Compute entropy
  base = 2 if base is None else base
  for i in probs:
    ent -= i * np.log(i, base)

  return ent

#file=open("D:\\mem_whatsapp\\mem1.img","rb")
file=open("C:\\Users\\HAUCK\\memoria.001","rb")
data = file.read()
file.close()
step=8
keys={}
npassos=int(len(data)/step)
progress=int(npassos/1000)
for i in range(npassos):
    start=i*step
    key=data[start:start+0x10]
   
    unique=set(key)
    if i%progress ==0:
       print(npassos,i,len(keys),100*(i/npassos))
    if len(unique)>12:
        if key.hex() in keys:
           keys[key.hex()]+=1
        else:
           keys[key.hex()]=1
saida=open("keys.txt","w")
for key,value in keys.items():
   saida.write(key+" "+str(value)+"\n")
saida.close()
