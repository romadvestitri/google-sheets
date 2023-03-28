from pprint import pprint

import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials
import socket
import time

ERROR_ANSWER = "HTTP/1.1 404 Not Found\r\nCache-Control: private\r\nContent-Type: text/plain\r\nContent-Length: 9\r\n\r\nNotFound"
ERROR_ANSWER1 = "HTTP/1.1 400 Bad Request\r\nCache-Control: private\r\nContent-Type: text/plain\r\nContent-Length: 9\r\n\r\nBad Request or TimeOut"

SHEETS = {
			'1JHd2okt9qehFoIDBz8wt1yvR4rQoNgBjQaneQmiFS7k': ['Лист1', 'Лист2'],	
			'1kbnaRHxrjluNkukZ9xpY_AOTMLtTq45BU_FPt6uIKMY': ['Лист1', 'Лист2']	
		 }

#Файлик json, получаемый при регистрации проекта
CREDENTIALS_FILE = 'creds.json'
# ID Google Sheets документа (можно взять из его URL)
spreadsheet_id = '1JHd2okt9qehFoIDBz8wt1yvR4rQoNgBjQaneQmiFS7k'

# Авторизуемся и получаем service — экземпляр доступа к API
credentials = ServiceAccountCredentials.from_json_keyfile_name(
	CREDENTIALS_FILE,
	['https://www.googleapis.com/auth/spreadsheets',
	 'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http = httpAuth)


sock = socket.socket()
sock.bind(('', 80))

while True:
	sock.listen(1)
	print("accepting...")
	conn, addr = sock.accept()
	main_data = ''
	main_time = time.time()
	conn.settimeout(2)
	while True:
		try:
			data = conn.recv(2048)
		except:
			try:
				conn.send(ERROR_ANSWER1.encode('utf-8'))
			except:
				pass
			break
		print(data)
		if not data or time.time() - main_time >=1:
			break
			
		data_arr = data.decode('utf-8')
		main_data += data_arr

		main_arr = main_data.split(": ")	
		find_str = main_arr[len(main_arr)-1]
		ind = find_str.find("\r\n\r\n")

		find_str = find_str[(ind+4):]
		if not find_str:
			print("not found string for searching")
			continue
		if find_str.find('%20') != -1:	
			find_str = find_str.replace("%20", " ")
		elif find_str.find('%40') != -1:
			find_str = find_str.replace("%20", "@")

		
		for key in SHEETS.keys():
			for sheet in SHEETS[key]:
				values = service.spreadsheets().values().get(
				spreadsheetId=key,
				range=f'{sheet}!A:E',
				majorDimension='ROWS'
				).execute()
				for i in range(len(values['values'])):
					if find_str in values['values'][i]:
						output_str = '{'
						for j in range(len(values['values'][i])):
							if values['values'][i][j] == '':
								continue
							if output_str == '{':
								output_str += values['values'][i][j]
							else:
								output_str += ', ' + values['values'][i][j]
						output_str += '}'
						ANSWER = f"HTTP/1.1 200 OK\r\nCache-Control: private\r\nContent-Type: text/html\r\nContent-Length: {len(output_str)}\r\n\r\n{output_str}"

						break
		try:		
			conn.send(ANSWER.encode('utf-8'))
			del output_str
			del ANSWER
			break
		except:
			try:
				conn.send(ERROR_ANSWER.encode('utf-8'))
				conn.close()
			except:
				pass
			break
	conn.close()	
	