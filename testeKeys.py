import fnmatch
import ccl_chromium_indexeddb
from Crypto.Cipher import AES
import hashlib
import hmac
import base64
import sys
import os
from datetime import datetime


def AESUnpad(s):
    return s[:-ord(s[len(s)-1:])]


def AESDecrypt(key, ciphertext, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = cipher.decrypt(ciphertext)
    return AESUnpad(plaintext)


encData="66595a7c5cb8327488c26fa4fb2f662da539ca59aa99fb0b9559a8f431a4da92773a9f652c67ef7d297e8e257d003338c523728a92d44f56a09e8e2488e0fc9e"
encData=bytes.fromhex(encData)
iv=bytes.fromhex("d5384920df9701ea94d2cbdc03dbcb47")
f=open("keys.txt","r")
count=0
for key in f:
    key=key.split(" ")[0]
    #if count%10000==0:
    #    print(count,key)
    key=bytes.fromhex(key)
    decData=AESDecrypt(key,encData,iv)
    hexData=decData.hex()
    if len(decData)>2 and hexData.startswith("0a") and hexData.endswith("1200"):
        print("Possivel chave encontrada",key.hex())
        print(decData)
        #break
    count+=1