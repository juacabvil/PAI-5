from django.shortcuts import render
from django.http import HttpResponse
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta
from django.conf import settings
from django.middleware.csrf import get_token
from django.template.context_processors import csrf
from django.middleware import csrf
import requests
from django.views.decorators.csrf import csrf_exempt
import base64
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256



def index(request):
    return render(request, 'main/index.html')

@csrf_exempt
def pedido(request):
    
    if request.method == 'POST':    
        numero_camas = request.POST.get('input_numero_camas')
        numero_sabanas = request.POST.get('input_numero_sabanas')
        numero_sillas = request.POST.get('input_numero_sillas')
        numero_sillones = request.POST.get('input_numero_sillones')
        signature_base64 = request.POST.get('signature')
        public_key_pem = request.POST.get('public_key')
        
        if  verify_signature(numero_camas, numero_sabanas, numero_sillas, numero_sillones, signature_base64, public_key_pem):
            log_pedidos_correctos(numero_camas, numero_sabanas, numero_sillas, numero_sillones)
            # Retorna una respuesta adecuada
            return render(request, 'main/index.html')
        else:
            log_pedidos_incorrectos()
            return HttpResponse('Invalid signature')

        # Realiza las validaciones que necesites con los datos recibidos
        
    else:
        # Retorna una respuesta para el caso en que el método no sea POST
        return (render(request, 'main/pedido.html'))


def log_pedidos_correctos(camas, sabanas, sillas, sillones):
    fecha_pedido = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pedido = f"Pedido correcto realizado el {fecha_pedido}. Cantidad de productos:"
    if(camas):
        pedido+= ' Camas: '+ camas 
    if(sabanas):
        pedido+= ', Sabanas: '+sabanas
    if(sillas):
        pedido+= ', Sillas: '+sillas
    if(sillones):
        pedido+= ', Sillones: '+sillones
    
    with open("pedidos.txt", "a") as archivo:
        archivo.write(pedido + "\n")

def log_pedidos_incorrectos():
    fecha_pedido = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pedido = f"Pedido incorrecto realizado el {fecha_pedido}."
    with open("incorrectos.txt", "a") as archivo:
            archivo.write(pedido + "\n")

def verify_signature(numero_camas, numero_sabanas, numero_sillas, numero_sillones, signature_base64, public_key_pem):
    cadena_datos = str(numero_camas) + str(numero_sabanas) + str(numero_sillas) + str(numero_sillones)
    signature = base64.b64decode(signature_base64)

    # Convertir la clave pública en formato PEM a un objeto RSA
    public_key = RSA.importKey(public_key_pem)

    # Verificar la firma utilizando la clave pública
    h = SHA256.new(cadena_datos.encode('utf-8'))
    verifier = PKCS1_v1_5.new(public_key)
    return verifier.verify(h, signature)
   

def pedido_falso(request):
    
    # Definir una firma y clave pública falsas simulando man in the middle 
    signature_base64 = 'c2lnbmF0dXJlX2Jhc2U2NA=='
    public_key_pem = '-----BEGIN PUBLIC KEY-----\nMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC5t2UWQDdLgVbMvJXqwMnJfA8G\naOT22bF+eK/sq39dS0xPKPjvoDmzHpmPzFhKln1MJ//7Lm+9fDe3qkEz3qTZK6Y9\nEoebW7Z7T+zTZDbb6+7Kk3VP0MBcVEk27gKv0GWeVWd7YU5/fb7rJmkCzQZlk6+R\npW9JH8bJ1bMSI+O4pwIDAQAB\n-----END PUBLIC KEY-----'

    data = {
        'input_numero_camas': '2',
        'input_numero_sabanas': '4',
        'input_numero_sillas': '6',
        'input_numero_sillones': '8',
        'signature': signature_base64,
        'public_key': public_key_pem,
    }

    response = requests.post('http://localhost:8000/pedido/', data=data)
    
    return (render(request, 'main/index.html'))
    
    
def informe(request):
    # Initialize dictionaries to store the count of orders for each month
    orders_by_month = {}
    fake_orders_by_month = {}

    # Read the text files
    with open('pedidos.txt', 'r') as file:
        text = file.readlines()

    with open('incorrectos.txt', 'r') as file:
        fake_text = file.readlines()

    # Loop through each line in the text files
    for line in text:
        # Extract the date and time information from the line
        date_str = line.split('realizado el ')[1].split('.')[0]
        date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

        # Extract the month from the date and update the count in the dictionary
        month = date.strftime('%B %Y')
        if month in orders_by_month:
            orders_by_month[month] += 1
        else:
            orders_by_month[month] = 1

    for line in fake_text:
        # Extract the date and time information from the line
        date_str = line.split('realizado el ')[1].split('.')[0]
        date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

        # Extract the month from the date and update the count in the dictionary
        month = date.strftime('%B %Y')
        if month in fake_orders_by_month:
            fake_orders_by_month[month] += 1
        else:
            fake_orders_by_month[month] = 1

    # Convert the dictionaries to separate lists for the labels and data
    labels = list(orders_by_month.keys())
    data = list(orders_by_month.values())
    fake_labels = list(fake_orders_by_month.keys())
    fake_data = list(fake_orders_by_month.values())

    # Return the labels and data as a tuple
    context = {'data': data, 'labels': labels, 'fake_data': fake_data, 'fake_labels': fake_labels}
    return render(request, 'main/informe.html', context)

    