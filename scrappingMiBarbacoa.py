import requests
from bs4 import BeautifulSoup
import datetime
import pandas
import re
from confluent_kafka import Producer
import socket
DIRECCION_SITEMAP = "https://mibarbacoa.com/sitemap.xml"
lista_productos = {}
json_productos = []
CONF = {'bootstrap.servers': 'localhost:9092', 'client.id': socket.gethostname()}

def web_kafka(producto):
    producer = Producer(CONF)
    def acked(err, msg):
        if err is not None:
            print("Failed to deliver message: %s: %s" % (str(msg), str(err)))
        else:
            print("Message produced: %s" % (str(msg)))
    producer.produce("miBarbacoaData", key="key", value=str(producto), callback=acked)
    producer.poll(1)

def get_urls():
    sitemap = requests.get(DIRECCION_SITEMAP)
    print("\n Status al obtener SiteMap: " + str(sitemap.status_code)) # 200 
    # print (sitemap.content)    # Devuelve el XML con el html
    soup = BeautifulSoup(sitemap.content, "xml")
    todos_soup = soup.find_all("loc")
    return [i.text for i in todos_soup]

def get_each_product(direccion_url, lista_productos):
    # print(direccion_url)
    page = requests.get(direccion_url)
    print("\n Status al obtener el HTML: " + str(page.status_code),direccion_url) # 200 

    soup = BeautifulSoup(page.content, 'html.parser')
    if(soup is not None):
        
        listaProductosHtml = soup.find(id="js-product-list")
        if(listaProductosHtml is not None):

            listaProductos = listaProductosHtml.find_all("article")
            if(listaProductos is not None):
                count = 0
                for productoArticulo in listaProductos:
                    
                    if(productoArticulo is not None):
                        # producto = {}
                        titulo = productoArticulo.find("h2", class_="product-title").find("a") if productoArticulo.find("h2", class_="product-title").find("a") is not None else "Nan"

                        imagen = productoArticulo.find("img", class_="product-thumbnail-first")["src"] if productoArticulo.find("img", class_="product-thumbnail-first") is not None else "Nan"
                        
                        # if imagen is not None:
                        #     url_imagen = imagen["src"]
                        #     print("URL de la imagen:", url_imagen)

                        enlace_producto = titulo["href"] if titulo["href"] is not None else "Nan"

                        texto_titulo = titulo.get_text() if titulo is not None else "Nan"

                        precio = productoArticulo.find("span", class_="product-price").get("content") if productoArticulo.find("span", class_="product-price") is not None else "Nan"

                        no_hay_stock = productoArticulo.find("span",class_="product-unavailable")  if productoArticulo.find("span",class_="product-unavailable") is not None else "Nan"
                        # None if no_hay_stock =="Nan" else print("Edu ", no_hay_stock)
                        hay_stock = productoArticulo.find("span",class_="product-available") if productoArticulo.find("span",class_="product-available") is not None else "Nan"
                        # print(hay_stock)

                        # descripcion = productoArticulo.find("div",class_="product-description-short").get_text() if productoArticulo.find("div",class_="product-description-short") is not None else "Nan"
                        
                        # descripcion = descripcion.replace('x', ';')
                        # print(descripcion)
                        # print()
                        # print(re.sub(r'[\n\t\;\s]+', ' ', descripcion.replace(';', ',')))
                        referencia_producto = productoArticulo.find("div",class_="product-reference").get_text() if productoArticulo.find("div",class_="product-reference") is not None else "Nan"

                        categoria = productoArticulo.find("div",class_="product-category-name").get_text() if productoArticulo.find("div",class_="product-category-name") is not None else "Nan"

                        lista_productos[texto_titulo]={
                                # "descripcion":re.sub(r'[\n\t\;\s]+', ' ', descripcion.replace(';', ',')),
                                # "titulo_producto":texto_titulo,
                                "categoria":re.sub(r'[\n\t\;\s]+', ' ', categoria.replace(';', ',')),
                                "referencia_producto":re.sub(r'[\n\t\;\s]+', ' ', referencia_producto.replace(';', ',')),
                                "enlace_producto":enlace_producto.replace(';', ','),
                                "imagen_url":imagen.replace(';', ','),
                                # "imagen":imagen,
                                "precio":float(precio),
                                "disponible":True if no_hay_stock =="Nan" else False
                            }
                        
                        producto_kafka = {
                                # "descripcion":re.sub(r'[\n\t\;\s]+', ' ', descripcion.replace(';', ',')),
                                "titulo_producto":texto_titulo,
                                "categoria":re.sub(r'[\n\t\;\s]+', ' ', categoria.replace(';', ',')),
                                "referencia_producto":re.sub(r'[\n\t\;\s]+', ' ', referencia_producto.replace(';', ',')),
                                "enlace_producto":enlace_producto.replace(';', ','),
                                "imagen_url":imagen.replace(';', ','),
                                # "imagen":imagen,
                                "precio":float(precio),
                                "disponible":True if no_hay_stock =="Nan" else False
                            }
                        
                        # json_productos.append(otro)
                        web_kafka(producto_kafka)
                        # print(producto_kafka)
                        
                    
                    count+=1 

    return lista_productos

