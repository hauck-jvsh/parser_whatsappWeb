#!/usr/bin/python3

from Crypto.Cipher import AES
import hashlib
import hmac
import base64
import sys
import sys
import ccl_chromium_indexeddb
from Crypto.Cipher import AES
import hashlib
import hmac
import base64
import sys
import re
import mozidbedit.mozidbedit.mozidb as mozidb

def strings(content,min=4):
    return re.findall(b"[^\x00-\x1F\x7F-\xFF]{"+str(min).encode("utf-8")+b",}", content)
def HKDF(key, length,appInfo=b"", salt=b"\0"*32):
    key = hmac.new(salt, key, hashlib.sha256).digest()
    keyStream = b""
    keyBlock = b""
    blockIndex = 1
    while len(keyStream) < length:
        keyBlock = hmac.new(
            key,
            msg=keyBlock+appInfo + (chr(blockIndex).encode("utf-8")),
            digestmod=hashlib.sha256).digest()
        blockIndex += 1
        keyStream += keyBlock
    return keyStream[:length]

def AESUnpad(s):
    return s[:-ord(s[len(s)-1:])]


def AESDecrypt(key, ciphertext, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = cipher.decrypt(ciphertext)
    return AESUnpad(plaintext)



def loadDbFirefox():
    conn=mozidb.IndexedDB("G:\\of2203526-2024\\user7753_firefox\\s4l1w1pt.default-esr\\storage\\default\https+++web.whatsapp.com^firstPartyDomain=whatsapp.com\\idb\\2181795718meogdaerlo-ts.sqlite")
    return mozidb.IDBObjectWrapper(conn)


def loadDb():

    # assuming command line arguments are paths to the .leveldb and .blob folders
    #leveldb_folder_path = "C:\\Users\\HAUCK\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\IndexedDB\\https_web.whatsapp.com_0.indexeddb.leveldb"
    #blob_folder_path = "C:\\Users\\HAUCK\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\IndexedDB\\https_web.whatsapp.com_0.indexeddb.blob"
    #leveldb_folder_path = "IndexedDB\\file__0.indexeddb.leveldb"
    #blob_folder_path = "IndexedDB\\file__0.indexeddb.blob"
    blob_folder_path = None
    leveldb_folder_path = "G:\\of2203526-2024\\user7708_chrome\\Default\\IndexedDB\\https_web.whatsapp.com_0.indexeddb.leveldb"
    
    #leveldb_folder_path="F:\\Downloads\\volatility3-2.5.2\\caso_dip\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 4\\IndexedDB\\https_web.whatsapp.com_0.indexeddb.leveldb"
    #blob_folder_path="F:\\Downloads\\volatility3-2.5.2\\caso_dip\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 4\\IndexedDB\\https_web.whatsapp.com_0.indexeddb.blob"
    print("ola1",leveldb_folder_path)
    # open the indexedDB:
    indexedDB = ccl_chromium_indexeddb.WrappedIndexDB(leveldb_folder_path, blob_folder_path)
    return indexedDB
    
def printTables(db):
    for table in db.object_store_names:
        print(table)

def decriptyFiles(indexedDB,hashes):
    
    db_model=indexedDB
    
    
    print(len(hashes))
    values=[]
    #aeskey=b"\x01\x0B\x10\x06\x10\x11\xA0\x74\x73\x48\xEA\x17\x52\xD7\x84\x28\xD0\xBF\xD3\xC4\xAF\x0D\x27\xC0\x42\x20\x91\xEE\x64\xDE\xA8\xE4\x52\xCA\xB4\xCA\x5B\x2C\xB4\x22\x2E\x5D\xAF\x01\x3D\x1B\xDF\x71\xBD\xAB\xCE\x7B\xB8\x75\x29\x27\x4F\x34\x7B\x02\x7B\x02\xA0\x00\x00\x00"
    print("Total",len(hashes.keys()))
    for record in db_model["message"].iterate_records():
        #print(record)
        if record.value is None:
            continue
                 

        values.append(record.value)
        if "quotedMsg" in record.value and isinstance(record.value["quotedMsg"], dict):
            values.append(record.value["quotedMsg"])
       
        if "thumbnailEncSha256" in record.value and isinstance(record.value["thumbnailEncSha256"], str):

            if "thumbnail" in record.value and isinstance(record.value["thumbnail"],str):
                thumb=base64.b64decode(record.value["thumbnail"])
                encFilehash=base64.b64decode(record.value["thumbnailEncSha256"])
                if len(thumb)>0:
                    open(pasta2+"/thumb_"+encFilehash.hex()+".jpg","wb").write(thumb)
                    continue
            
            values.append({"mediaKey":record.value["mediaKey"],
                           "type":record.value["type"]+" Thumb",
                           "encFilehash":record.value["thumbnailEncSha256"],
                           "filehash":record.value["thumbnailSha256"],
                           "org":record.value})
            
    
    for record in db_model["profile-pic-thumb"].iterate_records():
        if record.value is None:
            continue
        if "filehash" in record.value and isinstance(record.value["filehash"],str):
            values.append({"filehash":record.value["filehash"]})
            


    for record in db_model["recent-stickers"].iterate_records():
        if record.value is None or "sticker" not in record.value:
            continue
        data= record.value["sticker"]
        if "filehash" in data and isinstance(data["filehash"],str):
            values.append(data)
            #print("aee",data)
    
    nerros=0
    search=set()
    found=set()
   
    for data in values:
        
        filehash=None
        if("filehash" in data and  isinstance(data["filehash"], str)):
            
            filehash=base64.b64decode(data["filehash"])
            search.add(filehash.hex())
            if(filehash.hex() in hashes):
                found.add(filehash.hex())
                #print("achou",hashes[filehash.hex()],data)
                ext=".jpg"
                if "mimetype" in data and isinstance(data["mimetype"],str):
                    ext="."+data["mimetype"].split("/")[1]
                if "filename" in data and isinstance(data["filename"],str):
                    ext="."+data["filename"].split(".")[-1]
                f_org=open(hashes[filehash.hex()],"rb")
                f_dest=open(pasta2+"/copy_"+filehash.hex()+ext,"wb")
                f_dest.write(f_org.read())
                f_dest.close()
                f_org.close()
                del hashes[filehash.hex()]
            
        if  "encFilehash" in data and isinstance(data["encFilehash"], str) and "mediaKey" in data and isinstance(data["mediaKey"], str):
            
            encFilehash=base64.b64decode(data["encFilehash"])           
            
            mediaKey=base64.b64decode(data["mediaKey"])
            
        

            if(encFilehash.hex() in hashes):
                print(data["type"])
                tipo=data["type"]
                if tipo=="ptt":
                    tipo="audio"
                if tipo=="sticker" or tipo=="chat":
                    tipo="image"
                
                ext=None
                if "filename" in data and isinstance(data["filename"],str):
                    ext=data["filename"].split(".")[-1]
                #print("Tipo",tipo)
                print(hashes[encFilehash.hex()])
                if filehash is not None:
                    for info in  infos.keys():
                        if ext is None:
                            temp_ext=infos[info]
                        else:
                            temp_ext=ext
                        print("Tipo",info,temp_ext)                         
                        if decrypt(hashes[encFilehash.hex()],mediaKey,info, pasta2+"/"+encFilehash.hex()+"."+ temp_ext,filehash.hex()):
                            found.add(filehash.hex())
                            del hashes[encFilehash.hex()]
                            break
                                                        
                else:
                    print("Chegou aqui")
                    if ext is None:
                            ext=infos[tipo]
                    if decrypt(hashes[encFilehash.hex()],mediaKey,appInfo[tipo], pasta2+"/"+encFilehash.hex()+"."+ ext):
                        del hashes[encFilehash.hex()]
                

                if(encFilehash.hex() in hashes):
                    nerros+=1
                    print("Erro",nerros,data)
            else:
                search.add(encFilehash.hex())
        
    print("Erros",nerros)
                        
    print("sem refencia",len(hashes.keys()))

    

    open("hashes.txt","w").write(str(search.difference(found)))
            
           

    


appInfo = {
    "image": b"WhatsApp Image Keys",
    "video": b"WhatsApp Video Keys",
    "audio": b"WhatsApp Audio Keys",
    "document": b"WhatsApp Document Keys",
    "image/webp": b"WhatsApp Image Keys",
    "image/jpeg": b"WhatsApp Image Keys",
    "image/png": b"WhatsApp Image Keys",
    "video/mp4": b"WhatsApp Video Keys",
    "audio/aac": b"WhatsApp Audio Keys",
    "audio/ogg": b"WhatsApp Audio Keys",
    "audio/wav": b"WhatsApp Audio Keys",
}
infos={b"WhatsApp Image Keys":"jpg",
        b"WhatsApp Video Keys":"mp4",
        b"WhatsApp Audio Keys":"ogg",
        b"WhatsApp Document Keys":"bin",
       b"WhatsApp Document Thumbnail Keys":"jpg",
       b"WhatsApp Image Thumbnail Keys":"jpg",
       b"WhatsApp Video Thumbnail Keys":"jpg",
       b"WhatsApp Link Thumbnail Keys":"jpg",
       b"WhatsApp History Keys":"his",
       b"WhatsApp App State Keys":"app",
       b"WhatsApp Payment Background Keys":"pay"}


extension = {
    "ptt": "ogg",
    "image": "jpg",
    "video": "mp4",
    "audio": "ogg",
    "document": "bin",
}

def decryptInt(data, mediaKey, iv, decHash=None):
    try:
        data = AESDecrypt(mediaKey, data, iv)
        if decHash is not None:
            sha256Hash = hashlib.sha256(data)
            sha256Hashed = sha256Hash.hexdigest()
        
            if sha256Hashed!=decHash:
                #print("Erro",decHash,sha256Hashed)
                return None
        return data
    except:
        return None

def decrypt(fileName, mediaKey, mediaType, output,decHash=None):
    mediaKeyExpanded = HKDF(mediaKey, 112, mediaType)
    macKey = mediaKeyExpanded[48:80]
    mediaData = open(fileName, "rb").read()
   
    data=decryptInt(mediaData[:-10], mediaKeyExpanded[16:48], mediaKeyExpanded[:16], decHash)
    if data==None:
        data=decryptInt(mediaData, mediaKeyExpanded[16:48], mediaKeyExpanded[:16], decHash)
    if data==None:
         print("Erro",decHash)
         return False
    
    with open(output, 'wb') as f:
        f.write(data)
    
    if decHash is not None:
        print("Decrypted")
    else:
        print("Decrypted (hopefully)")

    return True


pasta="G:\\of2203526-2024\\files"
pasta2="G:\\of2203526-2024\\files_dec"
#pasta="../whatsapp_files"
#pasta2="../dec_files"
import os
import fnmatch
enc_files={}
print("teste")
for root, dir, files in os.walk(pasta):
        print(root)
        for item in fnmatch.filter(files, "*"):
            sha256Hash = hashlib.sha256(open(pasta+"/"+item,"rb").read())
            sha256Hashed = sha256Hash.hexdigest()
            #print(sha256Hashed)
            enc_files[sha256Hashed]=pasta+"/"+item

indexedDB=loadDbFirefox()
decriptyFiles(indexedDB,enc_files)


# database="/mnt/c/Users/HAUCK/AppData/Local/Google/Chrome/User Data/Default/IndexedDB/https_web.whatsapp.com_0.indexeddb.leveldb"
# #print(enc_files)
# for root, dir, files in os.walk(database):
#         for item in fnmatch.filter(fil es, "*"):
#                 file=open(database+"/"+item,"rb")
#                 try:
#                     data=file.read()
#                 except:
#                      continue
#                 #print("ola",file.name)     
               
#                 if data.find(b'\xed\x53\x5a\xe5\x98\xe7\x68\x39\x9d\x0f\xc8\x3d\xc0\x13\x9d\xf4\x2d\x7b\x6c\x88\xc6\xb8\xbe\xb8\xca\xe4\x14\xef\x1d\xd7\x51\x99')>0:
#                      print(file.name)
                
#                 for enc_file in enc_files.keys():
#                     pos=0
#                     while pos>=0:
#                         pos=data.find(enc_file.encode('utf-8'),pos+1)
#                         posKey=data.find(b"Key\"",pos)
#                         fimKey=posKey+5+0x2c
#                         if data.find(b"audio",pos,posKey)>0:
#                             mtype="audio"
#                         elif data.find(b"image",pos,posKey)>0 or data.find(b"jpeg",pos,posKey)>0:
#                             mtype="image"
#                         elif data.find(b"video",pos,posKey)>0:
#                             mtype="video"
#                         else:
#                             mtype="document"
#                         outfile=pasta2+"/"+enc_file+"."+ extension[mtype]
#                         if pos>0 and  posKey>0 and posKey-pos<500 and not os.path.isfile(outfile):
#                             mediaKey=base64.b64decode(data[posKey+5:fimKey])
                            
#                             print(file.name,enc_file,data[posKey+5:fimKey], mediaKey.hex(),mtype,)
#                             try:
#                                 if decrypt(pasta+"/"+enc_files[enc_file],mediaKey, mtype,pasta2+"/"+enc_file+"."+ extension[mtype]):
#                                     print("Decrypted (hopefully)")
#                                     break
#                             except:
#                                 print("Erro")
                        



# exit()
# if __name__ == "__main__":
#     from optparse import OptionParser
#     parser = OptionParser(version='1')
#     parser.add_option(
#         '-m',
#         '--mime',
#         dest='mediaType',
#         default='image',
#         help="media type of the encrypted file. Default 'image'"
#     )
#     parser.add_option(
#         '-b',
#         '--base64',
#         dest='base64Key',
#         default=None,
#         help='media key in Base64'
#     )
#     parser.add_option(
#         '-j',
#         '--hex',
#         dest='hexKey',
#         default=None,
#         help='media key in Hex'
#     )
#     parser.add_option(
#         '-o',
#         '--output',
#         dest='output',
#         default=None,
#         help='path for the plaintext'
#     )
#     (options, args) = parser.parse_args()

#     fileName = args[0]
#     if options.base64Key is not None:
#         mediaKey = base64.b64decode(options.base64Key)
#     elif options.hexKey is not None:
#         mediaKey = bytes.fromhex(options.hexKey)
#     else:
#         print("You must specify the key in either "
#               "Base64 or Hex.\nUsage: decrypt.py -h")
#         sys.exit(1)

#     if decrypt(fileName, mediaKey, options.mediaType, options.output):
#         print("Decrypted (hopefully)")
