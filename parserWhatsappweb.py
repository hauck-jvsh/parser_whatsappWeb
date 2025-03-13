import fnmatch
import ccl_chromium_indexeddb
from Crypto.Cipher import AES
import hashlib
import hmac
import base64
import sys
import os
from datetime import datetime
import mozidbedit.mozidbedit.mozidb as mozidb
from pathlib import Path
import blackboxprotobuf
import filetype
import argparse
from messagemProtoBufDefinition import type_prot

class TagHtml:
    def __init__(self, tagname):
        self.tagname = tagname
        self.inner = []
        self.attributes = {}

    def set_attribute(self, attribute, value):
        self.attributes[attribute] = value

    def get_attribute(self, attribute):
        return self.attributes.get(attribute)

    def __str__(self):
        sb = []
        sb.append(f"<{self.tagname}")

        for attr, value in self.attributes.items():
            sb.append(f" {attr}")
            if value is not None:
                sb.append(f"=\"{value}\"")
        sb.append(">")

        for subelm in self.inner:
            sb.append(str(subelm))

        sb.append(f"</{self.tagname}>")
        return "".join(sb)

    def get_inner(self):
        return self.inner

    def set_inner(self, inner):
        self.inner = inner

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


def AESDecrypt(key, ciphertext, iv:bytes):
    #print(key,iv)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = cipher.decrypt(ciphertext)
    return AESUnpad(plaintext)

def loadDb(leveldb_folder_path:str, blob_folder_path:str|None=None):

    
    #print("ola1")
    # open the indexedDB:
    indexedDB = ccl_chromium_indexeddb.WrappedIndexDB(leveldb_folder_path, blob_folder_path)
    for db in indexedDB.database_ids:
        print(db)
    return indexedDB
    
def loadDbFirefox(folder):
    print(folder)
    databases={}
    for root, dir, files in os.walk(folder):
        for item in fnmatch.filter(files, "*.sqlite"):
            dbFile=folder+"\\"+item
            #print(dbFile)
            conn=mozidb.IndexedDB(dbFile)
            databases[conn.get_name()]=mozidb.IDBObjectWrapper(conn)
            print(conn.get_name())
    return databases



def getValue(dict,key):
    try:
        return dict[key]
    except:
        return None
    

def getMessage(rawData,aesKey,quoted=False):
    chat_id=rawData["id"].split("_")[1]
    message={
        "chat_id":chat_id,
        "quoteMsg":quoted,
        "isForwarded": rawData["isForwarded"] if "isForwarded" in rawData else False,
        "mediaHash":getValue(rawData,"filehash"),
        "filename":getValue(rawData,"filename"),
        "encMediaHash":getValue(rawData,"encFilehash"),
        "mediaKey":getValue(rawData,"mediaKey"),
        "mimetype":getValue(rawData,"mimetype"),
        "type":getValue(rawData,"type"),
        "timeStamp": None if quoted else rawData["t"],
        "to": rawData["to"]["_serialized"] if getValue(rawData,"to") is not None else None,
        "from": rawData["from"]["_serialized"] if quoted else rawData["from"],
        "thumb":getValue(rawData,"thumbnail"),
        "encThumbHash":getValue(rawData,"thumbnailEncSha256"),
        "thumbHash":getValue(rawData,"thumbnailSha256"),
        "url":getValue(rawData,"deprecatedMms3Url"),
                }
  
    
    if message["from"].find(chat_id)>=0 or chat_id.find(message["from"])>=0:
        message["isFromMe"]=False
    else:
        message["isFromMe"]=True
    
    if "msgRowOpaqueData" in rawData:
        message["encData"]=rawData["msgRowOpaqueData"]
        #print(message["encData"]["_data"].hex())
        #print(bytes(message["encData"]["iv"]).hex())
        #input()
        print("dados cifrados",message["encData"])
        message["decData"]=None
        if aesKey is not None and not quoted:
            message["decData"]=AESDecrypt(aesKey,message["encData"]["_data"],bytes(message["encData"]["iv"]))
            message2,type=blackboxprotobuf.decode_message(message["decData"],type_prot)
            message["decData"]=message2
            

    if "author" in rawData:
        message["author"]= getValue(rawData["author"],"_serialized")

    
    if  "quotedMsg" in rawData and isinstance(rawData["quotedMsg"],dict) and "from" in rawData["quotedMsg"]:
        rawData["quotedMsg"]["id"]=rawData["id"]        
        message["quotedMsg"]=getMessage(rawData["quotedMsg"],aesKey,True)
        message["quotedMsg"]["decData"]=message["decData"]

    return message
    
