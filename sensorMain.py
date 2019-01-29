#

from __future__ import print_function
import time
from RF24 import *
import RPi.GPIO as GPIO
import Tkinter as tk
from Tkinter import *
import struct
import threading
from datetime import datetime
import sys

label_map = {} #Hierin worden de aangemaakte labels opgeslagen in een map (key:value)
node = 1 #Globale variabele voor laatst binnengekomen zender node nummer
sensor_value = 0 #Gloabele variabel voor laatst binnengekomen zender waarde van sensor
alarm_value = 1000 #Variabele voor bepalen van te hoge waarde van sensor
file_name = str(datetime.now().time()) #bestandsnaam, indien geen naam gekozen, dan naam is tijd van moment van beginnen met luisteren


#Schrijft data van sensoren naar een text-file
def write_date_to_file(node,value): 
    
    global file_name
    
    f = open(file_name + ".txt", "a")
    time = str(datetime.now().time()) #tijd op moment van schrijven
    time = time[: -3]
    f.write(time + "\t")
    
    for x in range(0, node): #schrijft tabs in text-file zodat het bij de juiste sensor komt te staan
        f.write("\t")
        
    f.write(str(value) + "\n") #schrijft de waarde van de sensor in tekst-bestand
    f.close()
    

#Functie die radio code bevat, wordt met de button gestart op een aparte thread
def receive_payload():
    payload = np.uint32(1000)
    radio = RF24(RPI_BPLUS_GPIO_J8_15, RPI_BPLUS_GPIO_J8_24, BCM2835_SPI_SPEED_8MHZ) #Maakt radio object, parameters afhankelijk van aansluiting op RPi 
    pipes = [0xE6] #Hexidecimale addressen waarop radio kan ontvangen
    
    #Initialiseert de radio en begint met luisteren
    radio.begin()
    
    radio.setAutoAck(False)
    radio.setRetries(5,15)
    radio.setChannel(80);
    radio.setDataRate(RF24_1MBPS)
    radio.setCRCLength(RF24_CRC_16)
    
    #radio.enableDynamicPayloads();
    radio.payloadsize = 16
    radio.openReadingPipe(1, pipes[0])
    radio.startListening()
    print("Radio listening")
    
    #Radio blijft continue  
    while True:  
        while not radio.available(): #als geen data beschikbaar is van zenders, dan korte sleep
            time.sleep(1/100)
        print("Received");
        receive_payload = radio.read(radio.payloadsize) #leest beschikbare data
        for x in receive_payload:
            print(x)
            
##        #Ontvangen data is in bytes, eerst string, dan unpacked als 2 integers
        string_payload = ''.join(chr(c) for c in receive_payload)
       
        unpacked_payload = struct.unpack("ll", string_payload)
       
       
        global node
        global sensor_value
##        
##        #data wordt gegeven aan globale variabelen, node en value
        node = int(unpacked_payload[0])
        sensor_value = int(unpacked_payload[1])
##        
        write_date_to_file(node,sensor_value)
##        
##
###Class voor interface
class GUI:
    
    def setup_file(self): #Maakt text-file voor schrijven van data
        
        global file_name
        
        if(len(self.file_entry.get()) != 0):
            file_name = self.file_entry.get()
        
        f = open(file_name + ".txt", "w")
        f.write("Time\t\t\t")
        
        for x in range (1, int(self.nodes_entry.get()) + 1): #Maakt kop voor elke node 
            f.write("Node" + " " + str(x))
            f.write("\t")
        
        f.write("\n")
        f.close()
        
        
    def update_labels(self): #Update de aangemaakte labels 
        
        font_colour = "green"
        global node
        global sensor_value
        
        if(sensor_value > alarm_value): 
            font_colour = "red"
        
        label_map[node].config(text = sensor_value, fg = font_colour) #update de tekst van de label en de kleur
        root.after(100, self.update_labels) #Functie roept zichzelf weer aan, tijd kan aangepast worden
        
        
    def create_labels(self): #Maakt de labels voor nodes en slaat dit op in de label_map(key:value)
        
            nodes = int(self.nodes_entry.get())
            self.setup_file()
            
            if(len(self.alarm_entry.get()) != 0):
                global alarm_value
                alarm_value = int(self.alarm_entry.get())
            
            for x in range(1, nodes + 1):
                Label(root, text = "Node " + str(x) + ":", font = "Helvetica 12 bold").grid(row = 4+x, column = 0,pady = 3)
                label_map[x] = Label(root, font = "Helvetica 12", text = "0")
                label_map[x].grid(row = 4+x, column = 1,pady = 3)
            
            self.update_labels()
            
            
    def quit_handler(self): #Stopt alle processen en interface
        
        root.destroy()
        sys.exit(0)
        print("Process killed")

    
    def __init__(self,master): #Initialisatie van interface
        
        self.t = threading.Thread(target = receive_payload) #Nieuwe thread voor radio code
        self.t.setDaemon = True #Daemon thread stopt wanneer hoofdprocessen stoppen
        
        Label(master, text = "Amount of Nodes:").grid(row = 0, sticky = W, pady = 10)
        self.nodes_entry = Entry(master)
        self.nodes_entry.grid(row = 0, column = 1, pady = 10)
        
        Label(master, text = "Warning value:").grid(row = 1, sticky = W, pady = 10)
        self.alarm_entry = Entry(master)
        self.alarm_entry.grid(row = 1, column = 1, pady = 10)

        Label(master, text = " File name:").grid(row = 2, sticky = W, pady = 10)
        self.file_entry = Entry(master)
        self.file_entry.grid(row = 2, column = 1, pady = 10)

        generate_nodes_button= tk.Button(master,
                            text = "Generate Nodes",
                            fg = "black",
                            command = self.create_labels)
        generate_nodes_button.grid(row = 3, column = 0, pady = 10, sticky = W + E)


        start_radio_button= tk.Button(master,
                           text ="Start Radio",
                           fg ="black",
                           command = self.t.start)
        start_radio_button.grid(row = 3, column = 1, pady = 10, sticky = W + E)
        
        quit_button = tk.Button(master,
                             text = "Quit",
                             fg = "black",
                             command = self.quit_handler)
        quit_button.grid(row = 3, column =  2, pady = 10, sticky = W + E)
        
        Label(master, font = "Helvetica 18 bold", text = "Sensoren:").grid(row = 4, column = 0, pady = 10)
        
    
root = tk.Tk()
root.title("Sensor interface")
gui = GUI(root)
root.mainloop() #Begint mainloop van interface
