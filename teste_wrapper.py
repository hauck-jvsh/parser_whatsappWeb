import sys
import ccl_chromium_indexeddb
from Crypto.Cipher import AES
import hashlib
import hmac
import base64
import sys
import re

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

def loadDb():

    # assuming command line arguments are paths to the .leveldb and .blob folders
    #leveldb_folder_path = "IndexedDB\\file__0.indexeddb.leveldb"
    #blob_folder_path = "IndexedDB\\file__0.indexeddb.blob"
    leveldb_folder_path = "C:\\Users\\HAUCK\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\IndexedDB\\https_web.whatsapp.com_0.indexeddb.leveldb"
    blob_folder_path = "C:\\Users\\HAUCK\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\IndexedDB\\https_web.whatsapp.com_0.indexeddb.blob"
    #leveldb_folder_path="F:\\Downloads\\volatility3-2.5.2\\caso_dip\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 4\\IndexedDB\\https_web.whatsapp.com_0.indexeddb.leveldb"
    #blob_folder_path="F:\\Downloads\\volatility3-2.5.2\\caso_dip\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 4\\IndexedDB\\https_web.whatsapp.com_0.indexeddb.blob"
    print("ola1")
    # open the indexedDB:
    indexedDB = ccl_chromium_indexeddb.WrappedIndexDB(leveldb_folder_path, blob_folder_path)
    return indexedDB
    
def printTables(db):
    for table in db.object_store_names:
        print(table)

def parseChats(indexedDB,aeskeys):

    for dbname in indexedDB.database_ids:
        print(dbname)
    #db_work=indexedDB['worker-storage']
    db_model=indexedDB['model-storage']
    db_enc=indexedDB['wawc_db_enc']
    db_wawc=indexedDB['wawc']
    db_sig=indexedDB['signal-storage']
    db_fts=indexedDB['fts-storage']
    
    printTables(db_fts) 
    keys=db_fts['fts-v3-index']
    for record in keys.iterate_records():
        print(record.value)
        
        
    
    print("-----------------------")
    
    messages=db_model["message"]
    print("ola")
    chats={}
    hashes={}
    #aeskey=b"\x01\x0B\x10\x06\x10\x11\xA0\x74\x73\x48\xEA\x17\x52\xD7\x84\x28\xD0\xBF\xD3\xC4\xAF\x0D\x27\xC0\x42\x20\x91\xEE\x64\xDE\xA8\xE4\x52\xCA\xB4\xCA\x5B\x2C\xB4\x22\x2E\x5D\xAF\x01\x3D\x1B\xDF\x71\xBD\xAB\xCE\x7B\xB8\x75\x29\x27\x4F\x34\x7B\x02\x7B\x02\xA0\x00\x00\x00"
    for record in messages.iterate_records():
        if record.value is None:
            continue
        #print("aa",record.value)
        
        if  record.value['type']=="chat" and len(record.value['msgRowOpaqueData']["_data"])>50:
            
            for key in aeskeys:
                #print(record.value['type'],len(record.value['msgRowOpaqueData']["_data"]))
                
                #key=bytearray.fromhex(key)
                decripted=AESDecrypt(key,record.value['msgRowOpaqueData']["_data"],bytes(record.value['msgRowOpaqueData']["iv"]))
                
                #decripted=strings(decripted)
                #print(decripted)
                if(len(decripted)>0 and sum([len(x) for x in strings(decripted)])/len(decripted)>0.4):
                    #print(key)
                    print(sum([len(x) for x in strings(decripted,5)]))
                    print(len(decripted),strings(decripted))
                    #break
               

                #print(record.value["msg"])
            break
        chat_id=record.value["id"].split("_")[1]
        if chat_id in chats:
            chats[chat_id].append(record.value)
        else:
            chats[chat_id]=[record.value]
    return hashes


def findHashes(hashes,pasta):
    for root, dir, files in os.walk(pasta):
        print(root)
        for item in fnmatch.filter(files, "*"):
            data=open(pasta+"/"+item,"rb").read()
            
            sha256Hash = hashlib.sha256()
            sha256Hashed = sha256Hash.hexdigest()
            print(sha256Hashed)
            enc_files[sha256Hashed]=pasta+"/"+item    