def error_handler(key, value):
    print(key,value)

def parseChats(indexedDB,aesKey:bytes|None=None):
    if "model-storage" not in indexedDB:
       return {},{}
    print("Inicio do parsing")
    db_model=indexedDB["model-storage"]
    chats={}
    contacts={}
    for record in db_model["chat"].iterate_records():
         if record.value is None:
            continue
         chats[record.value["id"]]={
             "id":record.value["id"],
             "name":getValue(record.value,"name"),
             "chat": {}
         }
         contacts[record.value["id"].split("@")[0]]={
             "id":record.value["id"],
             "name":getValue(record.value,"name"),
             "isAddressBookContact":0
         }
    for record in db_model["contact"].iterate_records():
        if record.value is None:
            continue
       
        name=None

        if name is None and "name" in record.value:
            name=record.value["name"]
        if name is None and "pushname" in record.value:
            name=record.value["pushname"]
        
        if name is not None:
            
            if record.value["id"] in contacts:
                if contacts[record.value["id"]]["name"] is not None:
                    contacts[record.value["id"]]["name"]=name
                    contacts[record.value["id"]]["isAddressBookContact"]=getValue(record.value,"isAddressBookContact")
                    
            else:
                contacts[record.value["id"].split("@")[0]]={
                    "id":record.value["id"],
                    "name":name
                }
                contacts[record.value["id"].split("@")[0]]["isAddressBookContact"]=getValue(record.value,"isAddressBookContact")
            
            phoneNumber=getValue(record.value,"phoneNumber")
            if phoneNumber is not None:
                phoneNumber=phoneNumber.split("@")[0]
               
                if phoneNumber in contacts:
                     contacts[phoneNumber]["name"]=name
                     contacts[phoneNumber]["phoneNumber"]=phoneNumber
                else:
                     contacts[phoneNumber]={
                        "id":record.value["id"],
                        "name":name,
                        "phoneNumber":phoneNumber
                        }
                contacts[phoneNumber]["isAddressBookContact"]=getValue(record.value,"isAddressBookContact")


    for record in db_model["profile-pic-thumb"].iterate_records():
        if record.value is None:
            continue
        contactid=record.value["id"].split("@")[0]
        if contactid not in contacts:
            contacts[contactid]={
                "id":record.value["id"],
                "name":None,
                "isAddressBookContact":None
            }
            
        if "filehash" in record.value and isinstance(record.value["filehash"],str):
            contacts[contactid]["avatarHash"]=record.value["filehash"]

    
   
    
    messages=db_model["message"]
    
    for record in messages.iterate_records(bad_deserializer_data_handler=error_handler):
        if record.value is None or "t" not in record.value or "rowId" not in record.value:
            continue
        message=getMessage(record.value,aesKey)
        chat_id=message["chat_id"]

        if chat_id in chats:
            chats[chat_id]["chat"][str(record.value["rowId"])]=message
        else:
            chats[chat_id]= {
                "id":chat_id,
                "name":chat_id,
                "chat":{str(record.value["rowId"]): message}
            }
        
                

        
    for chat in chats.values():
      
        try:
            chat["chat"]=list(chat["chat"].values())
        except:
            chat["chat"]=[]
            

            
    return chats,contacts

def getImageResourceAsEmbedded(resource):
    return getResourceAsEmbedded(resource,"image")
def getResourceAsEmbedded(resource,mime):
    ext = resource.split(".")[-1]
    type = "jpg"
    if (len(ext) > 0):
        type = ext
    
    return "data:"+mime+"/" + type + ";base64," + base64.b64encode(open(resource,"rb").read()).decode("utf-8")


