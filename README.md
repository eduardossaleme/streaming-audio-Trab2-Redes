# Sistema de Streaming de Áudio Seguro via Sockets

## Descrição
Este projeto implementa um sistema de streaming de áudio cliente-servidor utilizando sockets TCP em Python. O diferencial do projeto é a implementação de uma camada de segurança SSL/TLS para criptografar a transmissão, além da capacidade de realizar streaming tanto de arquivos de áudio (`.wav`) quanto de áudio ao vivo (captura de microfone).

Os principais desafios abordados incluem a sincronização de áudio em tempo real, controle de fluxo (buffering), programação concorrente (threads para áudio e interface gráfica) e implementação de protocolos de segurança.

## Tecnologias Utilizadas
* **Linguagem:** Python 3
* **Bibliotecas Principais:**
    * `socket`: Comunicação de rede via TCP.
    * `ssl`: Criptografia e segurança da conexão.
    * `threading`: Execução paralela de áudio e interface.
    * `tkinter`: Interface Gráfica do Usuário (GUI).
    * `pyaudio`: Captura e reprodução de áudio (Requer instalação).
    * `wave`: Manipulação de arquivos de áudio.

## Como Executar

### Requisitos
* Python 3.x instalado.
* Microfone (para servidor) e Alto-falantes (para cliente).
* **Dependências:**
    * `pyaudio`

### Instruções de Execução

**1. Clone o repositório:**
```bash
git clone https://github.com/eduardossaleme/streaming-audio-Trab2-Redes.git
cd streaming-audio-Trab2-Redes.
```
**2. Instalar as dependências:**
```bash
pip install pyaudio
```
Notas paras usuários Linux: 
Se houver erro, instale antes: sudo apt-get install portaudio19-dev  ou tente sudo apt-get install python3-pyaudio <br>
Talvez também seja necessário instalar o Tkinter: sudo apt-get install python3-tk

**3. Configuração do Ambiente (Arquivos Obrigatórios):**
Para que o servidor funcione corretamente, você deve criar os seguintes arquivos na mesma pasta onde estão os scripts `server.py` e `client.py`:

* **`users.json`** (Controle de acesso):
    Crie um arquivo com este nome contendo os usuários e senhas permitidos.
    ```json
    {
        "usuarios": {
            "admin": "admin123",
            "convidado": "12345"
        }
    }
    ```

* **`musicas.json`** (Lista de arquivos disponíveis):
    Crie um arquivo com este nome listando os arquivos de áudio que estarão disponíveis para streaming.
    ```json
    {
        "musicas": [
            "musica1.wav",
            "teste_audio.wav"
        ]
    }
    ```

* **Certificados SSL:**
    Certifique-se de que os arquivos `cert.pem` (certificado público) e `key.pem` (chave privada) estejam na pasta raiz do projeto.
    *(Estes arquivos são necessários para a criptografia SSL funcionar)*.

* **Arquivos de Áudio:**
    Coloque os arquivos `.wav` correspondentes aos nomes listados em `musicas.json` na mesma pasta.

**4. Execute o servidor:**
Abra o terminal e execute:
```bash
python server.py
```

**5. Execute o cliente:**
Em outro terminal (ou outra máquina), execute:
```bash
python client.py
```
## Como Testar

1.  **Iniciar Servidor:** Execute o `server.py`.
2.  **Iniciar Cliente:** Execute o `client.py`. A janela de login "Login SSL" será aberta.
3.  **Login:** Insira um usuário e senha que você cadastrou previamente no arquivo e clique em "Entrar".
4.  **Seleção de Mídia:** Após a autenticação bem-sucedida, uma nova janela listará as opções disponíveis:
    * Escolha **"🔴 TRANSMISSAO AO VIVO"** para ouvir o microfone do servidor em tempo real.
    * Ou escolha um nome de arquivo `.wav` da lista para ouvir a música gravada.
5.  **Controles do Player:** A interface principal do player abrirá com os seguintes controles:
    * **▶ PLAY / ⏸ PAUSE:** Alternam o estado de reprodução do áudio.
    * **🔙 Trocar Transmissão:** Envia o comando de parada, fecha a conexão atual e retorna ao menu de seleção para escolher outra faixa.
    * **⏹ Sair:** Encerra a aplicação completamente.

## Funcionalidades Implementadas

* [x] **Segurança SSL/TLS:** Toda a comunicação (autenticação e dados de áudio) é criptografada utilizando a biblioteca `ssl`, garantindo privacidade na rede local.
* [x] **Autenticação:** Sistema de login que valida as credenciais enviadas pelo cliente comparando-as com o arquivo `users.json` no servidor.
* [x] **Streaming Híbrido:**
    * **Arquivos:** Leitura de arquivos `.wav` com controle de tempo (frames) para garantir a velocidade de reprodução correta.
    * **Live:** Captura direta do microfone via `PyAudio` e envio imediato dos pacotes para o cliente.
* [x] **Interface Gráfica (GUI):** Interface completa com `Tkinter`, gerenciando janelas de login, seleção de música e o player com feedback visual de status.
* [x] **Multithreading:** Utilização de threads (`threading.Thread`) tanto no servidor (para atender múltiplos clientes) quanto no cliente (para reproduzir áudio sem travar a interface gráfica).

## Possíveis Melhorias Futuras

* **Verificação de Certificado:** Alterar a configuração do cliente para verificar o hostname e a validade do certificado (`check_hostname = True`), aumentando a segurança para produção.
* **Buffer :** Criar um buffer dinâmico no cliente para armazenar alguns segundos de áudio antes de tocar, prevenindo falhas causadas por instabilidade na rede.
