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


# https://mazzo.li/posts/whatsapp-backup.html
# message WhatsAppMessage {
#   string body = 1;
#   string caption = 2;
#   string loc = 4;
#   double lng = 5;
#   double lat = 7;
#   int32 paymentAmount1000 = 8;
#   string paymentNoteMsgBody = 9;
#   string canonicalUrl = 10;
#   string matchedText = 11;
#   string title = 12;
#   string description = 13;
#   bytes futureproofBuffer = 14;
# }

# message FullWhatsAppMessage {
#   WhatsAppMessage currentMsg = 1;
#   WhatsAppMessage quotedMsg = 1;
# }




type_whatsappmsg= {'1': {'type': 'str', 'name': 'body'},
                  '2': {'type': 'str', 'name': 'caption'},
                  '4': {'type': 'str', 'name': 'loc'},
                  '5': {'type': 'double', 'name': 'lng'},
                  '7': {'type': 'double', 'name': 'lat'},
                  '11': {'type': 'str', 'name': 'matchedText'},
                  '12': {'type': 'str', 'name': 'title'}, 
                  '13': {'type': 'str', 'name': 'description'}, 
                  '21': {'type': 'bytes', 'name': ''}}
type_prot={'1': {'type': 'message', 'message_typedef': type_whatsappmsg, 
                  'name': 'currentMsg'}, 
           '2': {'type': 'message', 'message_typedef': type_whatsappmsg, 'name': 'quotedMsg '}}

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

def loadDb(leveldb_folder_path:str, blob_folder_path=None):

    
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

def parseChats(indexedDB,aesKey:bytes|None=None):
   
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
            
        if isinstance(record.value["filehash"],str):
            contacts[contactid]["avatarHash"]=record.value["filehash"]

    
   
    
    messages=db_model["message"]
    
    for record in messages.iterate_records():
        if record.value is None or "t" not in record.value:
            continue


        chat_id=record.value["id"].split("_")[1]
        message={
            "mediaHash":getValue(record.value,"filehash"),
            "filename":getValue(record.value,"filename"),
            "encMediaHash":getValue(record.value,"encFilehash"),
            "mediaKey":getValue(record.value,"mediaKey"),
            "mimetype":getValue(record.value,"mimetype"),
            "type":getValue(record.value,"type"),
            "timeStamp":record.value["t"],
            "to": record.value["to"]["_serialized"] if getValue(record.value,"to") is not None else None,
            "from":record.value["from"],
            "thumb":getValue(record.value,"thumbnail"),
            "encThumbHash":getValue(record.value,"thumbnailEncSha256"),
            "thumbHash":getValue(record.value,"thumbnailSha256"),
            "url":getValue(record.value,"deprecatedMms3Url"),


                 }
        
        if message["from"].find(chat_id)>=0 or chat_id.find(message["from"])>=0:
            message["isFromMe"]=False
        else:
            message["isFromMe"]=True
        
        if "msgRowOpaqueData" in record.value:
            message["encData"]=record.value["msgRowOpaqueData"]
            #print(message["encData"]["_data"].hex())
            #print(bytes(message["encData"]["iv"]).hex())
            #input()
            message["decData"]=None
            if aesKey is not None:
                message["decData"]=AESDecrypt(aesKey,message["encData"]["_data"],bytes(message["encData"]["iv"]))
                message2,type=blackboxprotobuf.decode_message(message["decData"],type_prot)
                message["decData"]=message2
               

        if "author" in record.value:
            message["author"]= getValue(record.value["author"],"_serialized")
        
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