def printMessageFileHeader(out, title, avatar):
        out.write("<!DOCTYPE html>\n"
                + "<html>\n" 
                + "<head>\n" 
                + "	<title>" + title + "</title>\n" 
                + "	<meta http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-8\" />\n"
                + "	<meta name=\"viewport\" content=\"width=device-width\" />\n" 
                + "     <meta charset=\"UTF-8\" />\n" 
                + "	<link rel=\"shortcut icon\" href=\"" 
                + getImageResourceAsEmbedded("img/favicon.ico") + "\" />\n" 
                + "<style>\n" + open("css/whatsapp.css","r").read()
                + "\n</style>\n" + "<script>"
                + open("js/whatsapp.js","r").read() + "</script>"
                "<style>.tab {display: inline-block; border-collapse: collapse; border: 1px solid black;}"
                + ".cel {border-colapse: colapse; border: 1px solid black; font-family: Arial, sans-serif;}</style></head>\n" 
                + "<style>.check {vertical-align: top;}</style>" + "<body>\n" 
                + "<div id=\"topbar\" class=''>\n"
                + "	<span class=\"left\">" 
                + " &nbsp; ")

        if (avatar is not None) :
            out.write("<img src=\"data:image/jpg;base64," + base64.b64encode(avatar) 
                            + "\" width=\"40\" height=\"40\"/>")

        
        out.write(title + "</span>\n" 
                + "</div>\n"
                + "<div id=\"conversation\">\n" 
                + "<br/><br/><br/>")

def getThumbTag(m:any, classnotfound:str,thumbBody:bool=False):
        thumb = m["thumb"]
        
        if thumbBody:
            try:
                
                decData=m["decData"]["quotedMsg" if m["quoteMsg"] else "currentMsg"]
                if len(decData["body"])>0:
                    thumb_new=base64.b64decode(decData["body"])
                    if "image" in filetype.guess_mime(thumb_new):
                        decData["body"]="thumb"
                        if thumb is None:
                            m["thumb"]=thumb=thumb_new
            except:
                thumb=None
            
       
        if (thumb is not None):
            img = TagHtml("img")
            img.set_attribute("class", "thumb")
            if b'PNG' in thumb:
                data_type="image/png"
            else:
                data_type="image/jpg"

            img.set_attribute("src",
                    "data:"+data_type+";base64," + base64.b64encode(thumb).decode("utf-8") )
        else:
            img = TagHtml("div")
            img.set_attribute("class", classnotfound)
        
        return img
    

def printImage(out, message, isLink=False):
        title="Image"
        if isLink:
            out.write("<b> Link </b><br/>")
            title = "Link"
            
        
        if ("mediaLink" in message):
            
            message["thumb"]=open(message["mediaLink"],"rb").read()

            div = TagHtml("div")
           

            link = TagHtml("a")
            #link.set_attribute("onclick", "app.open('hash:" + message["mediaHash"] + "')")
            link.set_attribute("href",getImageResourceAsEmbedded(message["mediaLink"]) )
            
            img = getThumbTag(message, "imageImg",True)

            img.set_attribute("title", title)
            link.get_inner().append(img)
            div.get_inner().append(link)

            out.write(str(div))

        elif not isLink:
            out.write(str(getThumbTag(message, "imageImg",True)))
        
        out.write("<br/>")

    
        
def printMessageFileFooter(out) :
        out.write("	<br /><br /><br />\n" 
                + "</div>\n"
                + "<div id=\"lastmsg\">&nbsp;</div>\n" 
                + "</body>\n"
                + "</html>")


def printVideo(out,message):

        if ("mediaLink" in message) :


            div = TagHtml("div")
            

            link = TagHtml("a")
            link.set_attribute("onclick", "app.open('hash:" + message["mediaHash"] + "')")

            img = getThumbTag(message, "videoImg",True)
           
            try:
                reportSource = getImageResourceAsEmbedded(message["mediaLink"],message["mimetype"])
                img.set_attribute("data-src1", reportSource)
            except:
                pass
                
            img.set_attribute("title", "Video")
           
            img.set_attribute("class", img.get_attribute("class") + " iped-video")
           

            link.get_inner().append(img)

            div.get_inner().append(link)


            out.write(str(div))
            out.write("\n<br/>")

        else:
            out.write(str(getThumbTag(message, "videoImg")))
        

