from django.shortcuts import render
from django.http import HttpResponse
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta
from django.conf import settings
import hashlib
import re
from django.middleware.csrf import get_token
from django.template.context_processors import csrf
from django.middleware import csrf
import requests
from django.views.decorators.csrf import csrf_exempt



def index(request):
    return render(request, 'main/index.html')

@csrf_exempt
def pedido(request):
    
    if request.method == 'POST':    
        numero_camas = request.POST.get('input_numero_camas')
        numero_sabanas = request.POST.get('input_numero_sabanas')
        numero_sillas = request.POST.get('input_numero_sillas')
        numero_sillones = request.POST.get('input_numero_sillones')
        firma = request.POST.get('signature')
        print(firma)
        if firma == verify_signature(numero_camas, numero_sabanas, numero_sillas, numero_sillones):
            log_pedidos_correctos(numero_camas, numero_sabanas, numero_sillas, numero_sillones)
            # Retorna una respuesta adecuada
            
            tendencias()
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

def verify_signature(numero_camas, numero_sabanas, numero_sillas, numero_sillones):
    
    cadena_datos = str(numero_camas) + str(numero_sabanas) + str(numero_sillas) + str(numero_sillones)
    # Calcular la firma utilizando la función hash SHA-256
    firma = hashlib.sha256(cadena_datos.encode()).hexdigest()

    return firma
   
def tendencias():

    # Read the text file
    with open('pedidos.txt', 'r') as file:
        text = file.read()

    # Extract the date and number using regular expressions
    date_pattern = r'Pedido realizado el (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
    number_pattern = r'Camas: (\d+)'

    date_match = re.search(date_pattern, text)
    number_match = re.search(number_pattern, text)

    if date_match and number_match:
        date = date_match.group(1)
        number = number_match.group(1)
    else:
        print("No match found.")
    return


def pedido_falso(request):
    
    url = "http://localhost:8000/pedido/"
    
    response = requests.get(url)

    # Datos del formulario a enviar
    data = {
        'checkBox_camas': 'on',
        'input_numero_camas': 2,
        'checkBox_sabanas': 'on',
        'input_numero_sabanas': 4,
        'checkBox_sillas': 'on',
        'input_numero_sillas': 6,
        'checkBox_sillones': 'on',
        'input_numero_sillones': 8,
        'signature': '12345'
    }
    

    response = requests.post(url, data=data)
    print(response.text)
    # Mostrar la respuesta del servidor
    
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

    