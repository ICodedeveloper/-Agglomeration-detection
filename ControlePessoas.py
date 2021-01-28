import cv2
import numpy as np
import os
from threading import Thread
import pygame
from datetime import datetime
import pyautogui
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import requests
import base64

labels_path = os.path.sep.join(["coco.names"])
LABELS = open(labels_path).read().strip().split("\n")
weights_path = os.path.sep.join(["yolov4-tiny.weights"])
config_path = os.path.sep.join(["yolov4-tiny.cfg"])
net = cv2.dnn.readNet(config_path, weights_path)

np.random.seed(42)
COLORS = np.random.randint(0, 255, size=(len(LABELS), 3), dtype="uint8")
ln = net.getLayerNames()
ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]


def blob_imagem(net, imagem):
    blob = cv2.dnn.blobFromImage(imagem, 1 / 255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    layerOutputs = net.forward(ln)

    return net, imagem, layerOutputs


def deteccoes(detection, _threshold, caixas, confiancas, IDclasses):
    scores = detection[5:]
    classeID = np.argmax(scores)
    confianca = scores[classeID]

    if confianca > _threshold:
        caixa = detection[0:4] * np.array([W, H, W, H])
        (centerX, centerY, width, height) = caixa.astype("int")

        x = int(centerX - (width / 2))
        y = int(centerY - (height / 2))

        caixas.append([x, y, int(width), int(height)])
        confiancas.append(float(confianca))
        IDclasses.append(classeID)

    return caixas, confiancas, IDclasses


def funcoes_imagem(imagem, i, confiancas, caixas, COLORS, LABELS, mostrar_texto=True):
    (x, y) = (caixas[i][0], caixas[i][1])
    (w, h) = (caixas[i][2], caixas[i][3])

    cor = [int(c) for c in COLORS[IDclasses[i]]]
    cv2.rectangle(imagem, (x, y), (x + w, y + h), cor, 2)
    texto = "{}: {:.4f}".format(LABELS[IDclasses[i]], confiancas[i])
    if mostrar_texto:
        print("> " + texto)
        print(x, y, w, h)
    cv2.putText(imagem, texto, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, cor, 2)

    return imagem, x, y, w, h


class ReiniciarConexao(Exception):
    pass


# camera = "rtsp://admin:perbras#2020@10.1.2.132:8080/cam/realmonitor?channel=1&subtype=0"
cameracel = "https://10.1.2.132:8080/video"
# camera = 0
video = []

while(True):
    time.sleep(10)
    try:
       arquivo_video = cameracel
       try:
            cap = cv2.VideoCapture(arquivo_video)
       except cv2.error as exc:
            raise ReiniciarConexao('Camera Ausente')
       conectado, video = cap.read()
       try:
            video_largura = video.shape[1]
            video_altura = video.shape[0]
       except:
           raise ReiniciarConexao('Camera Ausente')
    except ReiniciarConexao as exc:
            print("%s" % exc)
    if conectado == True:
        break




def redimensionar(largura, altura, largura_maxima=600):
    if (largura > largura_maxima):
        proporcao = largura / altura
        video_largura = largura_maxima
        video_altura = int(video_largura / proporcao)
    else:
        video_largura = largura
        video_altura = altura

    return video_largura, video_altura


threshold = 0.5
threshold_NMS = 0.3
fonte_pequena, fonte_media = 0.4, 0.6
fonte = cv2.FONT_HERSHEY_SIMPLEX


def enviarMsgBot(mystring):
    numero = "3"
    base64 = mystring

    url = "https://webrun.perbras.com.br/PGI/mensagapi.rule?sys=PGI"

    payload = "{\r\n\"token\":\"Adkx5TMuyIN1QK6NjNjmh6G7RA1+YKfPRFYyhnPoB/5CXxgTl7ps1scs5JVBVJgz\",\r\n\"action\":\"sendMessage\",\r\n\"wbody\":\"Alerta ! - Detectado o máximo de pessoas permitidas no (Cozinha - Sala Principal) !\",\r\n\"chatid\":\"c#" + numero + "\",\r\n\"lat\":\"\",\r\n\"lon\":\"\",\r\n\"filename\":\"download.jpg\",\r\n\"file64\":\"" + base64 + "\"\r\n}"

    headers = {}

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text.encode('utf8'))


