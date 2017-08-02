#USER

import socket
import sys
import signal
import os

tcs_name = socket.gethostbyname(socket.gethostname())
tcs_port = 58003

if ("-p" in sys.argv):
	tcs_port = int(sys.argv[sys.argv.index("-p") + 1])

if ("-n" in sys.argv):
	tcs_name = sys.argv[sys.argv.index("-n") + 1]

#UDP
sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock1.settimeout(5)
tcs_addr = (tcs_name, tcs_port)

#Global variables
var = ""
langNumber = 0
langs = ""
sbytes = 1024
utf = "utf-8"

#function that handles ctrl + c
def signal_handler(signal, frame):
	print("Bye")
	sock1.close()
	sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

#this function conects to TCS and return the languages available to translation
def list_command():
	msgList = "ULQ\n"
	i = 0
	sent = sock1.sendto(msgList.encode(utf), tcs_addr)
	try:
		data, server = sock1.recvfrom(sbytes)
		if(data.decode(utf) == "ULR EOF\n"):
			print("No Languages available")
			return(0,"")
		elif(data.decode(utf) == "ULR ERR\n"):
			print("list failed try again")
			return(0,"")
		elif(data.decode(utf).split()[0] == "ULR"):

			langNumber = int(data.split()[1])
			langs = data.decode(utf)
	
			while(i < langNumber):
				print(str(i + 1) + "- " + data.decode(utf).split()[i + 2])
				i = i+1
			return (langNumber, langs)
	except socket.timeout:
		print("The TCS doenst respond")
		return(0,"")

#this function conects to TCS and return the TRS adress to translate something
def tcs_connect(message):
	
	if(int(message[1]) <= langNumber):
		sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		msgRequest = "UNQ " + langs.split()[int(message[1]) + 1] + "\n"
		sent = sock1.sendto(msgRequest.encode(utf), tcs_addr)
		try:
			data, server = sock1.recvfrom(sbytes)
			data = data.decode(utf).split()
			if(data[0] == "UNR" and data[1] == "EOF"):
				print("Language not available")
				return None

			elif(data[0] == "UNR" and data[1] == "ERR"):
				print("Request invalid, try again!")
				return None

			elif(data[0].split()[0] == "UNR"):
				trs_addr = (data[1], int(data[2]))
				return trs_addr

		except socket.timeout:
			print("The TCS doesnt respond")
			return None
		
	print("Language not available")

#This function connects to TRS and receive the translation to the words requested
def request_command_t(message):

	message = message.split()

	sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock2.settimeout(5)

	trs_addr = tcs_connect(message)
	if(trs_addr != None):
		print(trs_addr[0] + " " + str(trs_addr[1]))
		translateN = len(message) - 3
	
		req = "TRQ t " + str(translateN)
		i = 3
		while(i < len(message)):
			req = req + " " + message[i]
			i += 1
	
		sock2.connect(trs_addr)
		req = req + "\n"
		sock2.send(req.encode(utf))
		try:
			data = sock2.recv(sbytes)
			data = data.decode('latin1').split()

			if(data[0] == "TRR" and data[1] == "NTA"):
				print("No translation available")
				sock2.close()

			elif(data[0] == "TRR" and data[1] == "ERR"):
				print("Invalid translation request, try again!")
				sock2.close()

			else:
				trs_resp = ""
				f = 3
				while(f < len(data)):

					trs_resp = trs_resp + " " + str(data[f])
					f += 1
				print(trs_addr[0] + ":" + trs_resp)

				sock2.close()
		except socket.timeout:
			print("TRS doesnt respond!")
			sock2.close()
	
#this function connects to the TRS and receive the translated file
def request_command_f(message):
	message = message.split()

	sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock2.settimeout(15)

	trs_addr = tcs_connect(message)
	if(trs_addr != None):
		try:
			
			filesize = int(os.stat(message[3]).st_size)
			req = "TRQ f " + message[3] + " " + str(filesize) + " "
			sock2.connect(trs_addr)
			sock2.send(req.encode(utf))
			f = open(message[3], 'rb')
			sended = 0
			while(sended < filesize):
				l = f.read(sbytes)
				sended += sbytes
				if(filesize - sended < 0):
					l += b'\n'
				sock2.send(l)	

			f.close()

			print(str(filesize) + " bytes to transmit")
		
			data = sock2.recv(128)
			data = data.split()
			
			if(data[0] == b'TRR' and data[1] == b'NTA'):
					print("No translation available")
					sock2.close()

			elif(data[0] == b'TRR' and data[1] == b'ERR'):
				print("Invalid translation request, try again!")
				sock2.close()

			else:
				
				f2 = open(data[2], 'wb')
				filesizeR = int(data[3])
				filename = str(data[2].decode(utf))
				
				data = data[4:]
				received = 0
				i = 0
				
				
				while(i < len(data)):
					f2.write(data[i])
					
					received += len(data[i])
					i += 1
				
				try:
					
					while(received < filesizeR):
						
						l2 = sock2.recv(128)
						received += len(l2)
						f2.write(l2)
						if(len(l2) == 0):
							break
										
						
					f2.seek(-1, os.SEEK_END)
					f2.truncate()
					f2.close()
					print("received file " + filename + " " + str(filesizeR) + " Bytes")
					sock2.close()
				except socket.timeout:
					print("TRS doesnt respond!")
					sock2.close()
		
		except FileNotFoundError:
			print("File not found, try again!")

#main program
while(var != "exit"):
		
	var = input()

	#command list
	if(var == "list"):
		langNumber, langs = list_command()

	#handles the blank input
	elif(len(var) == 0):
		print("invalid command")
		
	#request command
	elif(var.split()[0] == "request"):
		#request translation words
		if(len(var.split()) > 3 and var.split()[2] == "t" and len(var.split()) <= 13):
			request_command_t(var)

		#request translation file
		elif(len(var.split()) > 3 and var.split()[2] == "f"):
			request_command_f(var)

		#handles a bar request command
		else:
			print("invalid request, try again")

	#handles a bad command
	elif("exit" not in var.split()):
		print("invalid command")

sock1.close()
