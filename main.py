import socketio
import time
import RPi.GPIO as GPIO
import board
import adafruit_dht
import asyncio
import json
import threading
import requests

#DHT sensor pin GPIO4
sensor = adafruit_dht.DHT11(board.D4)


sio = socketio.Client()
GPIO.setmode(GPIO.BCM)
    
#GPIO pins of nodes
drip_motor_relay_pin=6
fog_motor_relay_pin=10
cooler_pad_motor_relay_pin=20
valve_relay_pin=30

drip_motor_push_button_pin=17
fog_motor_push_button_pin=17
cooler_pad_motor_push_button_pin=17
valve_push_button_pin=17
    
#sensor initalising code has to be updated 
#nodes pin config setup
GPIO.setup(drip_motor_relay_pin,GPIO.OUT,initial=GPIO.LOW)  #relay pin
GPIO.setup(fog_motor_relay_pin,GPIO.OUT,initial=GPIO.LOW)  #relay pin
GPIO.setup(cooler_pad_motor_relay_pin,GPIO.OUT,initial=GPIO.LOW)  #relay pin
GPIO.setup(valve_relay_pin,GPIO.OUT,initial=GPIO.LOW)  #relay pin

GPIO.setup(drip_motor_push_button_pin, GPIO.IN,pull_up_down=GPIO.PUD_DOWN) #push button pin
GPIO.setup(fog_motor_push_button_pin, GPIO.IN,pull_up_down=GPIO.PUD_DOWN) #push button pin
GPIO.setup(cooler_pad_motor_push_button_pin, GPIO.IN,pull_up_down=GPIO.PUD_DOWN) #push button pin
GPIO.setup(valve_push_button_pin, GPIO.IN,pull_up_down=GPIO.PUD_DOWN) #push button pin

#nodes initial state
drip_motor_state=False
fog_motor_state=False
cooler_pad_motor_state=False
valve_state=False

server_disconnect_state=False
server_disconnect_threshold_time=10
push_button_debounce_time=500
    

async def DHT11_sensor():
    while True:
        temp_c = sensor.temperature
        temp_f = temp_c * (9 / 5) + 32
        humidity = sensor.humidity
        print(f"temp={temp_c}*c humidity={humidity}")
        await asyncio.sleep(2)

def handle_server_disconnect():

	global drip_motor_state,fog_motor_state,cooler_pad_motor_state,valve_state
	time.sleep(server_disconnect_threshold_time)
	
	if(server_disconnect_state):
		GPIO.output(drip_motor_relay_pin,GPIO.LOW)
		GPIO.output(fog_motor_relay_pin,GPIO.LOW)
		GPIO.output(cooler_pad_motor_relay_pin,GPIO.LOW)
		GPIO.output(valve_relay_pin,GPIO.LOW)
		
		drip_motor_state=False
		fog_motor_state=False
		cooler_pad_motor_state=False
		valve_state=False
		                
def node_handler(state,pin):
    if state:
        GPIO.output(pin,GPIO.HIGH)
    else:
        GPIO.output(pin,GPIO.LOW)

def node_button_handler(node_name,pin):
    print("btn handler called")
    
    global drip_motor_state,fog_motor_state,cooler_pad_motor_state,valve_state
    if node_name == "dripmotor":
    	drip_motor_state = not drip_motor_state
    	node_handler(drip_motor_state,pin)
    	sio.emit("dripmotor",{"state":drip_motor_state})
    elif node_name == "fogmotor":
    	fog_motor_state = not fog_motor_state
    	node_handler(fog_motor_state,pin)
    	sio.emit("fogmotor",{"state":fog_motor_state})
    elif node_name == "coolerpad-motor":
    	cooler_pad_motor_state = not cooler_pad_motor_state
    	node_handler(cooler_pad_motor_state,pin)
    	sio.emit("coolerpad-motor",{"state":cooler_pad_motor_state})
    else:
    	valve_state = not valve_state
    	node_handler(valve_state,pin)
    	sio.emit("valve",{"state":valve_state})
    	
   
    

@sio.event
def connect():
    	global server_disconnect_state     
    	server_disconnect_state=False
    	print('connection established')
    	sio.emit("join-room",{"node_name":"device1"})
    	
@sio.event
def disconnect():
    	global server_disconnect_state
    	print("diconnected")
    	server_disconnect_state=True
    	thread=threading.Thread(target=handle_server_disconnect)
    	thread.start()
    	
@sio.on("joined-room")
def handle_room_joined():
	print("successfully joined to room")
    	
@sio.on("dripmotor")
def drip_motor_event_handler(data):
	print(data)
	global drip_motor_state,drip_motor_relay_pin
	drip_motor_state=data["state"]
	node_handler(drip_motor_state,drip_motor_relay_pin)
	sio.emit("dripmotor-ack",{"state":drip_motor_state})
    	
@sio.on("fogmotor")
def fog_motor_event_handler(data):
	print(data)
	global fog_motor_state,fog_motor_relay_pin
	fog_motor_state=data["state"]
	node_handler(fog_motor_state,fog_motor_relay_pin)
	sio.emit("fogmotor-ack",{"state":fog_motor_state})
    	
@sio.on("coolerpad-motor")
def cooler_pad_motor_event_handler(data):
	print(data)
	global cooler_pad_motor_state,cooler_pad_motor_relay_pin
	cooler_pad_motor_state=data["state"]
	node_handler(cooler_pad_motor_state,cooler_pad_motor_relay_pin)
	sio.emit("coolerpad-motor-ack",{"state":cooler_pad_motor_state})
    	
@sio.on("valve")
def valve_event_handler(data):
	print(data)
	global valve_state,valve_relay_pin
	valve_state=data["state"]
	node_handler(valve_state,valve_relay_pin)
	sio.emit("valve-ack",{"state":valve_state})
   
async def main():
    #task=asyncio.create_task(DHT11_sensor())
    #await task
    try:
    	#adding eventlistener for push button
    	 GPIO.add_event_detect(drip_motor_push_button_pin,GPIO.FALLING,callback=lambda channel: node_button_handler("dripmotor",drip_motor_relay_pin),bouncetime=push_button_debounce_time)
    	 
    	 GPIO.add_event_detect(fog_motor_push_button_pin,GPIO.FALLING,callback=lambda channel: node_button_handler("fogmotor",fog_motor_relay_pin),bouncetime=push_button_debounce_time)
    	 
    	 GPIO.add_event_detect(cooler_pad_motor_push_button_pin,GPIO.FALLING,callback=lambda channel: node_button_handler("coolerpad-motor",cooler_pad_relay_pin),bouncetime=push_button_debounce_time)
    	 
    	 GPIO.add_event_detect(valve_push_button_pin,GPIO.FALLING,callback=lambda channel: node_button_handler("valve",valve_relay_pin),bouncetime=push_button_debounce_time)
    	
    except Exception as e:
    	print("failed to add event listener")
    	print(e)
    
    	
    try:    	
    	sio.connect('http://192.168.41.85:8000')
    	print("connected to server")
    	sio.wait()
    except Exception as e:
    	print("failing to connect server")
    
if __name__ == "__main__":         
	asyncio.run(main())


        
