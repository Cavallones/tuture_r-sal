import socket
import sys
import traceback
from threading import Thread
from struct import pack
from struct import unpack
from struct import calcsize as sizeof
import json
import random

CONNECT_TO_CAR = 1
MOVE_CAR = 2
GET_MALUS = 3
SEND_MALUS = 4

#Les ips de tous les participants
IP_ANTOINE = "192.168.1.100"
IP_ENZO = "192.168.1.101"
IP_SOSOS = "192.168.1.102"
IP_THIERNO = "192.168.1.103"
IP_PAUL = "192.168.1.104"
IP_THEO = "192.168.1.105"
IP_MAX = "192.168.1.106"
IP_AMINE = "192.168.1.107"
IP_JEROME = "192.168.1.108"

ip_gens = [IP_PAUL, IP_ENZO, IP_MAX, IP_SOSOS, IP_THEO, IP_THIERNO, IP_JEROME, IP_AMINE, IP_ANTOINE]

#Un dictionnaire en variable globale qui nous permettra d'attaquer les joueurs avec les malus, il contiendra en tant que clé des adresses IP
#et en tant que valeur, la socket liée à ladite IP, on le remplira à chaque nouvelle connexion
ip_et_co = {}

def process_packet(packet):
    return unpack("!I{}s".format(len(packet)-sizeof("!I")), packet)

def create_packet(op_code, data):
    return pack("!I{}s".format(len(data)), op_code, data.encode())

def main():
    start_server()


def start_server():
    #Valeurs choisies de manière totalement arbitraire
    host = "192.168.0.4"
    port = 15555

    ecoute_telecommande = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ecoute_telecommande.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("Socket created")

    try:
        ecoute_telecommande.bind(('', port))
    except:
        print("Bind failed. Error : " + str(sys.exc_info()))
        sys.exit()

    #Ici, il faut autoriser au maximum 9 connexions pour 9 joueurs en même temps
    ecoute_telecommande.listen(9)
    print("Socket now listening")

    while True:
        connection, address = ecoute_telecommande.accept()
        ip, port = str(address[0]), str(address[1])
        #Feedback pour savoir qui est connecté
        print("Connected with " + ip + ":" + port)

        #Pour chaque nouvelle connexion, on créé une nouvelle Thread qui gèrera le client
        try:
            Thread(target=client_thread, args=(connection, ip, port)).start()
        except:
            print("Thread did not start.")
            traceback.print_exc()

    ecoute_telecommande.close()


def client_thread(connection, ip, port, max_buffer_size = 5120):
    is_active = True

    while is_active:
        #Quand le client arrive, on récupère le packet et les données qu'il a envoyés au serveur
        code, data = receive_input(connection, max_buffer_size)
        donnees = json.loads(data)

        #Normalement, grâce au code de la télécommande, nous savons que CONNECT_TO_CAR ne sera envoyé qu'un fois par la télécommande, au tout début
        if code == CONNECT_TO_CAR :
            #On ouvre donc une connection avec la voiture ciblée sur l'IP et le port qui ont été fournis
            parle_voiture = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            parle_voiture.connect(donnees["ip"], donnees["port"])
            #On enregistre la socket dans notre dictionnaire global
            global ip_et_co
            ip_et_co[donnees["ip"]] = parle_voiture
            #Et on créé un tableau en retirant notre voiture du tableau ip_gens : on ne veut pas pouvoir s'envoyer de malus à nous même !
            nouveaux_ips = ip_gens.remove(donnees[0])
        #Si le client souhaite se déconnecter, on met fin à la thread
        elif code == MOVE_CAR :
            if "t" in data:
                print("Client is requesting to quit")
                connection.close()
                print("Connection " + ip + ":" + port + " closed")
                is_active = False
            #Sinon, on envoie à la voiture le paquet qu'on a reçu
            else:
                to_send = create_packet(MOVE_CAR, data)
                connection.sendall(to_send)
        #Si le joueur demande à envoyer un malus à un autre joueur
        elif code == SEND_MALUS :
            #On choisit l'ip de la cible
            a_malusser = random.randint(0, 8)
            joueur_cible = nouveaux_ips[a_malusser]
            #Et on envoie à sa voiture le paquet correspondant
            pack_malus = create_packet(SEND_MALUS, "")
            global ip_et_co
            ip_et_co[joueur_cible].sendall(pack_malus)

        #Pour savoir si un joueur a le droit d'envoyer des malus, on décide ça au hasard, ici les probabilités sont assez faibles
        #Mais comme nous sommes dans une boucle infinie, ça devrait aller
        test = random.randint(1000)
        if test < 5 :
            create_malus = create_packet(GET_MALUS, "")
            connection.sendall(create_malus)


#Fonction pour recevoir les données
def receive_input(connection, max_buffer_size):
    client_input = connection.recv(max_buffer_size)

    packet_recu = process_packet(client_input)

    client_input_size = sys.getsizeof(client_input)

    if client_input_size > max_buffer_size:
        print("The input size is greater than expected {}".format(client_input_size))

    return packet_recu

if __name__ == "__main__":
    main()
