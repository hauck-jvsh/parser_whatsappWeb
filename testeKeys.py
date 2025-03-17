# import fnmatch
# import ccl_chromium_indexeddb
# from Crypto.Cipher import AES
# import hashlib
# import hmac
# import base64
# import sys
# import os
# from datetime import datetime
# import blackboxprotobuf
# type_whatsappmsg= {'1': {'type': 'str', 'name': 'body'},
#                   '2': {'type': 'str', 'name': 'caption'},
#                   '3': {'type': 'str', 'name': 'mediaText'},
#                   '4': {'type': 'str', 'name': 'loc'},
#                   '5': {'type': 'double', 'name': 'lng'},
#                   '7': {'type': 'double', 'name': 'lat'},
#                   '11': {'type': 'str', 'name': 'matchedText'},
#                   '12': {'type': 'str', 'name': 'title'}, 
#                   '13': {'type': 'str', 'name': 'description'}, 
#                   '21': {'type': 'bytes', 'name': ''}}
# type_prot={'1': {'type': 'message', 'message_typedef': type_whatsappmsg, 
#                   'name': 'currentMsg'}, 
#            '2': {'type': 'message', 'message_typedef': type_whatsappmsg, 'name': 'quotedMsg'}}

# def AESUnpad(s):
#     return s[:-ord(s[len(s)-1:])]


# def AESDecrypt(key, ciphertext, iv):
#     cipher = AES.new(key, AES.MODE_CBC, iv)
#     plaintext = cipher.decrypt(ciphertext)
#     return AESUnpad(plaintext)
#  # 'iv': (0, 187, 58, 106, 33, 82, 72, 36, 137, 99, 230, 93, 126, 66, 255, 52)

# encData=b'~\x86\xaa3; g\xc7gi\x83np\x06\xaf\xdc\xc6\xaa\xeaC \xf8\x0e\x8e\x14\xa4D\x02\xfd!\xdc&D\xb6\x15\x19v\xf9\xde\x98\xde\x17\xe2\xcb:d\xb6\xabq\x83\xf1bP\xf6,)\xf8?FU\xa6\xeb6ix\xb2\\\xc7=Tb\x97\xd0\x83\xac\x0b\xcb\xda\xd1\xb7'
# iv=bytes.fromhex("00BB3A6A215248248963E65D7E42FF34")

# import mmap
# with open("F:\\teste_decrypt_whatsapp\\HibRec_2025-03-10-20-02-26-49481\\ActiveMemory.bin", "rb") as f:
#     file_data = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

# tamanho = len(file_data)
# chunk_size = 16
# progress_block = 0x100000  # print progress every 1MB
# print(f"File size: {tamanho} bytes")
# print("tamanho",tamanho)
# tam_enc=len(encData)
# for i in range(0,tamanho,0x10):
#     #key=key.split(" ")[0]
#     #if count%10000==0:
#     #    print(count,key)
#     #key=bytes.fromhex(key)
#     if i % 0x100000 == 0:
#         percent = (i / tamanho) * 100
#         print(f"Progress: {percent:.2f}%  (offset: {i:#x})")

#     key=file_data[i:i+0x10]
#     decData=AESDecrypt(key,encData,iv)
#     if len(decData)<len(encData)-16:
#         continue
    
#     try:
#         message2,type=blackboxprotobuf.decode_message(decData,type_prot)
#         if "currentMsg" in message2 or "quotedMsg" in message2:
#             hexData=decData.hex()
#             print("Possivel chave encontrada",key.hex())
#             print("messagem",message2,hexData)
#     except:
#         pass
import multiprocessing
import blackboxprotobuf
from Crypto.Cipher import AES
import mmap
import math
import numpy as np

from messagemProtoBufDefinition import type_prot
from parserWhatsappweb import getEncryptedMessage


def shannon_entropy(data: bytes) -> float:
    """
    Calculate the Shannon entropy (bits per byte) of 'data'.
    For 16-byte data, the theoretical maximum is 8.0 bits/byte.
    """
    if not data:
        return 0.0
    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1
    length = len(data)
    ent = 0.0
    for count in freq.values():
        p = count / length
        ent -= p * math.log2(p)
    return ent
def shannon_entropy_np(data: bytes) -> float:
    """
    Calculate Shannon entropy (bits per byte) using NumPy.
    Typically returns a value in [0..8] for 16-byte data.
    """
    if not data:
        return 0.0
    arr = np.frombuffer(data, dtype=np.uint8)
    length = arr.size
    freq = np.bincount(arr, minlength=256)
    p = freq[freq > 0] / length
    ent = -np.sum(p * np.log2(p))
    return ent

def quick_unpad_check(plaintext: bytes) -> bytes:
    """PKCS#7 unpadding with basic validation."""
    pad_len = plaintext[-1]
    if pad_len < 1 or pad_len > 16:
        raise ValueError("Invalid PKCS#7 padding")
    return plaintext[:-pad_len]
def AESUnpad(s):
    return s[:-ord(s[len(s)-1:])]