class Th(Thread):

    def __init__(self, num):
        Thread.__init__(self)
        self.num = num

    def run(self):
        global qtdpessoas
        global antes
        time.sleep(2)

        if qtdpessoas >= 5:

            capturar = pyautogui.screenshot()
            capturar.save('print.jpg')
            print("Quantidade de pessoas : ", qtdpessoas)
            time.sleep(4)
            pygame.mixer.init()
            pygame.mixer.music.load("audio.wav")
            pygame.mixer.music.play()

            from datetime import datetime
            from datetime import timedelta

            FMT = '%m/%d/%Y %H:%M:%S'

            end_time = datetime.strptime(agora, FMT)
            print(end_time, antes)
            if end_time > antes + timedelta(minutes=1):
                enviarEmail()
                antes = datetime.strptime(agora, FMT)
                print("Email Enviado com Sucesso !")
                with open("print.jpg", "rb") as img_file:
                    my_string = base64.b64encode(img_file.read())
                    my_string = str(my_string)
                    my_string = my_string.replace("b'", "")
                    enviarMsgBot(my_string)
                    print("Mensagem no Bot Enviado com Sucesso !")

            else:
                print("ainda não e o momento")


hora = time.ctime()


def enviarEmail():
    smtp_server = 'smtp.office365.com'
    smtp_port = 587
    acc_addr = 'noreply@perbras.com.br'
    acc_pwd = '+j7+#JaK.=#,:hF'

    to_addr = 'marcilio.dantas@perbras.com.br'
    subject = f'Aglomeração {hora}!'
    body = 'Alerta ! - Detectado o máximo de pessoas permitidas no (Cozinha - Sala Principal) !'

    # Configura o servidor de envio (SMTP)
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(acc_addr, acc_pwd)

    # Cria o documento com várias partes
    msg = MIMEMultipart()
    msg["From"] = acc_addr
    msg["To"] = to_addr
    msg["Subject"] = subject

    # Anexa a imagem
    imgFilename = 'Aglomeração.jpg'  # Repare que é diferente do nome do arquivo local!
    with open('print.png', 'rb') as f:
        msgImg = MIMEImage(f.read(), name=imgFilename)
    msg.attach(msgImg)

    # Anexa o corpo do texto
    msgText = MIMEText('<b>{}</b><br><img src="cid:{}"><br>'.format(body, imgFilename), 'html')
    msg.attach(msgText)

    # Envia!
    server.sendmail(acc_addr, to_addr, msg.as_string())
    server.quit()


classes = ["pessoas"]
global a
global antes
FMT = '%m/%d/%Y %H:%M:%S'
antes = datetime.strptime("01/01/1990 00:00:00", FMT)
a = Th(1)

while (cv2.waitKey(1) < 0):
    hora = time.ctime()
    try:
        z = 0
        try:
            conectado, frame = cap.read()
            t = time.time()
            frame = cv2.resize(frame, (video_largura, video_altura))
        except:
            cap = cv2.VideoCapture(arquivo_video)
            raise ReiniciarConexao('Camera Ausente')
        try:
            (H, W) = frame.shape[:2]
        except:
            raise ReiniciarConexao("Camera não conectada")

        imagem_cp = frame.copy()
        net, frame, layerOutputs = blob_imagem(net, frame)
        caixas = []
        confiancas = []
        IDclasses = []

        for output in layerOutputs:
            for detection in output:
                caixas, confiancas, IDclasses = deteccoes(detection, threshold, caixas, confiancas, IDclasses)

        objs = cv2.dnn.NMSBoxes(caixas, confiancas, threshold, threshold_NMS)

        if len(objs) > 0:
            for i in objs.flatten():
                if LABELS[IDclasses[i]] in classes:
                    frame, x, y, w, h = funcoes_imagem(frame, i, confiancas, caixas, COLORS, LABELS,
                                                       mostrar_texto=False)
                    objeto = imagem_cp[y:y + h, x:x + w]
                    x = LABELS[IDclasses[i]].count("pessoas")
                    z = z + len(str(x))
                    qtdpessoas = z

                    if not a.is_alive():
                        a = Th(1)
                        a.start()
                        import datetime

                        now = datetime.datetime.now()
                        agora = now.strftime('%m/%d/%Y %H:%M:%S')

        cv2.putText(frame, "frame processado em {:.2f} segundos".format(time.time() - t),
                    (20, video_altura - 50), fonte, fonte_pequena, (250, 250, 250), 0, lineType=cv2.LINE_AA)

        cv2.putText(frame, f"frame processado {hora}, quantidade de pessoas {z} ".format(time.time() - t),
                    (20, video_altura - 20), fonte, fonte_pequena, (250, 250, 250), 0, lineType=cv2.LINE_AA)

        cv2.imshow("Captura de Pessoas", frame)

    except ReiniciarConexao as exc:
        print("%s" % exc)
