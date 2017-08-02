#TCS

import os
import socket
import sys

UDP_PORT = 58003
TCS_IP = socket.gethostbyname(socket.gethostname())
TRS_SRG_OK = 'SRR OK\n'
TRS_SUN_OK = 'SUR OK\n'
TRS_NOK = 'SRR NOK\n'
TRS_EOF = 'UNR EOF\n'
TRS_ERR = 'UNR ERR\n'
UNQ_RESP = 'ULR'
UNQ_REQ = 'UNR'
UNQ_EOF = 'UNR EOF\n'
UNQ_ERR = 'UNR ERR\n'
ULQ_EOF = 'ULR EOF\n'
ULQ_ERR = 'ULR ERR\n'
MAX_CHAR_LANGUAGE = 20
MAX_LANGUAGES = 99

if ("-p" in sys.argv):
	UDP_PORT = int(sys.argv[sys.argv.index("-p") + 1])

def searchInFile(language):

	with open('languages.txt', 'r') as f:
		
		for line in f:
			if(language in line):
				return line

	return None


def countLanguages():

	count = 0
	with open('languages.txt', 'r') as f:
		
		for line in f:
			count += 1

	return count


def languagesInFile():

	languages = ''
	count = 0

	with open('languages.txt', 'r') as f:
		
		for line in f:
			languages = languages + line.split()[0] + ' '
			count += 1

	if(count == 0):
		return None
	return (str(count), languages)


def writeInFile(line):

	with open('languages.txt', mode = 'a') as f:
		f.write(line + '\n')


def deleteLineFromFile(arg):

	deleted = False

	with open('languages.txt', 'r') as f:
		lines = f.readlines()

	with open('languages.txt', 'w') as f:
		for line in lines:
			if(line != arg):
				f.write(line)
			else:
				deleted = True
		return deleted


try:

	open('languages.txt', 'w')

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((TCS_IP, UDP_PORT))

	while(True):

		data, addr = sock.recvfrom(1024)
		raw = data.decode('UTF-8')
		message = raw.split()

		#Languages request from user (User)
		if(message[0] == "ULQ" and raw[len(raw) - 1] == '\n'):
			if(len(message) == 1):
				txt = languagesInFile()
				
				if(txt != None):
					
					languages = txt[1].rstrip()

					sent = sock.sendto((UNQ_RESP + ' ' + str(txt[0]) + ' ' + languages + '\n').encode('UTF-8'), addr)
					print("List request: " + addr[0] + ' ' + str(addr[1]))
					print(languages)
				else:
					sent = sock.sendto((ULQ_EOF).encode('UTF-8'), addr)
					print("List request: " + addr[0] + ' ' + str(addr[1]))
			else:
				sent = sock.sendto((ULQ_ERR).encode('UTF-8'), addr)

		#Language server request from user (User)
		if(message[0] == "UNQ" and raw[len(raw) - 1] == '\n'):
			if(len(message) == 2):
				txt = searchInFile(message[1])

				if(txt != None):

					txt = txt.split()
					sent = sock.sendto((UNQ_REQ + ' ' + txt[1] + ' ' + txt[2] + '\n').encode('UTF-8'), addr)
					print(txt[1] + ' ' + txt[2])
				else:
					sent = sock.sendto((UNQ_EOF).encode('UTF-8'), addr)
			else:
				sent = sock.sendto((UNQ_ERR).encode('UTF-8'), addr)

		#Request to add a language server (TRS)
		if(message[0] == "SRG" and raw[len(raw) - 1] == '\n'):
			if(len(message) == 4):
				txt = searchInFile(message[1])

				if(txt == None and countLanguages() < MAX_LANGUAGES and len(message[1]) <= MAX_CHAR_LANGUAGE):
					writeInFile(message[1] + ' ' + message[2] + ' ' + message[3])
					sent = sock.sendto(TRS_SRG_OK.encode('UTF-8'), addr)
					print('+' + ' ' + message[1] + ' ' + message[2] + ' ' + message[3])

				else:
					sent = sock.sendto(TRS_NOK.encode('UTF-8'), addr)
			else:
				sent = sock.sendto(TRS_ERR.encode('UTF-8'), addr)

		#Remove language from languages.txt (TRS)
		if(message[0] == "SUN" and raw[len(raw) - 1] == '\n'):
			if(len(message) == 4):
				
				txt = searchInFile(message[1])

				if(txt != None):

					if(deleteLineFromFile(txt)):
						sent = sock.sendto(TRS_SUN_OK.encode('UTF-8'), addr)
						print('- ' + txt.rstrip())
					else:
						sent = sock.sendto(TRS_NOK.encode('UTF-8'), addr)
				else:
					sent = sock.sendto(TRS_NOK.encode('UTF-8'), addr)
			else:
				sent = sock.sendto(TRS_ERR.encode('UTF-8'), addr)

except KeyboardInterrupt:
    pass
finally:
    sock.close()
    os.remove('languages.txt')
    print('Bye!')
    exit()
