# coding: utf-8

from pynput.keyboard import Key, Listener
import time
import socket
from struct import pack
from struct import unpack
from struct import calcsize as sizeof
import json
from threading import Thread

#Les différentes actions que le serveur reçoit, envoyées par la télécommande
CONNECT_TO_CAR = 1
MOVE_CAR = 2
GET_MALUS = 3
SEND_MALUS = 4

#Ceux sont ceux du serveur qui a été utilisé pour la course, à modifier bien sur
hote = "192.168.1.1"
port = 1337

def process_packet(packet):
    return unpack("!I{}s".format(len(packet)-sizeof("!I")), packet)

def create_packet(op_code, data):
    return pack("!I{}s".format(len(data)), op_code, data.encode())

got_malus = False

parler_serveur_principal = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
parler_serveur_principal.connect((hote, port))
#Feedback pour l'utilisateur
print "Connection on {}".format(port)

#On envoie un packet au serveur pour lui dire que nous souhaitons connecter notre voiture ayant l'ip donnée et qu'elle écoutera sur le port donné
init = create_packet(CONNECT_TO_CAR, json.dumps({'ip':'192.168.1.104', 'port':9999}))
parler_serveur_principal.sendall(init)

#Il faut également que l'on écoute le serveur principal pour savoir si on peut envoyer des malus on non
ecouter_serveur_principal = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ecouter_serveur_principal.bind(('', 8887))

ecouter_serveur_principal.listen(1)

client_actif = True

#Utilisation de pynput.keyboard pour savoir si les touches sont pressées ou relâchées
def on_press(event) :
	evt = str(event)
	#Si on veut se déconnecter
	if evt == "t" :
		test = False
		print "Deconnexion"
		sentpacket = create_packet(MOVE_CAR, evt)
		parler_serveur_principal.sendall(sentpacket)
		parler_serveur_principal.close()
	#Envoyer un packet malus au serveur si on en a la possibilité et si on appuye sur m, à noter que dans notre configuration, on ne peut
	#Envoyer qu'un seul malus et pas les stocker (en avoir plusieurs d'un coup à envoyer)
	elif evt == "m" and got_malus == True:
		sentmalus = create_packet(SEND_MALUS, "")
		got_malus = False
 	else :
		sentpacket = create_packet(MOVE_CAR, evt)
		parler_serveur_principal.sendall(sentpacket)

def on_release(event) :
	evt = str(event)
	ccbb = "r" + evt
	parler_serveur_principal.sendall(str(ccbb))

with Listener(
	on_press = on_press,
	on_release = on_release) as listener :
	listener.join()

#On créé une thread qui surveillera le clavier toute seul pour pouvoir écouter en même temps le serveur principal
Thread(target=ecoute).start()

while client_actif :
	connection, address = ecouter_serveur_principal.accept()
	pack_recu = connection.recv(1024)
	if pack_recu != "" :
		code, data = process_packet(pack_recu)
		#Si le serveur nous envoie un packet nous autorisant à lancer un malus sur un adversaire, on prévient le client
		if code == GET_MALUS :
			got_malus = True
			print "Hoy ! Yah goat a maylus ta goyve moayte ! "


"""
A noter : dans notre configuration, ce n'est pas le jouer qui décide à qui envoyer un malus, mais le serveur qui choisira de manière aléatoire un adversaire à qui
Envoyer le malus. Il n'y a donc pas de touche pour décider à qui envoyer de malus, seulement une touche pour dire qu'on veut qu'un malus soit envoyé à quelqu'un
"""
