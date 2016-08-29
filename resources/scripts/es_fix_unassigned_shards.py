
# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from pyLibrary import convert
from pyLibrary.debugs import constants
from pyLibrary.debugs import startup
from pyLibrary.debugs.logs import Log
from pyLibrary.dot import wrap, listwrap, Dict
from pyLibrary.env import http
from pyLibrary.maths import Math
from pyLibrary.maths.randoms import Random
from pyLibrary.queries import jx
from pyLibrary.queries.unique_index import UniqueIndex
from pyLibrary.thread.threads import Thread, Signal

CONCURRENT = 3
BIG_SHARD_SIZE = 5 * 1024 * 1024 * 1024  # SIZE WHEN WE SHOULD BE MOVING ONLY ONE SHARD AT A TIME


def assign_shards(settings):
    """
    ASSIGN THE UNASSIGNED SHARDS
    """
    path = settings.elasticsearch.host + ":" + unicode(settings.elasticsearch.port)

    # GET LIST OF NODES
    # coordinator    26.2gb
    # secondary     383.7gb
    # spot_47727B30   934gb
    # spot_BB7A8053   934gb
    # primary       638.8gb
    # spot_A9DB0988     5tb
    Log.note("get nodes")

    # stats = http.get_json(path+"/_stats")

    # TODO: PULL DATA ABOUT NODES TO INCLUDE THE USER DEFINED ZONES
    #

    nodes = UniqueIndex("name", list(convert_table_to_list(
        http.get(path + "/_cat/nodes?bytes=b&h=n,r,d,i,hm").content,
        ["name", "role", "disk", "ip", "memory"]
    )))
    if "primary" not in nodes or "secondary" not in nodes:
        Log.error("missing an important index\n{{nodes|json}}", nodes=nodes)

    zones = UniqueIndex("name")
    for z in settings.zones:
        zones.add(z)

    risky_zone_names = set(z.name for z in settings.zones if z.risky)

    for n in nodes:
        if n.role == 'd':
            n.disk = 0 if n.disk == "" else float(n.disk)
            n.memory = text_to_bytes(n.memory)
        else:
            n.disk = 0
            n.memory = 0

        if n.name.startswith("spot_") or n.name.startswith("coord"):
            n.zone = zones["spot"]
        else:
            n.zone = zones["primary"]

    total_node_memory = Math.sum(nodes.memory)

    for g, siblings in jx.groupby(nodes, "zone.name"):
        siblings = list(siblings)
        siblings = filter(lambda n: n.role == "d", siblings)
        for s in siblings:
            s.siblings = len(siblings)
    # Log.note("Nodes:\n{{nodes}}", nodes=list(nodes))

    # GET LIST OF SHARDS, WITH STATUS
    # debug20150915_172538                0  p STARTED        37319   9.6mb 172.31.0.196 primary
    # debug20150915_172538                0  r UNASSIGNED
    # debug20150915_172538                1  p STARTED        37624   9.6mb 172.31.0.39  secondary
    # debug20150915_172538                1  r UNASSIGNED
    shards = wrap(list(convert_table_to_list(http.get(path + "/_cat/shards").content,
                                             ["index", "i", "type", "status", "num", "size", "ip", "node"])))
    for s in shards:
        s.i = int(s.i)
        s.size = text_to_bytes(s.size)
        s.node = nodes[s.node]

    # TODO: MAKE ZONE OBJECTS TO STORE THE NUMBER OF REPLICAS

    # ASSIGN SIZE TO ALL SHARDS
    for g, replicas in jx.groupby(shards, ["index", "i"]):
        replicas = wrap(list(replicas))
        size = max(*replicas.size)
        for r in replicas:
            r.size = size

    # AN "ALLOCATION" IS THE SET OF SHARDS FOR ONE INDEX ON ONE NODE
    # CALCULATE HOW MANY SHARDS SHOULD BE IN EACH ALLOCATION
    allocation = UniqueIndex(["index", "node"])

    for g, replicas in jx.groupby(shards, "index"):
        replicas = wrap(list(replicas))
        index_size = Math.sum(replicas.size)
        total_expected_replicas = Math.sum(zones.shards)

        for n in nodes:
            allocation.add({
                "index": g.index,
                "node": n.name,
                "max_allowed": Math.ceiling(len(replicas)*(n.memory/total_node_memory)*(n.zone.shards/total_expected_replicas))
            })

        for r in replicas:
            r.index_size = index_size
            r.siblings = len(replicas)


    relocating = [s for s in shards if s.status in ("RELOCATING", "INITIALIZING")]

    # LOOKING FOR SHARDS WITH ZERO INSTANCES, IN THE spot ZONE
    not_started = []
    for g, replicas in jx.groupby(shards, ["index", "i"]):
        replicas = list(replicas)
        started_replicas = list(set([s.zone for s in replicas if s.status in {"STARTED", "RELOCATING"}]))
        if len(started_replicas) == 0:
            # MARK NODE AS RISKY
            for s in replicas:
                if s.status == "UNASSIGNED":
                    not_started.append(s)
                    break  # ONLY NEED ONE
    if not_started:
        Log.note("{{num}} shards have not started", num=len(not_started))
        Log.warning("Shards not started!!\n{{shards|json|indent}}", shards=not_started)
        if len(relocating) > 1:
            # WE GET HERE WHEN AN IMPORTANT NODE IS WARMING UP ITS SHARDS
            # SINCE WE CAN NOT RECOGNIZE THE ASSIGNMENT THAT WE MAY HAVE REQUESTED LAST ITERATION
            Log.note("Delay work, cluster busy RELOCATING/INITIALIZING {{num}} shards", num=len(relocating))
        else:
            allocate(30, not_started, relocating, path, nodes, set(n.zone for n in nodes) - risky_zone_names, shards)
        return
    else:
        Log.note("All shards have started")

    # LOOKING FOR SHARDS WITH ONLY ONE INSTANCE, IN THE RISKY ZONES ZONE
    high_risk_shards = []
    for g, replicas in jx.groupby(shards, ["index", "i"]):
        replicas = list(replicas)
        realized_zones = set([s.zone for s in replicas if s.status in {"STARTED", "RELOCATING"}])
        if len(realized_zones-risky_zone_names) == 0:
            # MARK NODE AS RISKY
            for s in replicas:
                if s.status == "UNASSIGNED":
                    high_risk_shards.append(s)
                    break  # ONLY NEED ONE
    if high_risk_shards:
        Log.note("{{num}} high risk shards found", num=len(high_risk_shards))
        allocate(10, high_risk_shards, relocating, path, nodes, set(n.zone for n in nodes) - risky_zone_names, shards)
        return
    else:
        Log.note("No high risk shards found")

    # LOOK FOR SHARD IMBALANCE
    not_balanced = Dict()
    for g, replicas in jx.groupby(filter(lambda r: r.status == "STARTED" and not r.index.startswith("unit"), shards), ["node", "index"]):
        replicas=list(replicas)
        if not g.node:
            continue
        _node = nodes[g.node]
        existing_shards = filter(lambda r: r.node == g.node and r.index == g.index, shards)
        if not existing_shards:
            continue
        num_shards = existing_shards[0].siblings
        max_allowed = Math.ceiling(num_shards/_node.siblings)
        for i in range(max_allowed, len(replicas), 1):
            i = Random.int(len(replicas))
            shard = replicas[i]
            not_balanced[_node.zone] += [shard]

    if not_balanced:
        for z, b in not_balanced.items():
            Log.note("{{num}} shards can be moved to better location within {{zone|quote}} zone", zone=z, num=len(b))
            allocate(CONCURRENT, b, relocating, path, nodes, {z}, shards)
            return
    else:
        Log.note("No shards need to move")

    # LOOK FOR SHARDS WE CAN MOVE TO SPOT
    too_safe_shards = []
    for g, replicas in jx.groupby(shards, ["index", "i"]):
        replicas = wrap(list(replicas))
        safe_replicas = jx.filter(
            replicas,
            {"and": [
                {"eq": {"status": "STARTED"}},
                {"neq": {"zone.name": "spot"}}
            ]}
        )
        if len(safe_replicas) >= len(replicas):  # RATHER THAN ONE SAFE SHARD, WE ARE ASKING FOR ONE UNSAFE SHARD
            # TAKE THE SHARD ON THE FULLEST NODE
            # node_load = jx.run({
            #     "select": {"name": "size", "value": "size", "aggregate": "sum"},
            #     "from": shards,
            #     "groupby": ["node"],
            #     "where": {"eq": {"index": replicas[0].index}}
            # })

            i = Random.int(len(replicas))
            shard = replicas[i]
            too_safe_shards.append(shard)

    if too_safe_shards:
        Log.note("{{num}} shards can be moved to spot", num=len(too_safe_shards))
        allocate(CONCURRENT, too_safe_shards, relocating, path, nodes, risky_zone_names, shards)
        return
    else:
        Log.note("No shards moved")

    # LOOK FOR UNALLOCATED SHARDS WE CAN PUT IN THE SPOT ZONE
    low_risk_shards = []
    for g, replicas in jx.groupby(shards, ["index", "i"]):
        replicas = wrap(list(replicas))
        size = Math.MAX(replicas.size)
        current_zones = list(set([s.zone for s in replicas if s.status == "STARTED"]))
        if "spot" not in current_zones:
            # WE CAN ASSIGN THIS REPLICA TO spot
            for s in replicas:
                if s.status == "UNASSIGNED":
                    s.size = size
                    low_risk_shards.append(s)
                    break  # ONLY NEED ONE

    if low_risk_shards:
        Log.note("{{num}} low risk shards found", num=len(low_risk_shards))

        allocate(CONCURRENT, low_risk_shards, relocating, path, nodes, {"spot"}, shards)
        return
    else:
        Log.note("No low risk shards found")