direcciones_web = get_urls()
# print(direcciones_web)
ct = 0
errores = 0
for url in direcciones_web:
    if ct == 133: # Cortamos en la url numero 133 para ahorrar recursos, ya que no tengo muchos más productos desde este punto
        print("Cortamos en la url numero 133 para ahorrar recursos, ya que no tengo muchos más productos desde este punto")
        break
    try :
        lista_productos = get_each_product(direccion_url=url,lista_productos=lista_productos)
    except Exception as e:
        errores+=1
        print("\n\n\t\033[91mHA HABIDO UN ERROR: "+str(e)+"\033[0m\n\n")

    ct+=1
    print(" Página Número: "+str(ct)+" / "+str(len(direcciones_web))+" \n Productos en el diccionario: "+str(len(lista_productos))+"\n")

print("\n\033[92mRevisión de las páginas completadas, tenemos un total de "+str(len(lista_productos))+" productos\033[0m\n Procesando Datos y creando CSV...\n")
df = pandas.DataFrame(lista_productos)
df.head(31)
df_productos = df.T # TRASPONEMOS LA MATRIZ


df_productos["titulo_producto"] = df_productos.index
df_productos.reset_index(drop=True, inplace=True)
# df_productos.head()


fecha_actual = datetime.datetime.now().strftime('%Y%m%d')
#nombre_fichero_csv = "/home/ubuntuks/Documents/MiBarbacoaProductos_"+fecha_actual+".csv"
nombre_fichero_csv = "datos/MiBarbacoaProductos_"+fecha_actual+".csv" 
df_productos.to_csv(nombre_fichero_csv, index=False, sep=";", na_rep="NaN")
print("\t\033[92mCSV: "+nombre_fichero_csv+" creado con exito\033[0m\n")

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Configuración del servidor SMTP
smtp_server = "ssl0.ovh.net"  
port = 587  
username = "info@edvardks.com" # PONGA AQUÍ SU CORREO DESDE EL QUE SE VA A ENVIAR EL AVISO 
password = "PONGA AQUI LA CONTRASEÑA DE SU CORREO"  

# Configuración del correo electrónico
from_email = "info@edvardks.com" # CORREO REMITENTE DEL AVISO
to_email = "edwar_@outlook.com" # AQUÍ VA EL CORREO DÓNDE QUIERE RECIBIR EL AVISO
subject = "BigData Aplicado ha ejecutado el scraping contra mibarbacoa.com - Resultados"
message = "Se han revisado "+str(ct)+" URLS y han fallado "+str(errores)+" URLS.\n el dataFrame.shape devuelve: "+str(df_productos.shape) 

# Crear el mensaje
msg = MIMEMultipart()
msg['From'] = from_email
msg['To'] = to_email
msg['Subject'] = subject
msg.attach(MIMEText(message, 'plain'))

# Crear una conexión segura con el servidor usando TLS
server = smtplib.SMTP(smtp_server, port)
server.starttls()

# Iniciar sesión en el servidor SMTP
server.login(username, password) 

# Enviar el correo electrónico
server.sendmail(from_email, to_email, msg.as_string()) 

server.quit()

# crontab -e  