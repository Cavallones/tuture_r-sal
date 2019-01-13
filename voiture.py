# coding: utf-8

import RPi.GPIO as GPIO
import time
import sys
import socket
from struct import pack
from struct import unpack
from struct import calcsize as sizeof

#Une socket pour écouter les messages envoyés à la voiture par le serveur principal de notre application
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#Fonction commune à la promo pour pouvoir synchroniser nos différents serveurs principaux
def process_packet(packet) :
    return unpack("!I{}s".format(len(packet)-sizeof("!I")), packet)

#Le port sur lequel la voiture écoutera les messages du serveur principal, choisit arbitrairement
socket.bind(('', 9999))

#Pas besoin d'autoriser plus qu'une connexion entrante
socket.listen(1)

#Mise en place des roues, initialisation de la voiture
GPIO.setmode(GPIO.BOARD)
GPIO.setup(31,GPIO.OUT)
GPIO.setup(33,GPIO.OUT)
GPIO.setup(35,GPIO.OUT)
GPIO.setup(37,GPIO.OUT)

#Nous avons choisit d'initialiser ces actions différement dans le cas ou on jouerait avec un joystick
#et que l'inclinaison serait à prendre en compte, nous ne l'avons finalement pas fait. Nous initialisons tout de cette manière
#car nous avons remarqué qu'avec une fréquence élevée, même les actions avancer et reculer étaient plus rapides (moins de temps entre l'input et l'action, nous ne
#sommes pas certain de la raison cela dit)
avancer = GPIO.PWM(33, 1000)
reculer = GPIO.PWM(31, 1000)
tourner_gauche = GPIO.PWM(35, 1000)
tourner_droite = GPIO.PWM(37, 1000)

while True:
        #Accepter la connexion
        client, address = socket.accept()
        print "bienvenue" #Juste un feedback

        pack_recu = str(client.recv(255))
        code, texte = process_packet(pack_recu)
        #Nous utilisons ici la fonction str pour nous débarasser du u en python 2 qui se met devant les messages pour indiquer qu'ils sont en unicode
        evt = str(texte)

        #Si la voiture reçoit un code valant 4, alors c'est qu'elle vient de recevoir un malus, elle s'arrête donc pendant 1 seconde
        if code == 4 :
            GPIO.output(31,GPIO.LOW)
            GPIO.output(33, GPIO.LOW)
            tourner_gauche.start(0.0)
            tourner_droite.start(0.0)
            time.sleep(1)
        #Autrement, en fonction de l'input, elle fait différentes actions
        elif evt == "z" :
            GPIO.output(33, GPIO.HIGH)
        elif evt == "s" :
            GPIO.output(31,GPIO.HIGH)
        elif evt == "q'" :
            tourner_gauche.start(100.0)
        elif evt == "d" :
            tourner_droite.start(100.0)
        #Si le client choisit de terminer la connexion, on remet tous les moteurs à l'état initial et on "nettoie" avant de fermer la socket
        elif evt == "t" :
            GPIO.cleanup()
            client.close()
        elif evt == "rz" :
            GPIO.output(33, GPIO.LOW)
        elif evt == "rs" :
            GPIO.output(31,GPIO.LOW)
        elif evt == "rq" :
            tourner_gauche.start(0.0)
        elif evt == "rd" :
            tourner_droite.start(0.0)
