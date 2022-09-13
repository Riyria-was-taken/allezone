import aerospike
import custom_types
import sys
from config import aerospike_hosts, kafka_hosts, kafka_topic
from kafka import KafkaConsumer
import jsonpickle
from aerospike_helpers.operations import operations
from datetime import datetime, timedelta

###############################################################################

config = {
    'hosts': aerospike_hosts, 
    'policies': {
        'timeout': 1000 # milliseconds
    }
}

try:
    client = aerospike.client(config).connect()
except:
    print("Failed to connect to the Aerospike cluster with", config['hosts'])
    sys.exit(1)

###############################################################################

consumer = KafkaConsumer(kafka_topic, bootstrap_servers=kafka_hosts,
                                client_id="owo", group_id="bucket_master")

###############################################################################

buckets = dict()
last_write = datetime.now() 

event_loop()


def write_to_aero():
    operations = []
    for (bucket, (count, sum_price)) in buckets.items():
        try:
            key = ("allezone", "buckets", bucket)
            client.operate(key, [ operations.increment(Action.COUNT.value, count)
                                , operations.increment(Action.SUM_PRICE.value, sum_price)])
        except aerospike.exception.AerospikeError as e:
            print("Error while trying to increment bins in Aerospike: {}, key: {}".format(e, key), file=sys.stderr)
    
    buckets.clear()


def generate_buckets_for_tag(tag: UserTag):
    action = tag.action.value
    time = tag.time.split('.')[0]
    combinations = itertools.product([tag.origin, None], [tag.brand_id, None], [tag.category_id, None])
    return ["{}_{}_{}_{}_{}".format(action, origin, brand, category, time) for (origin, brand, category) in combinations]


def event_loop():
    for msg in consumer:
        if datetime.now() > last_write + timedelta(minutes=1):
            write_to_aero()
            last_write = datetime.now()

        tag = jsonpickle.decode(msg.decode("utf-8"))
        for bucket in generate_buckets_for_tag(tag):
            (old_count, old_sum) = buckets.get(bucket, default=(0, 0))
            buckets[bucket] = (old_count + 1, old_sum + product_info.price)
    
