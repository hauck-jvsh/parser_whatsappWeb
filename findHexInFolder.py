import os
import fnmatch
hex=bytes.fromhex("bd3b83a8cf3f0db0ca90a44c4058c86cc75f9de5c1918ed4b5bbb31d468d5d24")
pasta="C:\\Users\\HAUCK\\AppData\\Local\\Google\\Chrome\\User Data\\Default"
for root, dir, files in os.walk(pasta):
        #print(root)
        for item in fnmatch.filter(files, "*"):
            #print(item)
            try:
                data=open(root+"/"+item,"rb").read()
            except:
                #print("falhou",root+"/"+item)
                continue
            if data.find(b"bd3b83a8cf3f0db0ca90a44c4058c86cc75f9de5c1918ed4b5bbb31d468d5d24")>0:
                  print(root+"/"+item)