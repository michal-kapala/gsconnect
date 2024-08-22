import socket, sys, os
# relative module import stuff
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_dir)
import gsm, pkc, tcp

SERVER_ADDRESS = ('localhost', 7777)

CLIENTS: list[tcp.TcpClient] = []
"""Global list of connected game clients."""

def handle_req(client: tcp.TcpClient, req: gsm.Message):
  """Handler for `gsm.Message` requests."""
  res = None
  match req.header.type:
    case gsm.MESSAGE_TYPE.STILLALIVE:
      pass
    case gsm.MESSAGE_TYPE.LOGIN:
      pass
    case gsm.MESSAGE_TYPE.KEY_EXCHANGE:
      match req.dl.lst[0]:
        case '1':
          client.game_pubkey = pkc.RsaPublicKey.from_buf(req.dl.lst[1][2]).to_pubkey()
          # keygen
          pub_key, priv_key = pkc.keygen()
          client.sv_pubkey = pub_key
          client.sv_privkey = priv_key
          res = gsm.KeyExchangeResponse(req, client)
        case '2':
          enc_bf_key = bytes(req.dl.lst[1][2])
          bf_key = pkc.decrypt(enc_bf_key, client.sv_privkey)
          client.game_bf_key = bf_key
          res = gsm.KeyExchangeResponse(req, client)
        case _:
          raise BufferError(f'Unknown reqId ({req.dl[0]}) for a {req.header.type.name} message.')
    case _:
      raise NotImplementedError(f"No request handler for {req.header.type.name} messages.")
  return res

def start_server():
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  print(f"Router service is listening on port {SERVER_ADDRESS[1]}")
  sock.bind(SERVER_ADDRESS)
  sock.listen(5)
    
  while True:
    client = tcp.TcpClient(sock.accept())
    CLIENTS.append(client)
    print(f"Connection from {client.addr}")
    try:
      while True:
        data = client.conn.recv(4096)
        if data:
          req = gsm.Message(data, client.sv_bf_key)
          print(req)
          res = handle_req(client, req)
          if res:
            print(res)
            client.conn.sendall(bytes(res))
          elif req.header.type != gsm.MESSAGE_TYPE.STILLALIVE:
            client.conn.sendall(data)
        else:
          print("No more data from", client.addr)
          break
    finally:
      client.conn.close()
      CLIENTS.remove(client)

if __name__ == "__main__":
    start_server()