def printAttachment(out,  message) :
        
        if(isinstance(message["filename"],bytes) and message["filename"] is not None):
            try:
                message["filename"]=message["filename"].decode("latin-1")
            except:
                message["filename"]=message["filename"].decode("utf-8")
                
        
        if ("mediaLink" in message) :


            div = TagHtml("div")
            

            link = TagHtml("a")
            #link.set_attribute("onclick", "app.open('hash:" + message["mediaHash"] + "')")
            link.set_attribute("href", getResourceAsEmbedded(message["mediaLink"],"application"))
            #print(message["thumb"])
            if(message["filename"] is not None):
                link.get_inner().append(message["filename"]+"<br/>")

            img = getThumbTag(message, "attachImg",True)

            img.set_attribute("title", "Attachment")
            link.get_inner().append(img)
            div.get_inner().append(link)

            out.write(str(div))

        else:
            texto=str(getThumbTag(message, "attachImg",True))
            if(message["filename"] is not None and isinstance(message["filename"],str)):
                texto=message["filename"]+"<br/>"+texto
            out.write(texto)
        
        out.write("<br/>")

def printAudio( out,  message):

    img = TagHtml("div")
    img.set_attribute("title", "Audio")

    if ("mediaLink" in message):

        
        #print("messagem",message)
        div = TagHtml("div")
        

        link =  TagHtml("a")
        link.set_attribute("onclick", "app.open('hash:" + message["mediaHash"] + "')")

        reportSource = message["mediaLink"]
        
        
        img.set_attribute("data-src1", getResourceAsEmbedded(reportSource,"audio"))
        
        
        img.set_attribute("class", "audioImg iped-audio")

        link.get_inner().append(img)
        div.get_inner().append(link)
        out.write(str(div))

    else:
        img.set_attribute("class", "audioImg")
        out.write(str(img))
    

    out.write("<br/>")

    
    