def net_shards_to_move(concurrent, shards, relocating):
    sorted_shards = jx.sort(shards, ["index_size", "size"])
    total_size = 0
    for s in sorted_shards:
        if total_size > BIG_SHARD_SIZE:
            break
        concurrent += 1
        total_size += s.size
    concurrent = max(concurrent, CONCURRENT)
    net = concurrent - len(relocating)
    return net, sorted_shards


def allocate(concurrent, proposed_shards, relocating, path, nodes, zones, all_shards):
    net, shards = net_shards_to_move(concurrent, proposed_shards, relocating)
    if net <= 0:
        Log.note("Delay work, cluster busy RELOCATING/INITIALIZING {{num}} shards", num=len(relocating))
        return

    for shard in shards:
        if net <= 0:
            break
        # DIVIDE EACH NODE MEMORY BY NUMBER OF SHARDS FROM THIS INDEX (ASSUME ZERO SHARDS ASSIGNED TO EACH NODE)
        node_weight = {n.name: n.memory * 4 ** (Math.floor(shard.siblings / n.siblings + 0.9)-1) if n.memory else 0 for n in nodes}
        shards_for_this_index = wrap(jx.filter(all_shards, {
            "eq": {
                "index": shard.index
            }
        }))
        index_size = Math.sum(shards_for_this_index.size)
        for g, ss in jx.groupby(filter(lambda s: s.status == "STARTED" and s.node, shards_for_this_index), "node"):
            ss = wrap(list(ss))
            index_count = len(ss)
            node_weight[g.node] = nodes[g.node].memory * (1 - Math.sum(ss.size)/index_size)
            max_allowed = Math.ceiling(shard.siblings/nodes[g.node].siblings)
            node_weight[g.node] *= 4 ** (max_allowed - index_count - 1)

        list_nodes = list(nodes)
        while True:
            i = Random.weight([node_weight[n.name] if n.zone in zones else 0 for n in list_nodes])
            destination_node = list_nodes[i].name
            for s in all_shards:
                if s.index == shard.index and s.i == shard.i and s.node == destination_node:
                    Log.note("Shard {{shard.index}}:{{shard.i}} already on node {{node}}", shard=shard, node=destination_node)
                    break
            else:
                break

        if shard.status == "UNASSIGNED":
            # destination_node = "secondary"
            command = wrap({"allocate": {
                "index": shard.index,
                "shard": shard.i,
                "node": destination_node,  # nodes[i].name,
                "allow_primary": True
            }})
        else:
            command = wrap({"move":
                {
                    "index": shard.index,
                    "shard": shard.i,
                    "from_node": shard.node,
                    "to_node": destination_node
                }
            })

        result = convert.json2value(
            convert.utf82unicode(http.post(path + "/_cluster/reroute", json={"commands": [command]}).content))
        if not result.acknowledged:
            Log.warning("Can not move/allocate to {{node}}: Error={{error|quote}}", node=destination_node, error=result.error)
        else:
            net -= 1
            Log.note(
                "index={{shard.index}}, shard={{shard.i}}, assign_to={{node}}, ok={{result.acknowledged}}",
                shard=shard,
                result=result,
                node=destination_node
            )