def decrypt_and_decode(candidate_key: bytes, ciphertext: bytes, iv: bytes):
    """
    Try AES decryption with candidate_key. If successful, decode via blackboxprotobuf.
    Return (success: bool, msg_dict: dict or None).
    """
    try:
        cipher = AES.new(candidate_key, AES.MODE_CBC, iv)
        plaintext = cipher.decrypt(ciphertext)
        plaintext = quick_unpad_check(plaintext)
        # Attempt Protobuf decoding
        msg_dict, _ = blackboxprotobuf.decode_message(plaintext, type_prot)
        return (True, msg_dict)
    except:
        return (False, None)

def listInKeys(lista:list,dicionario:dict)->bool:
    return any(x in dicionario for x in lista )

def process_chunk(args):
    """
    Each process executes this on its assigned range.
    We'll return a list of (offset, key_hex, msg_dict) if a valid key is found.
    """
    filepath, start_offset, end_offset, encData, iv = args
    results = []

    # Open the file + create mmap in *this* child process
    with open(filepath, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        print("start",hex(start_offset))
        # Step in 16-byte blocks
        for offset in range(start_offset, end_offset, 16):
            key_candidate = mm[offset: offset+16]
            if len(key_candidate) < 16:
                break
            if shannon_entropy_np(key_candidate)<=3:
                continue
          
            #print("key",key_candidate.hex(),shannon_entropy(key_candidate),shannon_entropy_np(key_candidate))

            success, msg_dict = decrypt_and_decode(key_candidate, encData, iv)
            if success and listInKeys(["currentMsg","quotedMsg"],msg_dict):
                type_msg="currentMsg" if "currentMsg" in msg_dict else "quotedMsg"
                if isinstance(msg_dict[type_msg],dict ) and listInKeys(["body","caption","mediaText","loc","lat","lng","matchedText","title","description"],msg_dict[type_msg]):
                    print("key",key_candidate.hex(),shannon_entropy(key_candidate),shannon_entropy_np(key_candidate))
                    print("Mensagem",msg_dict)
                    results.append((offset, key_candidate.hex(), msg_dict))

        mm.close()

    return results
import os
def main(path_db,memdump_path):
    # Your ciphertext + IV
    #encData=b'\xf1\xaf\xd6Q\xa2.\x84\xd7\xd6\xb5\x0f\x96v\x86j\xfc\xb7\x90\x97\x0e\x0eu\x9c\x0e_\xab\xe6)\x1bF\xb8\x8a\xac:3b\xaen\xa5\x80\xddj<,\xf3\x92\xf1j\xa7,+\xd9\x8b\xff\xba\t\x80\xaf\xc8\x17"\xf9P\xa1\xfe\x93\xcf\x99\xca\xe6}\xc6\xbd\xbbe-\xfb\x16\xca\xbf\x85f\x8c\xe0`T%\ng\x98\xd6l\xa46\xecU'
    #iv= bytes((12, 65, 70, 171, 217, 32, 139, 111, 12, 21, 187, 64, 113, 39, 0, 111))
    #encData=b'~\x86\xaa3; g\xc7gi\x83np\x06\xaf\xdc\xc6\xaa\xeaC \xf8\x0e\x8e\x14\xa4D\x02\xfd!\xdc&D\xb6\x15\x19v\xf9\xde\x98\xde\x17\xe2\xcb:d\xb6\xabq\x83\xf1bP\xf6,)\xf8?FU\xa6\xeb6ix\xb2\\\xc7=Tb\x97\xd0\x83\xac\x0b\xcb\xda\xd1\xb7'
    #iv=bytes((0, 187, 58, 106, 33, 82, 72, 36, 137, 99, 230, 93, 126, 66, 255, 52))
    #memdump_path = r"F:\teste_decrypt_whatsapp\HibRec_2025-03-10-20-02-26-49481\ActiveMemory.bin"
    
    message=getEncryptedMessage(path_db)
    encData = message["_data"]
    iv =  bytes(message["iv"])
    print("mensagem",message)
    
    #print(decrypt_and_decode(bytes.fromhex("9ead014a52ee89494594029c45bcaaff"),encData,iv))
    # Get the file size (no need to read entire file into memory!)
    file_size = os.path.getsize(memdump_path)
    print(f"File size: {file_size} bytes")

    # Decide how many processes to use. Often = number of CPU cores.
    nprocs = 16
    print(f"Launching {nprocs} processes...")

    # Divide the file into nprocs chunks
    chunk_size = math.ceil(file_size / nprocs)

    # Build tasks for each process
    tasks = []
    start = 0
    for _ in range(nprocs):
        end = min(start + chunk_size, file_size)
        tasks.append((memdump_path, start, end, encData, iv))
        start = end
        if start >= file_size:
            break

    # Start the pool
    with multiprocessing.Pool(nprocs) as pool:
        results_list = pool.map(process_chunk, tasks)

    # Flatten all results
    all_candidates = [item for sublist in results_list for item in sublist]
    print(f"\nScan complete! Found {len(all_candidates)} candidate keys.\n")

    # Print them all
    for (offset, key_hex, msg) in all_candidates:
        print(f"Offset={offset:#x}, key={key_hex}")
        print("Decoded Message:", msg)

if __name__ == "__main__":
    import sys
    main(sys.argv[1],sys.argv[2])