def printMessage(out, message,contacts):

        out.write("\n<div class=\"linha\" id=\"" + str(message["timeStamp"]) + "\">")
        try:
            decData=message["decData"]["quotedMsg" if message["quoteMsg"] else "currentMsg"]
        except:
            decData=None
        if (message["isFromMe"]):
            out.write("<div class=\"bbr\"><div class=\"outgoing to\">")
        else:
            out.write(
                    "<div class=\"bbl\"><div class=\"aw\"><div class=\"awl\"></div></div><div class=\"incoming from\">")
        
        contact=None
        if "author" in message and isinstance(message["author"],str):
            contact = message["author"]
        else:
            contact = message["from"]
        
        

        if (contact is not None):
            if contact.split("@")[0] in contacts and isinstance(contacts[contact.split("@")[0]]["name"],str):
                contact=contact +" - "+contacts[contact.split("@")[0]]["name"]
                #print(contact)
            out.write("<span style=\"font-family: Arial; color: #b4c74b;\">" 
                    + contact + "</span><br/>")
           
            if message["isForwarded"]:
                out.write("<span style=\"font-family: Arial;font-style:italic; color: #8696a0;\">")
                out.write('<svg viewBox="0 0 16 16" height="16" width="16" preserveAspectRatio="xMidYMid meet" class="" version="1.1"><title>forwarded</title><path d="M9.51866667,3.87533333 C9.51866667,3.39333333 10.1006667,3.152 10.4406667,3.49266667 L14.4706667,7.52666667 C14.682,7.738 14.682,8.07933333 14.4706667,8.29066667 L10.4406667,12.3246667 C10.1006667,12.6646667 9.51866667,12.424 9.51866667,11.942 L9.51866667,10.1206667 C6.12133333,10.1206667 3.63266667,11.0906667 1.78266667,13.1946667 C1.61866667,13.3806667 1.31466667,13.2226667 1.38133333,12.984 C2.33466667,9.53533333 4.66466667,6.31466667 9.51866667,5.62066667 L9.51866667,3.87533333 Z" fill="currentColor"></path></svg>')
                out.write("Encaminhada</span><br/>")
        
        
        if "quotedMsg" in message:
            out.write("<div style='zoom: 0.7;'>quoted msg")
            printMessage(out,message["quotedMsg"],contacts)
            out.write("</div>")
        
        if (message["type"] is not None):
            out.write(message["type"] + "<br>")
            if message["type"]=="revoked":
                out.write("<span style=\"font-family: Arial; color: #8696a0;\">")
                out.write('<svg viewBox="0 0 24 24" height="24" width="24" preserveAspectRatio="xMidYMid meet" class="" fill="none"><title>recalled</title><path fill-rule="evenodd" clip-rule="evenodd" d="M7.75897 6.43054C8.93584 5.533 10.4057 5 12 5C15.866 5 19 8.13401 19 12C19 13.5943 18.467 15.0642 17.5695 16.241L7.75897 6.43054ZM6.35707 7.85707C5.50399 9.01706 5 10.4497 5 12C5 15.866 8.13401 19 12 19C13.5503 19 14.9829 18.496 16.1429 17.6429L6.35707 7.85707ZM12 3C7.02944 3 3 7.02944 3 12C3 16.9706 7.02944 21 12 21C16.9706 21 21 16.9706 21 12C21 7.02944 16.9706 3 12 3Z" fill="currentColor"></path></svg>')
                out.write("Mensagem apagada</span><br/>")

        
        if (message["mimetype"] is not None and isinstance(message["mimetype"],str)):
            if (message["mimetype"].startswith("video")) :
                printVideo(out, message)
            elif (message["mimetype"].startswith("image")):
                printImage(out, message)
            elif (message["mimetype"].startswith("audio")):
                printAudio(out, message)
            elif (message["mimetype"].startswith("link")):
                printImage(out, message,True)
            else:
                printAttachment(out, message)
            try:
                out.write(decData["mediaText"])
            except:                
                pass
                
      

        if (decData is not None):
            try:
                out.write(decData["body"])
                if "caption" in decData:
                    out.write(decData["caption"])
            except:
                if len(decData)>0:
                    out.write(str(decData))
        elif "encData" in message and  message["encData"] is not None:
            out.write("Conteudo cifrado")


        out.write("<br/>")


        if not message["quoteMsg"]:
            out.write("<span class=\"time\">")
            out.write(datetime.fromtimestamp(message["timeStamp"]).isoformat() + " &nbsp;")
            out.write("</span>")

        if (message["isFromMe"]):
            out.write("</div><div class=\"aw\"><div class=\"awr\"></div></div>")
        else:
            out.write("</div>")
        

        out.write("</div></div>")

    

def createChatHTML(pasta,chat,contacts,hashes):
   
    title=None
    try:
        if chat["name"] is not None:
            if isinstance(chat["name"],str):
                title=chat["id"]+"_"+chat["name"]
    except:
        title=str(chat["id"])
    if not isinstance(title,str):
        title=str(chat["id"])
    name=pasta+"/"+chat["id"]+".html"
    file=open(name,"w", encoding="utf-8")
    avatar=None
    if chat["id"] in contacts and  "avatarHash" in contacts[chat["id"]]:
        avatarHash=base64.b64decode(contacts[chat["id"]]["avatarHash"])
        print("tem hash")
        if avatarHash.hex() in hashes:
            print("tem arquivo")
            avatar=open(hashes[avatarHash.hex()],"rb").read()
    
    printMessageFileHeader(file,title,avatar)
    
    chat["chat"].sort(key=lambda i:i["timeStamp"])
    for msg in chat["chat"]:
        if "mediaHash" in msg and isinstance(msg["mediaHash"],str):
            mediaHash=base64.b64decode( msg["mediaHash"])
            if mediaHash.hex() in hashes:
                msg["mediaLink"]=hashes[mediaHash.hex()]
        if "thumbHash" in msg and isinstance(msg["thumbHash"],str):
            thumbHash=base64.b64decode( msg["thumbHash"])
            if thumbHash.hex() in hashes:
                msg["thumb"]=open(hashes[thumbHash.hex()],"rb").read()
                
                
        printMessage(file,msg,contacts)
        
    
    printMessageFileFooter(file)
    file.close()


