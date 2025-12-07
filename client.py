# client.py
import socket
import pyaudio
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
import ssl

SERVER_IP = "127.0.0.1"
SERVER_PORT = 6795
CHUNK = 4096

SAVED_USER = ""
SAVED_PASS = ""

context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

client = None
socket_lock = threading.Lock()

executando = True
tocando = True

def criar_socket_seguro():
    global client
    raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client = context.wrap_socket(raw, server_hostname=SERVER_IP)

criar_socket_seguro()

def recv_line(sock, timeout=None):
    buf = b""
    sock.settimeout(timeout)
    try:
        while True:
            c = sock.recv(1)
            if not c: return None
            if c == b"\n": break
            buf += c
    except: return None
    finally: sock.settimeout(None)
    return buf.decode().strip()

def recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        try:
            pkt = sock.recv(n - len(buf))
            if not pkt: return buf
            buf += pkt
        except: return buf
    return buf


def player_thread(sock, stream, bytes_pkt):
    global executando, tocando
    while executando:
        try:
            data = recv_exact(sock, bytes_pkt)
            if not data:
                executando = False
                break
            
            if tocando:
                stream.write(data)
            else:
                pass
        except: break

    try:
        stream.stop_stream()
        stream.close()
    except: pass
    
    if executando: 
        cmd_stop()

def cmd_play():
    global tocando
    tocando = True
    try:
        status_label.config(text="🟢 Reproduzindo")
        with socket_lock: client.sendall(b"PLAY\n")
    except: pass

def cmd_pause():
    global tocando
    tocando = False
    try:
        status_label.config(text="🟡 Pausado")
        with socket_lock: client.sendall(b"PAUSE\n")
    except: pass

def cmd_stop():
    global executando
    executando = False
    try:
        status_label.config(text="🔴 Encerrando...")
        with socket_lock: client.sendall(b"STOP\n")
    except: pass
    try: client.close()
    except: pass
    root.after(500, root.destroy)

def cmd_trocar():
    global executando

    executando = False
    
    try: status_label.config(text="🔄 Trocando...")
    except: pass
    
    try:
        with socket_lock: client.sendall(b"STOP\n")
    except: pass
    
    try: client.close()
    except: pass

    root.destroy()
    
    reconectar_e_escolher()

def reconectar_e_escolher():
    global client
    time.sleep(0.2)
    
    criar_socket_seguro()
    try:
        client.connect((SERVER_IP, SERVER_PORT))
        client.sendall(f"AUTH {SAVED_USER} {SAVED_PASS}\n".encode())
        
        resp = recv_line(client, timeout=5)
        
        if resp != "AUTH_OK":
            messagebox.showerror("Erro", "Falha na reautenticação automática.")
            return
            
        lista = recv_line(client, timeout=5)
        if not lista: return
        musicas = lista.split(",") if lista else []
        abrir_seletor_musicas(musicas)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro na reconexão: {e}")

def fazer_login():
    global SAVED_USER, SAVED_PASS
    login = entry_user.get().strip()
    senha = entry_pass.get().strip()
    if not login or not senha: return
        
    SAVED_USER = login
    SAVED_PASS = senha
    
    try:
        client.connect((SERVER_IP, SERVER_PORT))
        client.sendall(f"AUTH {login} {senha}\n".encode())
        resp = recv_line(client, timeout=5)
        if resp != "AUTH_OK":
            messagebox.showerror("Erro", "Login/Senha incorretos")
            client.close()
            criar_socket_seguro()
            return
        
        lista = recv_line(client, timeout=5)
        musicas = lista.split(",") if lista else []
        abrir_seletor_musicas(musicas)
    except Exception as e:
        messagebox.showerror("Erro", f"Login: {e}")
        criar_socket_seguro()

def abrir_seletor_musicas(musicas):
    try: login_window.destroy()
    except: pass

    sel = tk.Tk()
    sel.title("Seleção")
    sel.geometry("350x250")
    
    tk.Label(sel, text=f"Usuário: {SAVED_USER}", font=("Arial", 10)).pack(pady=2)
    tk.Label(sel, text="Escolha a transmissão:", font=("Arial", 12, "bold")).pack(pady=5)
    
    music_var = tk.StringVar(value=musicas[0] if musicas else "")
    combo = ttk.Combobox(sel, textvariable=music_var, values=musicas, state="readonly", width=40)
    combo.pack(pady=8)
    
    def confirmar():
        escolha = music_var.get().strip()
        if not escolha: return
        try:
            client.sendall((escolha + "\n").encode())
            resp = recv_line(client, timeout=5)
            if resp != "OK":
                messagebox.showerror("Erro", "Opção inválida")
                client.close()
                sel.destroy()
                return
            sel.destroy()
            abrir_interface()
        except:
            client.close()
            sel.destroy()
            
    tk.Button(sel, text="Confirmar", command=confirmar, width=20, bg="#4CAF50", fg="white").pack(pady=12)
    sel.mainloop()

def abrir_interface():
    global root, status_label, executando
    root = tk.Tk()
    root.title("Cliente SSL Player")
    root.geometry("360x350")
    
    tk.Label(root, text="🎧 Player", font=("Arial", 16, "bold")).pack(pady=10)
    status_label = tk.Label(root, text="Conectado", font=("Arial", 12))
    status_label.pack(pady=6)

    meta = recv_line(client, timeout=5)
    if not meta:
        root.destroy()
        return
    try:
        channels, sampwidth, rate = map(int, meta.split(","))
    except:
        root.destroy()
        return

    bytes_pkt = CHUNK * channels * sampwidth
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pa.get_format_from_width(sampwidth),
                     channels=channels, rate=rate, output=True, frames_per_buffer=CHUNK)

    executando = True
    threading.Thread(target=player_thread, args=(client, stream, bytes_pkt), daemon=True).start()

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=15)
    tk.Button(btn_frame, text="▶ PLAY", width=12, bg="#4CAF50", command=cmd_play).grid(row=0, column=0, padx=5)
    tk.Button(btn_frame, text="⏸ PAUSE", width=12, bg="#FFC107", command=cmd_pause).grid(row=0, column=1, padx=5)
    tk.Button(root, text="🔙 Trocar Transmissão", width=28, bg="#2196F3", fg="white", command=cmd_trocar).pack(pady=5)
    tk.Button(root, text="⏹ Sair", width=28, bg="#F44336", fg="white", command=cmd_stop).pack(pady=5)

    root.protocol("WM_DELETE_WINDOW", cmd_stop)
    root.mainloop()

login_window = tk.Tk()
login_window.title("Login SSL")
login_window.geometry("300x200")
tk.Label(login_window, text="Login:").pack(pady=5)
entry_user = tk.Entry(login_window); entry_user.pack()
tk.Label(login_window, text="Senha:").pack(pady=5)
entry_pass = tk.Entry(login_window, show="*"); entry_pass.pack()
tk.Button(login_window, text="Entrar", command=fazer_login, width=15).pack(pady=15)

try: login_window.mainloop()
except: pass