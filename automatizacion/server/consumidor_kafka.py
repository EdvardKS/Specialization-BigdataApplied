from kafka import KafkaConsumer
from datetime import datetime

nombre_grupo = 'grupo_' + datetime.now().strftime('%Y%m%d%H%M%S')

consumer = KafkaConsumer('miBarbacoaData',
                         bootstrap_servers=['localhost:9092'],
                         auto_offset_reset='earliest', 
                         enable_auto_commit=True,
                         group_id=nombre_grupo) 

variable = []
i = 0
for message in consumer:
    # print(message.value.decode('utf-8'))
    # break
    variable.append(message.value.decode('utf-8')) 
    if i == 100:
        break
    else:
        i+=1

print(variable)