def createContactPage(pasta,contacts):
    contact_file=open(pasta+"/"+"contatos.html","wb")
    contact_file.write(b"<html><body><table border=1>\n")
    contact_file.write(b"<tr><th>N</th><th>Id</th><th>phoneNumber</th><th>name</th><th>Agenda</th></tr>\n")
    i=0
    for id,contact in contacts.items():
        if not isinstance(id,str) or id=="0":
            continue
        i+=1
        phonenumber="-"
        name="-"
        if(isinstance(getValue(contact,"phoneNumber"),str)):
            phonenumber=getValue(contact,"phoneNumber")
        if(isinstance(getValue(contact,"name"),str)):
            name=getValue(contact,"name")
        isAddressBookContact="-"
        if contact["isAddressBookContact"] is not None and contact["isAddressBookContact"]!=0:
            isAddressBookContact="Sim"
        contact_file.write(("<tr><td>"+str(i)+"</td><td>"+id+"</td><td>"+phonenumber+"</td><td>"+name+"</td><td>"+isAddressBookContact+"</td></tr>\n").encode("utf-8"))
    
    contact_file.write(b"</table></body></html>\n")
    contact_file.close()

def createReports(pastaAnexos,pastaRelatorios,chats,contacts):
    
    hashes={}
    for root, dir, files in os.walk(pastaAnexos):
        print(root)
        
        for item in fnmatch.filter(files, "*"):
            sha256Hash = hashlib.sha256(open(pastaAnexos+"/"+item,"rb").read())
            sha256Hashed = sha256Hash.hexdigest()
            #print(item,sha256Hashed)
            hashes[sha256Hashed]=pastaAnexos+"/"+item
    
   
    createContactPage(pastaRelatorios,contacts)
    totmsgs=0
    for name,chat in chats.items():
        totmsgs+=len(chat["chat"])
        print("mensagens em",chat["id"],"-",chat["name"],":",len(chat["chat"]))
        createChatHTML(pastaRelatorios,chat,contacts,hashes)
    print("Total de mensagens extraidas",totmsgs)

def main():
    parser = argparse.ArgumentParser(
        description="Processamento de IndexedDB para chats de navegadores",
        # Use Portuguese for consistency with variable names like 'pastaAnexos'
        epilog="Exemplo: script.py pasta_anexos relatorios caminho_indexeddb tipo [hex_key]"
    )
    
    # Required positional arguments
    parser.add_argument('pastaAnexos', help='Diretório de anexos')
    parser.add_argument('pastaRelatorios', help='Pasta para salvar os relatórios')
    parser.add_argument('caminhoIndexedDB', help='Caminho do arquivo IndexedDB ou diretório')
    parser.add_argument(
        'tipo',
        type=lambda s: s.lower(),
        choices=['firefox', 'chrome'],
        help="Tipo de navegador ('firefox' ou 'chrome')"
    )
    
    # Argumento opcional com sinalizador --aeskey
    def parse_aes_key(key_str):
        if key_str is None:
            return None # Permite omitir a chave
        try:
            return bytes.fromhex(key_str)
        except ValueError:
            raise argparse.ArgumentTypeError("Chave AES deve ser uma string hexadecimal válida")
    
    parser.add_argument(
        '--aesKey',
        dest='aesKey',  
        default=None,
        type=parse_aes_key,
        help="Chave de criptografia em formato hexadecimal (opcional)"
    )

    args = parser.parse_args()
    
    pastaAnexos = args.pastaAnexos
    pastaRelatorios = args.pastaRelatorios
    caminhoIndexedDB = args.caminhoIndexedDB
    tipo = args.tipo  # Already lowercase via lambda conversion
    aesKey = args.aesKey  # Now properly converted to bytes or None

    Path(pastaRelatorios).mkdir(parents=True, exist_ok=True)
    
    if tipo == "firefox":
        indexedDB = loadDbFirefox(caminhoIndexedDB)
    elif tipo == "chrome":
        blob_folder_path = caminhoIndexedDB.replace(".leveldb", ".blob")
        if os.path.exists(blob_folder_path):
            indexedDB = loadDb(caminhoIndexedDB, blob_folder_path)
        else:
            indexedDB = loadDb(caminhoIndexedDB, None)

    # Extract and process chats/contacts
    chats, contacts = parseChats(indexedDB, aesKey)
    
    createReports(pastaAnexos, pastaRelatorios, chats, contacts)

if __name__ == "__main__":
    main()

