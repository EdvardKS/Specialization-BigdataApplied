import subprocess
import json
import os


def guardar_resultado_en_json(resultado, nombre_archivo):
    with open(nombre_archivo, 'w') as f:
        json.dump(resultado, f)



def ejecutar_ssh():
    # Este hace uso del archivo py del servidor para crear un consumidor y consumir el topic de kafka
    ssh_command = "ssh -p 35001 8ia-edvard@abastos.duckdns.org 'python3 /home/8ia-edvard/bdAplic/consumidor_kafka.py'"
    # Este crea un consumidor de forma nativa para atacar a la topic y consumir su contenido
    # ssh_command = "ssh -p 35001 8ia-edvard@abastos.duckdns.org '/usr/local/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic miBarbacoaData --from-beginning'"
    try:
        resultado = subprocess.check_output(ssh_command, shell=True)
        return resultado.decode()
    except subprocess.CalledProcessError as e:
        return "Error al ejecutar el comando SSH: {}".format(e)

if __name__ == "__main__":
    resultado_ssh = ejecutar_ssh()
    print("Resultado obtenido con exito!")
    guardar_resultado_en_json(resultado_ssh, "resultado.csv")
    print("Resultado gaurdado en resultado.json con exito!")


# Ejecutar el comando Docker
# comando_docker = "docker run --rm -it --network mi_red -v ./proy.conf:/usr/share/logstash/config/proy.conf docker.elastic.co/logstash/logstash:7.15.2 -f /usr/share/logstash/config/proy.conf"
comando_docker = "docker run --rm -it --network elog \
                  -v ./pipelines.yml:/usr/share/logstash/config/pipelines.yml \
                  -v ./logstash.yml:/usr/share/logstash/config/logstash.yml \
                  -v ./proy.conf:/usr/share/logstash/config/proy.conf \
                  -v ./resultado.json:/home/resultado.json \
                  docker.elastic.co/logstash/logstash:7.17.21 \
                  -f /usr/share/logstash/config/proy.conf"


os.system(comando_docker)


#cd /mnt/c/Users/Edwar/Documents/configuracion/