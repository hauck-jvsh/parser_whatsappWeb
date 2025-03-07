import os
from pathlib import Path
from decrypt_all_files import decriptyFiles,load_enc_files
from parserWhatsappweb import loadDb,loadDbFirefox,parseChats,createReports
import argparse
def _lazyLoad():
    global jFile,IPEDSource,FileOutputStream,BufferedOutputStream,IOUtil,IPEDSearcher
    from jnius import autoclass

    #importing java classes
    jFile = autoclass('java.io.File')
    IPEDSource = autoclass("iped.engine.data.IPEDSource")
    FileOutputStream = autoclass('java.io.FileOutputStream')
    BufferedOutputStream = autoclass('java.io.BufferedOutputStream')
    IOUtil = autoclass("iped.utils.IOUtil")
    IPEDSearcher = autoclass("iped.engine.search.IPEDSearcher")




def exportHashes(iped,hashes:set,saida:Path):
    print("buscando arquivos")
    searcher = IPEDSearcher(iped)
    searcher.setQuery(str(hashes).replace("{","sha\\-256:(").replace("}",")"))
    ids = searcher.search().getIds()
    print(f"Exportando {len(ids)} arquivos")
    for id in ids:
        item = iped.getItemByID(id)
        inputStream = item.getBufferedInputStream()
        path_saida=Path(saida,item.getName())
        outputStream = BufferedOutputStream(FileOutputStream(jFile(str(path_saida))))
        try:
            IOUtil.copyInputToOutputStream(inputStream, outputStream)
        finally:
            inputStream.close()
            outputStream.close()
        


def exportDB(instalation,path_saida):
    path_saida=Path(path_saida)
    path_saida.mkdir(parents=True, exist_ok=True)
    for item in instalation:
        path_org=str(Path(item.getPath()))
        path=path_org.replace(str(get_parent_folder(path_org)),"")
        
        try:
            indice = min([i for i in [path.find("/"),path.find("\\")] if i != -1])
        except:
            indice=-1
        path=path[indice+1:]
        if ".leveldb" in path_org:
            path=".leveldb/"+path
        if ".blob" in path_org:
            path=".blob/"+path
        path_export=Path(path_saida,path).parent
        path_export.mkdir(parents=True, exist_ok=True)
        path_export=Path(path_export,item.getName())
        inputStream = item.getBufferedInputStream()
        print("Exporting",path_org,"To",path_export)
        outputStream = BufferedOutputStream(FileOutputStream(jFile(str(path_export))))
        try:
            IOUtil.copyInputToOutputStream(inputStream, outputStream)
        finally:
            inputStream.close()
            outputStream.close()


def get_parent_folder(file_path):
    p = Path(file_path)
    whatsapp_folder= p.parent
    while whatsapp_folder:
        if "web.whatsapp" in whatsapp_folder.name:
            return whatsapp_folder
        whatsapp_folder=whatsapp_folder.parent
    return  None

def main(iped_path,case_folder,output,aesKey=None):
    os.environ['CLASSPATH'] = iped_path
    _lazyLoad()
    iped = IPEDSource(jFile(case_folder))


    searcher = IPEDSearcher(iped)

    # search for recovered files
    searcher.setQuery(f'path:"web.whatsapp"')
    ids = searcher.search().getIds()


    instalations=dict()
    for id in ids:
        item = iped.getItemByID(id)
        folder=str(get_parent_folder(item.getPath()))
        folder=folder.replace("indexeddb.leveldb","indexeddb").replace("indexeddb.blob","indexeddb")
        if folder not in instalations:
            instalations[folder]=[]
        instalations[folder].append(item)

    print("numero de instalacoes",len(instalations))
    i=0
    for inst in instalations.keys():
        i+=1
        path_saida=Path(f"{output}/instalacao_"+str(i))
        exportDB(instalations[inst],path_saida)
        print("Parsing database")
        indexedDB=None
        if Path(path_saida,".leveldb").is_dir(): # entao e chrome
            ldb= Path(path_saida,".leveldb")
            blob=Path(path_saida,".blob")
            if blob.is_dir():
                indexedDB=loadDb(str(ldb),str(blob))
            else:
                indexedDB=loadDb(str(ldb))
        elif(Path(path_saida,"idb").is_dir()): #entao eh firefox
            indexedDB=loadDbFirefox(str(Path(path_saida,"idb")))
        
        if indexedDB is None:
            continue
        
        path_enc_files=Path(path_saida,"enc_files")
        path_enc_files.mkdir(parents=True, exist_ok=True)
        path_dec_files=Path(path_saida,"dec_files")
        path_dec_files.mkdir(parents=True, exist_ok=True)
        print("Finding hashes")
        hashes=decriptyFiles(indexedDB,{},None)
        exportHashes(iped,hashes,path_enc_files)
        print("Decrypting files")
        decriptyFiles(indexedDB,load_enc_files(str(path_enc_files)),str(path_dec_files))
        path_report=Path(path_saida,"reports")
        path_report.mkdir(parents=True, exist_ok=True)
        print("Parsing chats")
        chats, contacts = parseChats(indexedDB,aesKey)
        print("Creating reporting")
        createReports(str(path_dec_files), str(path_report), chats, contacts)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Processamento do whatsapp web em casos iped",
        # Use Portuguese for consistency with variable names like 'pastaAnexos'
        epilog="Exemplo: ipedWhatsAppParser.py pasta_iped pasta_caso diretorio_saida "
    )
    
    # Required positional arguments
    parser.add_argument('pasta_iped', help='Diretório da instalacao local do IPED')
    parser.add_argument('pasta_caso', help='Caminho do diretório do caso processado')
    parser.add_argument('diretorio_saida', help='Pasta para salvar os relatórios')

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
    
    main(args.pasta_iped,args.pasta_caso,args.diretorio_saida,args.aesKey)