def balance_multiplier(shard_count, node_count):
    return 10 ** (Math.floor(shard_count / node_count + 0.9)-1)


def convert_table_to_list(table, column_names):
    lines = [l for l in table.split("\n") if l.strip()]

    # FIND THE COLUMNS WITH JUST SPACES
    columns = []
    for i, c in enumerate(zip(*lines)):
        if all(r == " " for r in c):
            columns.append(i)

    for i, row in enumerate(lines):
        yield wrap({c: r for c, r in zip(column_names, split_at(row, columns))})


def split_at(row, columns):
    output = []
    last = 0
    for c in columns:
        output.append(row[last:c].strip())
        last = c
    output.append(row[last:].strip())
    return output


def text_to_bytes(size):
    if size == "":
        return 0

    multiplier = {
        "kb": 1000,
        "mb": 1000000,
        "gb": 1000000000
    }.get(size[-2:])
    if not multiplier:
        multiplier = 1
        if size[-1]=="b":
            size = size[:-1]
    else:
        size = size[:-2]
    try:
        return float(size) * float(multiplier)
    except Exception, e:
        Log.error("not expected", cause=e)


def main():
    settings = startup.read_settings()
    Log.start(settings.debug)

    constants.set(settings.constants)
    path = settings.elasticsearch.host + ":" + unicode(settings.elasticsearch.port)

    try:
        response = http.put(
            path + "/_cluster/settings",
            data='{"persistent": {"cluster.routing.allocation.enable": "none"}}'
        )
        Log.note("DISABLE SHARD MOVEMENT: {{result}}", result=response.all_content)

        response = http.put(
            path + "/_cluster/settings",
            data='{"transient": {"cluster.routing.allocation.disk.watermark.low": "95%"}}'
        )
        Log.note("ALLOW ALLOCATION: {{result}}", result=response.all_content)

        please_stop = Signal()
        def loop(please_stop):
            while not please_stop:
                assign_shards(settings)
                Thread.sleep(seconds=30, please_stop=please_stop)

        Thread.run("loop", loop, please_stop=please_stop)
        Thread.wait_for_shutdown_signal(please_stop=please_stop, allow_exit=True)
    except Exception, e:
        Log.error("Problem with assign of shards", e)
    finally:
        response = http.put(
            path + "/_cluster/settings",
            data='{"persistent": {"cluster.routing.allocation.enable": "all"}}'
        )
        Log.note("ENABLE SHARD MOVEMENT: {{result}}", result=response.all_content)

        response = http.put(
            path + "/_cluster/settings",
            data='{"transient": {"cluster.routing.allocation.disk.watermark.low": "80%"}}'
        )
        Log.note("RESTRICT ALLOCATION: {{result}}", result=response.all_content)
        Log.stop()


if __name__ == "__main__":
    main()
