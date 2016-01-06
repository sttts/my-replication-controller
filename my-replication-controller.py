#!/usr/bin/env python

import pprint, os, time, sys
from pyk import toolkit, util
import shortuuid
import logging
logging.getLogger("requests").setLevel(logging.WARNING)


REPLICAS = int(sys.argv[1])


master = os.getenv("KUBERNETES_MASTER", "http://localhost:8080")
print "Connecting to master at " + master
kubeclient = toolkit.KubeHTTPClient(api_server=master, debug=False)

while True:
    # count mypods
    response = kubeclient.execute_operation(method="GET", ops_path="/api/v1/namespaces/default/pods?labelSelector=name%3Dmypod")
    mypods = response.json()['items']
    running_mypods = len(mypods)
    print "{} running".format(running_mypods)

    # too many?
    if running_mypods > REPLICAS:
        to_delete = running_mypods - REPLICAS
        print "  Too many are running. Deleting {} pods:".format(to_delete)
        for pod in mypods[:to_delete]:
            print "    Deleting pod {}".format(pod['metadata']['name'])
            kubeclient.delete_resource(pod['metadata']['selfLink'])

    # too few?
    elif REPLICAS > running_mypods:
        to_launch = REPLICAS - running_mypods

        for n in range(0, to_launch):
            mypod_spec, _  = util.load_yaml(filename="mypod.yaml")
            mypod_spec["metadata"]["name"] += "-" + shortuuid.uuid()[:4].lower()

            print "Launching pod {}".format(mypod_spec["metadata"]["name"])
            response = kubeclient.execute_operation(method='POST',
                                         ops_path="/api/v1/namespaces/default/pods",
                                         payload=util.serialize_tojson(mypod_spec))
            if response.status_code >= 300:
                print "ERROR {}: {}".format(response.status_code, response.content)

    time.sleep(1)
