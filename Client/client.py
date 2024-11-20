import socket
import sys
import threading

rendezvous = ('192.168.0.3', 55555)

# connect to rendezvous
print('connecting to rendezvous server')

sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock1.bind(('0.0.0.0', 50001))
sock1.sendto(b'0', rendezvous)

while True:
    data = sock1.recv(1024).decode()

    if data.strip() == 'ready':
        print('checked in with server, waiting')
        break
    
data = sock1.recv(1024).decode()
ip, sport, dport = data.split(' ')
sport = int(sport)
dport = int(dport)

print('\ngot peer')
print(f'ip: {ip}')
print(f'source port: {sport}')
print(f'destination port: {dport}\n')


# punch hole
# equivalent: echo 'punch hole' | nc -u -p 50001 x.x.x.x 50002
print('punching hole')

sock1.close()
sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock2.bind(('0.0.0.0', sport))
sock2.sendto(b'0', (ip, dport))

print('ready to exchange messages\n')

# listen for
# equivalent: nc -u -l 50001
def listen():
    sock2.close()
    sock3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock3.bind(('0.0.0.0', sport))

    while True:
        data = sock3.recv(1024)
        print('\rpeer: {}\n'.format(data.decode()), end='')

listener = threading.Thread(target=listen, daemon=True)
listener.start()

# send messages
# equivalent: echo 'xxx' | nc -u -p 50002 x.x.x.x 50001
sock4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock4.bind(('0.0.0.0', dport))

while True:
    msg = input('> ')
    if (msg == "quit"):
        print("quitting")
        sock4.close()
        break
    sock4.sendto(msg.encode(), (ip, sport))