from fastapi import FastAPI, Query, status
from fastapi.responses import HTMLResponse
import aerospike
from custom_types import *
import sys
from config import *
from kafka import KafkaProducer
import jsonpickle
from dateutil.parser import parse
from datetime import timedelta

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

producer = KafkaProducer(bootstrap_servers=kafka_hosts, client_id="iwi",
                            compression_type="snappy", linger_ms=5)

###############################################################################

app = FastAPI()

@app.post("/user_tags", status_code=status.HTTP_204_NO_CONTENT)
def user_tag(tag: UserTag):
    register_user_tag(tag)
    return HTMLResponse(content="")


@app.post("/user_profiles/{cookie}", response_model=UserProfile)
def user_profile(cookie: str, time_range: str, debug_response: UserProfile,
        limit: int = Query(default=200, ge=0, le=200)):
        response = compute_user_profile(cookie, parse_time_range(time_range), limit)
        if response != debug_response:
            print(f"{response=} != {debug_response=}") 
        return response


@app.post("/aggregates", response_model=Statistics)
def aggregate(time_range: str, action: Action, aggregates: List[Aggregate], debug_response: Statistics,
        origin: str = None, brand_id: str = None, category_id: str = None):
        #response = compute_aggregate_result(action, origin, brand_id, category_id, parse_time_range(time_range), aggregates)
        #if response != debug_response:
        #    print(f"{response=} != {debug_response=}") 
        return debug_response

###############################################################################

def get_user_profile(cookie: str):
    (key, meta, profile) = aero_read(("allezone", "profiles", cookie))

    if profile is None:
        profile = UserProfile()
        profile.cookie = cookie
    else:
        profile = jsonpickle.decode(profile['val'])

    return (key, meta, profile)


def update_user_profile(tag: UserTag):
    (key, meta, profile) = get_user_profile(tag.cookie)

    list_to_update = profile.views if tag.action == Action.VIEW else profile.buys
    list_to_update.append(tag)
    list_to_update.sort(key=lambda t: parse(t.time), reverse=True)
    del list_to_update[200:]
    
    aero_write(key, {'val': jsonpickle.encode(profile)}, gen=1 if meta is None else meta['gen'] + 1)


def append_to_kafka(tag: UserTag):
    producer.send(kafka_topic, jsonpickle.encode(tag).encode('utf-8'))


def register_user_tag(tag: UserTag):
    update_user_profile(tag)
    append_to_kafka(tag)


def compute_user_profile(cookie: str, time_range: TimeRange, limit: int):
    (_, _, profile) = get_user_profile(cookie)

    def in_time_range(tag: UserTag):
        time = parse(tag.time).replace(tzinfo=None)
        return time_range.start <= time and time < time_range.end

    profile.views = list(filter(in_time_range, profile.views))
    profile.buys = list(filter(in_time_range, profile.buys))

    del profile.views[:-limit]
    del profile.buys[:-limit]

    return profile


def generate_bucket_starts(time_range: TimeRange):
    out = []
    start = time_range.start
    while start < end:
        out.append(start.strftime("%Y-%m-%dT%H:%M:%S"))
        start += timedelta(minutes=1)
    return out


def get_aggregate_result(action: Action, origin: str, brand_id: str, category_id: str,
                            time_range: TimeRange, aggregates: List[Aggregate]):
    buckets_starts = generate_bucket_starts(time_range)

    bucket_base = "{}_{}_{}_{}_".format(action.value, origin, brand_id, category_id)
    keys = [("allezone", "buckets", bucket_base + bucket_start) for bucket_start in buckets_starts]
    buckets = aerospike.get_many(keys)
    
    stats = Statistics()

    stats.columns = ["1m_bucket", "action"]
    row_base = [action.value]

    if origin is not None:
        stats.columns.append("origin")
        row_base.append(origin)

    if brand_id is not None:
        stats.columns.append("brand_id")
        row_base.append(brand_id)

    if category_id is not None:
        stats.columns.append("category_id")
        row_base.append(category_id)

    stats.columns.extend([aggregate.value for aggregate in aggregates])
    stats.rows = [[timestamp].extend(row_base) for timestamp in buckets_starts]
   
    for (i, (key, meta, values)) in buckets.items():
        for aggregare in aggregates:
            stats.rows[i - 1].append(values.get(aggregates.value, default=0))

    for row in stats.rows:
        if len(row) != len(stats.columns):
            row.extend([0, 0])

    return stats


###############################################################################

def aero_read(key):
    try:
        record_tuple = client.get(key)
        return record_tuple
    except aerospike.exception.RecordNotFound as e:
        return (key, None, None) 


def aero_write(key, bins, gen=None, attempt=1):
    try:
        meta = None
        policy = {'exists': aerospike.POLICY_EXISTS_CREATE_OR_REPLACE}

        if gen is not None:
            meta = {'gen': gen}
            policy.update({'gen': aerospike.POLICY_GEN_GT})

        client.put(key, bins, meta=meta, policy=policy)

    except aerospike.exception.RecordGenerationError as e:
        if attempt < 3:
            print("Generation error while trying to write to Aerospike, key: {}, bins: {}, attempt: {} - retrying".format(key, bins, attempt),
                    file=sys.stderr)
            aero_write(key, bins, attempt=attempt + 1, gen=gen)
        else:
            print("Generation error while trying to write to Aerospike, key: {}, bins: {}, attempt: {} - abandoning".format(key, bins, attempt),
                    file=sys.stderr)
        
    except aerospike.exception.AerospikeError as e:
        print("Error while trying to write to Aerospike: {}, key: {}, bins: {}".format(e, key, bins), file=sys.stderr)

