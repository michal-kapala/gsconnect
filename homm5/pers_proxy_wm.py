import socket, sys, os
# relative module import stuff
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_dir)
import gsm, pkc, client, h5

SERVER_ADDRESS = h5.ENDPOINTS["pers_proxy_wm"]
"""Address of the proxy's wait module service."""

CLIENTS: list[client.TcpClient] = []
"""Global list of connected game clients."""

def handle_req(clt: client.TcpClient, req: gsm.Message):
  """Handler for `gsm.Message` requests."""
  res = None
  match req.header.type:
    case gsm.MESSAGE_TYPE.STILLALIVE:
      pass
    case gsm.MESSAGE_TYPE.LOGINWAITMODULE:
      clt.username = req.dl.lst[0]
      res = gsm.ProxyLoginWaitModuleResponse(req)
    case gsm.MESSAGE_TYPE.KEY_EXCHANGE:
      match req.dl.lst[0]:
        case '1':
          clt.game_pubkey = pkc.RsaPublicKey.from_buf(req.dl.lst[1][2]).to_pubkey()
          # keygen
          pub_key, priv_key = pkc.keygen()
          clt.sv_pubkey = pub_key
          clt.sv_privkey = priv_key
          res = gsm.KeyExchangeResponse(req, clt)
        case '2':
          enc_bf_key = bytes(req.dl.lst[1][2])
          bf_key = pkc.decrypt(enc_bf_key, clt.sv_privkey)
          clt.game_bf_key = bf_key
          res = gsm.KeyExchangeResponse(req, clt)
        case _:
          raise BufferError(f'Unknown reqId ({req.dl[0]}) for a {req.header.type.name} message.')
    case _:
      raise NotImplementedError(f"No request handler for {req.header.type.name} messages.")
  return res

def start_server():
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  print(f"Proxy's wait module is listening on port {SERVER_ADDRESS[1]}")
  sock.bind(SERVER_ADDRESS)
  sock.listen(5)
    
  while True:
    clt = client.TcpClient(sock.accept())
    CLIENTS.append(clt)
    print(f"Connection from {clt.addr}")
    try:
      while True:
        data = clt.conn.recv(4096)
        if data:
          req = gsm.Message(data, clt.sv_bf_key)
          if req.header.size < len(data):
            bundle = gsm.GSMessageBundle(req, data[req.header.size:], clt)
            print(bundle)
            for msg in bundle.msgs:
              print(msg)
              res = handle_req(clt, msg)
              if res:
                print(res)
                clt.conn.sendall(bytes(res))
              elif req.header.type != gsm.MESSAGE_TYPE.STILLALIVE:
                clt.conn.sendall(data)
          else:
            print(req)
            res = handle_req(clt, req)
            if res:
              print(res)
              clt.conn.sendall(bytes(res))
            elif req.header.type != gsm.MESSAGE_TYPE.STILLALIVE:
              clt.conn.sendall(data)
        else:
          print("No more data from", clt.addr)
          break
    finally:
      clt.conn.close()
      CLIENTS.remove(clt)

if __name__ == "__main__":
    start_server()
