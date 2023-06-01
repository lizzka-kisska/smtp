import base64
import socket
import ssl
import sys

HOST = 'smtp.yandex.ru'
PORT = 465
USER_FROM = 'la-work-hard@yandex.ru'
BOUNDARY = 'bound2003'

ssl_contex = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_contex.check_hostname = False
ssl_contex.verify_mode = ssl.CERT_NONE

with open('configuration/config.txt', 'r') as config_file:
    f = config_file.read()
    lines = f.split('\n')
    USER_TO = lines[0]
    SUBJECT = lines[1]
    FILENAMES = lines[2].split(', ')

with open('password_yandex.txt', 'r') as password_file:
    PASSWORD = password_file.read().strip()


def create_headers():
    return f'FROM: {USER_FROM}\n' \
           f'TO: {USER_TO}\n' \
           f'SUBJECT: {SUBJECT}\n' \
           f'MIME-Version: 1.0\n' \
           f'Content-Type: multipart/mixed;\n' \
           f'\tboundary={BOUNDARY}\n'


def create_text_body():
    with open('configuration/plain_text.txt', 'r') as message_file:
        content = message_file.read()
    if content.startswith('.\n'):
        content = content[2:]
    content = content.replace('\n.', '\n..')
    return f'--{BOUNDARY}\n' \
           f'Content-Type: text/html; charset=utf-8\n' \
           f'\n' \
           f'{content}\n'


def create_attachment_body(file):
    path = file if file.find('configuration/') != -1 else 'configuration/' + file
    with open(path, 'rb') as attachment_file:
        attachment = attachment_file.read()
        attachment_base64 = base64.b64encode(attachment).decode()
    content_type = ''
    match file.split('.')[1]:
        case 'jpg':
            content_type = 'image/jpeg'
        case 'mp3':
            content_type = 'audio/basic'
        case 'mp4':
            content_type = 'video/mpeg'
        case 'pdf':
            content_type = 'application/pdf'
    return f'--{BOUNDARY}\n' \
           f'Content-Disposition: attachment;\n' \
           f'\tfilename={file}\n' \
           f'Content-Transfer-Encoding: base64\n' \
           f'Content-Type: {content_type};\n' \
           f'\tname={file}\n' \
           f'\n' \
           f'{attachment_base64}\n'


def message_prepare():
    headers = create_headers()
    text_body = create_text_body()
    message = headers + f'\n' + text_body
    for filename in FILENAMES:
        message += create_attachment_body(filename)
    message += f'--{BOUNDARY}--\n.\n'
    return message


def request(sock, data):
    sock.send((data + '\n').encode())
    recv_data = str(sock.recv(1024).decode())
    status_code = recv_data[:3]
    code = recv_data[4:9]
    if status_code == '354':
        print('The connection to the server has been established, the message transmission will now begin')
    elif status_code == '510' or status_code == '512' or status_code == '513' \
            or status_code == '515' or status_code == '550' or status_code == '555':
        print('The transmission of the message was interrupted, as it may not be the mail address')
    elif status_code == '523':
        print('The size of the letter exceeds the limit')
    elif status_code == '250' and code == '2.0.0':
        print('Your email has been sent, goodbye!')


def send_data():
    try:
        with socket.create_connection((HOST, PORT)) as sock:
            with ssl_contex.wrap_socket(sock, server_hostname=HOST) as client:
                client.recv(1024)
                request(client, f'ehlo {USER_FROM}')

                base64login = base64.b64encode(USER_FROM.encode()).decode()
                base64password = base64.b64encode(PASSWORD.encode()).decode()

                request(client, 'AUTH LOGIN')
                request(client, base64login)
                request(client, base64password)

                request(client, f'MAIL FROM:{USER_FROM}')
                for user in USER_TO.split(', '):
                    request(client, f'RCPT TO:{user}')
                request(client, 'DATA')
                request(client, message_prepare())
    except OSError:
        print('You entered the file names incorrectly (you need, for example: name1, name2)')
        sys.exit(0)


if __name__ == '__main__':
    send_data()
