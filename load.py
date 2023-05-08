import threading
import time
from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder
import json

ENDPOINT = "a1dpybdy2d67sl-ats.iot.ca-central-1.amazonaws.com"
CLIENT_ID = "464884341358"
PATH_TO_CERTIFICATE = "data/certificate.pem.crt"
PATH_TO_PRIVATE_KEY = "data/private.pem.key"
PATH_TO_AMAZON_ROOT_CA_1 = "data/root.pem"
MESSAGE = "Hello World"
RANGE = 20

def read_lat_lon_from_file(filename):
    lat_lon_list = []
    with open(filename, 'r') as file:
        for line in file:
            lat, lon = map(float, line.strip().split(','))
            lat_lon_list.append((lat, lon))
    return lat_lon_list

filename = "data/New_Karachi_to_islamabad_route.txt"
lat_lon_list = read_lat_lon_from_file(filename)
coordinate_index = 0
serial_numbers = ["RTC448-18", "RTC419-18", "RTC592-18", "RTC578-18", "RTC525-18","RTC423-17","RTC109-16","RTC77-15","RTC696-13","RTC737-11,","RTCD4ADB432","RTC2222BAB3","RTCBAAAC2DC","RTC4CA43DBC","RTCAC1CB311","41RTC778","80RTC569","39RTC430","90RTC830","52RTC975","20RTC194","63RTC582","26RTC673","35RTC979","17RTC295","84RTC687","46RTC252","45RTC721","44RTC556","88RTC818",
"87RTC527","14RTC812","53RTC10","10RTC211","13RTC413","RTC321CB2DD","RTC2A211ACB","RTC32142BC2","RTC422BC22A","RTC422BD2D4","RTC3D4BA4A2","RTCA4C4DABC","RTCA3D1AD1D","RTC3BD1DCB3","RTC42143D41","RTCDC243D42","RTC3A4D1DA2","RTC2DD4C3BB","RTC33D11D3D","RTCCD1CBBBC","RTCDDAA2D31","RTC21C41DDD","RTC41DD2AD4","RTC224221BB","RTCBB4AC3D4"]

stop_threads = False
publish_counter = 0
publish_lock = threading.Lock()

def publish_to_serial_number(serial_number):
    global coordinate_index
    global stop_threads
    global publish_counter
    global publish_lock

    while not stop_threads:
        lat, lon = lat_lon_list[coordinate_index]
        current_epoch_time_int = int(time.time()) + 1
        payload = {
            "app": "gps",
            "payload": [
                current_epoch_time_int,
                2,
                lat,
                lon,
                10.5
            ]
        }

        json_payload = json.dumps(payload)
        Topic = f"dt/dev/router/{serial_number}"
        print("Published: '" + json_payload + "' to the topic: " + Topic)
        mqtt_connection.publish(topic=Topic, payload=json_payload, qos=mqtt.QoS.AT_LEAST_ONCE)
        time.sleep(2)

        with publish_lock:
            publish_counter += 1
            if publish_counter % len(serial_numbers) == 0:
                print("===============PUBLISHED====================")

        coordinate_index += 1
        if coordinate_index == len(lat_lon_list):
            coordinate_index = 0

    mqtt_connection.disconnect().result()

event_loop_group = io.EventLoopGroup(1)
host_resolver = io.DefaultHostResolver(event_loop_group)
client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint=ENDPOINT,
            cert_filepath=PATH_TO_CERTIFICATE,
            pri_key_filepath=PATH_TO_PRIVATE_KEY,
            client_bootstrap=client_bootstrap,
            ca_filepath=PATH_TO_AMAZON_ROOT_CA_1,
            client_id=CLIENT_ID,
            clean_session=False,
            keep_alive_secs=6
            )
print("Connecting to {} with client ID '{}'...".format(
        ENDPOINT, CLIENT_ID))
connect_future = mqtt_connection.connect()
connect_future.result()
print("Connected!")
print('Begin Publish')

threads = []

for serial_number in serial_numbers:
    thread = threading.Thread(target=publish_to_serial_number, args=(serial_number,))
    thread.start()
    threads.append(thread)

try:
    while True:
        all_threads_finished = True
        for thread in threads:
            thread.join(timeout=0.1)
            if thread.is_alive():
                all_threads_finished = False
                break
        if all_threads_finished:
            break
except KeyboardInterrupt:
    print("\nStopping threads and closing MQTT connections...")
    stop_threads = True
    for thread in threads:
        thread.join()
    print("All MQTT connections closed. Exiting.")
