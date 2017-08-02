#TRS

import os
import socket
import sys
import signal

TCS_PORT = 58003
TRS_PORT = 59000
TCS_IP = socket.gethostbyname(socket.gethostname())
TRS_IP = socket.gethostbyname(socket.gethostname())

language = sys.argv[1]


if(len(language) > 20):
	print("Invalid language")
	exit(0)

if ("-p" in sys.argv):
	TRS_PORT = int(sys.argv[sys.argv.index("-p") + 1])

if ("-n" in sys.argv):
	TCS_IP = sys.argv[sys.argv.index("-n") + 1]

if ("-e" in sys.argv):
	TCS_PORT = int(sys.argv[sys.argv.index("-e") + 1])

message = "SRG " + language + " " + TRS_IP + " " + str(TRS_PORT) + "\n"
messageQuit = "SUN " + language + " " + TRS_IP + " " + str(TRS_PORT) + "\n"

def translate(word):

	result = ""
	with open("text_translation.txt", "r") as f:

		for line in f:

			if(line.split()[0] == word):
				result = line.split()[1]
				return result
	return "invalid"

def file_translate(word):

	result = ""
	with open("file_translation.txt", "r") as f:

		for line in f:

			if(line.split()[0] == word):
				result = line.split()[1]
				return result
	return "invalid"

#UDP

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(5)
tcs_addr = (TCS_IP, TCS_PORT)

try:
#send request to tcs
	sent = sock.sendto(message.encode('utf-8'), tcs_addr)

	#receive answer from tcs
	data, server = sock.recvfrom(128)
	resp = data.decode('utf-8')

except socket.timeout:
	print("tcs connection timeout")
	sock.close()
	exit()

#loop until connection is made
if(resp == "SRR NOK\n"):
	print("Invalid or repeated language")
	exit()
	
elif(resp == "SRR ERR\n"):
	print("Protocol error")
	exit()

try:
	#tcp connection
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((TRS_IP, TRS_PORT))
	s.listen(1)
except OSError as e:
	print("trying to access a port already in use")
	sent = sock.sendto(messageQuit.encode('utf-8'), tcs_addr)
	exit()

try:
	#loop until user shutsdown trs
	while(True):
		
		conn, addr = s.accept()
		data = conn.recv(30)
		data = data.split()

		if(data[1] == b'f'):
			header, data = data[:4], data[4:]
		else:
			header = data

		i = 0
		while(i < len(header)):
			header[i] = header[i].decode("utf-8")
			i += 1 	

		#text translation
		if(header[0] == "TRQ" and header[1] == "t" and len(header) < 14):

			request = header[3:]
			text = ' '.join(request)

			#translation request
			print(str(addr[0]) + " " + str(addr[1]) + ": " + text)

			i = 3
			p = 0
			result = ""

			while(i < len(header)):

				translated = translate(header[i])

				if(translated == "invalid"):
					break;

				result = result + translated + " "
				i = i + 1
				p = p + 1

			if(translated == "invalid"):

				#error message
				dispatch = "TRR NTA\n"

			else:

				#translation answer
				print(result + "(" + str(p) + ")")
				dispatch = "TRR t " + str(p) + " " + result + "\n"

			conn.send(dispatch.encode("utf-8"))
			conn.close()

		#file translation
		elif(header[0] == "TRQ" and header[1] == "f" and len(header) < 6):

			filename = header[2]
			filesizeR = int(header[3])
			f1 = open(filename, "wb")

			bytes = 0
			i = 0
			while(i < len(data)):
				f1.write(data[i])
				bytes += len(data[i])
				i += 1
			print(filesizeR)

			#translation request
			print(str(addr[0]) + " " + str(addr[1]) + ": " + filename)
			
			while(bytes < filesizeR):

				bytes += 128
				l1 = conn.recv(128)
				f1.write(l1)

			f1.seek(-1, os.SEEK_END)
			f1.truncate()
			f1.close()

			#file size
			print(str(bytes) + " Bytes received")

			filenameS = file_translate(filename)

			#no translation available
			if(filenameS == "invalid"):
				dispatch = "TRR NTA\n"
				conn.send(dispatch.encode("utf-8"))

			#found a translation available
			else:

				#file size to send
				filesize = os.stat(filenameS).st_size
				dispatch = "TRR f "+ filenameS + " " + str(filesize) + " "
				conn.send(dispatch.encode("utf-8"))
				f2 = open(filenameS, "rb")
				sended = 0
				while(sended < filesize):
					l2 = f2.read(128)
					sended += 128
					if(filesize - sended < 0):
						l2 += b'\n'
					conn.send(l2)
				#file sent
				print(filenameS + " (" + str(filesize) + ")")

			conn.close()
			f2.close()

		else:

			error = "TRR ERR\n"
			conn.send(error.encode("utf-8"))
			conn.close()

	s.close()

except KeyboardInterrupt:
	pass
finally:

	sent = sock.sendto(messageQuit.encode('utf-8'), tcs_addr)
	try:

		#receive answer from tcs
		sock.settimeout(5)
		data, server = sock.recvfrom(128)
		resp = data.decode('utf-8')

	except socket.timeout:
		print("")
	#tcs answer
	if(resp == "SUR OK\n"):
		print("TRS Shutdown...")

	s.close()
	sock.close()
	print('Bye!')
	exit()
