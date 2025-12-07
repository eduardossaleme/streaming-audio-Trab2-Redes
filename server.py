# server.py
import socket
import threading
import wave
import os
import select
import json
import time
import ssl
import pyaudio

HOST = ""
PORT = 6795
CHUNK = 4096

# Configurações para transmissão ao vivo
LIVE_RATE = 44100
LIVE_CHANNELS = 1
LIVE_FORMAT = pyaudio.paInt16
LIVE_SAMPWIDTH = 2

with open("users.json", "r") as f: USERS = json.load(f)["usuarios"]
with open("musicas.json", "r") as f: MUSICAS = json.load(f)["musicas"]

def send_line(sock, text):
    try: sock.sendall((text + "\n").encode())
    except: pass

class ClientHandler(threading.Thread):
    def __init__(self, conn, addr):
        super().__init__(daemon=True)
        self.conn = conn
        self.addr = addr
        self.running = True
        self.paused = False

    def recv_line(self, timeout=None):
        buf = b""
        self.conn.settimeout(timeout)
        try:
            while True:
                c = self.conn.recv(1)
                if not c: return None
                if c == b"\n": break
                buf += c
        except: return None
        finally: self.conn.settimeout(None)
        return buf.decode().strip()

    def run(self):
        print(f"[CONECTADO] {self.addr}")
        audio_interface = None
        stream_in = None
        wf = None
        
        try:
            #autenticação
            line = self.recv_line(timeout=5)
            if not line: return
            parts = line.split()
            if len(parts) == 3 and parts[0] == "AUTH" and \
               USERS.get(parts[1]) == parts[2]:
                send_line(self.conn, "AUTH_OK")
            else:
                send_line(self.conn, "AUTH_FAIL")
                return

            #envio da lista
            lista_completa = ["🔴 TRANSMISSAO AO VIVO"] + MUSICAS
            send_line(self.conn, ",".join(lista_completa))
            
            #recebe a escolha
            escolha = self.recv_line(timeout=10)
            if not escolha or escolha not in lista_completa:
                send_line(self.conn, "INVALID")
                return
            send_line(self.conn, "OK")
            print(f"[STREAM] {escolha} -> {self.addr}")

            #setup de transmissão de audio
            is_live = (escolha == "🔴 TRANSMISSAO AO VIVO")
            
            if is_live:
                audio_interface = pyaudio.PyAudio()
                stream_in = audio_interface.open(
                    format=LIVE_FORMAT, channels=LIVE_CHANNELS,
                    rate=LIVE_RATE, input=True, frames_per_buffer=CHUNK
                )
                channels, sampwidth, rate = LIVE_CHANNELS, LIVE_SAMPWIDTH, LIVE_RATE
            else:
                if not os.path.isfile(escolha): return
                wf = wave.open(escolha, "rb")
                channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                rate = wf.getframerate()
            
            send_line(self.conn, f"{channels},{sampwidth},{rate}")

            chunk_duration = CHUNK / rate 
            bytes_per_chunk = CHUNK * sampwidth * channels
            silence = b"\x00" * bytes_per_chunk

            self.conn.setblocking(0)
            last_chunk_time = time.time()

            #loop principal
            while self.running:
                try:
                    rlist, wlist, _ = select.select([self.conn], [self.conn], [], 0.01)
                except ValueError: break 

                if self.conn in rlist:
                    try:
                        data = self.conn.recv(1024)
                        if not data: break
                        cmds = data.decode(errors='ignore').split("\n")
                        for c in cmds:
                            c = c.strip()
                            if c == "PAUSE": self.paused = True
                            elif c == "PLAY": self.paused = False
                            elif c == "STOP": self.running = False
                    except: break

                #envio do audio
                if self.conn in wlist:
                    if is_live:
                        if not self.paused:
                            try:
                                chunk = stream_in.read(CHUNK, exception_on_overflow=False)
                                self.conn.sendall(chunk)
                            except: break
                        else:
                            time.sleep(0.01)
                    else:
                        now = time.time()
                        if (now - last_chunk_time) >= chunk_duration:
                            chunk = silence
                            if not self.paused:
                                chunk = wf.readframes(CHUNK)
                                if not chunk:
                                    wf.rewind()
                                    chunk = wf.readframes(CHUNK)
                            
                            try:
                                self.conn.sendall(chunk)
                                last_chunk_time = now
                            except: break
                        else:
                            time.sleep(0.001)

            # Limpeza
            if wf: wf.close()
            if stream_in: 
                stream_in.stop_stream()
                stream_in.close()
            if audio_interface: audio_interface.terminate()

        except Exception as e:
            print(f"Erro handler {self.addr}: {e}")
        finally:
            try: self.conn.close()
            except: pass
            print(f"[FIM] {self.addr}")

if __name__ == "__main__":
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(8)
    print(f"--- SERVER ON {PORT} ---")
    
    try:
        while True:
            conn, addr = server.accept()
            try:
                conn_ssl = context.wrap_socket(conn, server_side=True)
                ClientHandler(conn_ssl, addr).start()
            except ssl.SSLError:
                conn.close()
    except KeyboardInterrupt:
        server.close()