def getThumbTag(m, classnotfound):
        thumb = m["thumb"]

        

       
        if (thumb is not None):
            #print(thumb)
            img = TagHtml("img")
            img.set_attribute("class", "thumb")
            img.set_attribute("src",
                    "data:image/jpg;base64," + base64.b64encode(thumb).decode("utf-8") )
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
            
            img = getThumbTag(message, "imageImg")

            img.set_attribute("title", title)
            link.get_inner().append(img)
            div.get_inner().append(link)

            out.write(str(div))

        elif not isLink:
            out.write(str(getThumbTag(message, "imageImg")))
        
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

            img = getThumbTag(message, "videoImg")

            reportSource = message["mediaLink"]
            

            img.set_attribute("title", "Video")
            img.set_attribute("data-src1", reportSource)
            img.set_attribute("class", img.get_attribute("class") + " iped-video")

            link.get_inner().append(img)

            div.get_inner().append(link)


            out.write(str(div))
            out.write("<br/>")

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

            img = getThumbTag(message, "attachImg")

            img.set_attribute("title", "Attachment")
            link.get_inner().append(img)
            div.get_inner().append(link)

            out.write(str(div))

        else:
            texto=str(getThumbTag(message, "attachImg"))
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

        out.write("<div class=\"linha\" id=\"" + str(message["timeStamp"]) + "\">")
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
        
        if (message["type"] is not None):
            out.write(message["type"] + "<br>")
        
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
                
      

        if ("decData" in message and message["decData"] is not None):
            try:
                out.write(message["decData"]["currentMsg"]["body"])
            except:
                out.write(str(message["decData"]))
        elif "encData" in message and  message["encData"] is not None:
            out.write("Conteudo cifrado")


        out.write("<br/>")


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

    for name,chat in chats.items():
        createChatHTML(pastaRelatorios,chat,contacts,hashes)

def main():
    # assuming command line arguments are paths to the .leveldb and .blob folders
        
    #leveldb_folder_path = "C:\\Users\\HAUCK\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\IndexedDB\\https_web.whatsapp.com_0.indexeddb.leveldb"
    #blob_folder_path = "C:\\Users\\HAUCK\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\IndexedDB\\https_web.whatsapp.com_0.indexeddb.blob"
    #leveldb_folder_path="D:\\mem_whatsapp\\Default\\IndexedDB\\https_web.whatsapp.com_0.indexeddb.leveldb"
    #blob_folder_path="D:\\mem_whatsapp\\Default\\IndexedDB\\https_web.whatsapp.com_0.indexeddb.blob"
    #leveldb_folder_path="F:\\Downloads\\volatility3-2.5.2\\caso_dip\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 4\\IndexedDB\\https_web.whatsapp.com_0.indexeddb.leveldb"
    #blob_folder_path="F:\\Downloads\\volatility3-2.5.2\\caso_dip\\AppData\\Local\\Google\\Chrome\\User Data\\Profile 4\\IndexedDB\\https_web.whatsapp.com_0.indexeddb.blob"
    #blob_folder_path = None
    #leveldb_folder_path = "G:\\of2203526-2024\\user12528_chrome\\Default\\IndexedDB\\https_web.whatsapp.com_0.indexeddb.leveldb"
   

    pastaAnexos="C:\\Users\\HAUCK\\git\\whatsappWebService\\.wwebjs_auth\\session-teste\\Default\\dec_files"

    pastaRelatorios="C:\\Users\\HAUCK\\git\\whatsappWebService\\relatorio"
    Path(pastaRelatorios).mkdir(parents=True, exist_ok=True)

    #indexedDB=loadDb("G:\\of2203526-2024\\mat_2317_brownsers\\"+usuario+"\\Default\\IndexedDB\\https_web.whatsapp.com_0.indexeddb.leveldb",None)
    #indexedDB=loadDbFirefox("G:\\of2203526-2024\\mat_2317_brownsers\\"+usuario+"\\"+profile+"\\storage\\default\\https+++web.whatsapp.com^firstPartyDomain=whatsapp.com\\idb")

    indexedDB=loadDb("C:\\Users\\HAUCK\\git\\whatsappWebService\\.wwebjs_auth\\session-teste\\Default\\IndexedDB\\https_web.whatsapp.com_0.indexeddb.leveldb","C:\\Users\\HAUCK\\git\\whatsappWebService\\.wwebjs_auth\\session-teste\\Default\\IndexedDB\\https_web.whatsapp.com_0.indexeddb.blob")
    
    chats,contatcts=parseChats(indexedDB,b"\xdc\x26\x16\x16\xff\xba\x4a\x97\x86\x6e\x85\x53\x03\x95\xa0\xc9")
    createReports(pastaAnexos,pastaRelatorios,chats,contatcts)

if __name__ == "__main__":
    main()
