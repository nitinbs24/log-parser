# Data card

Train lines dropped because their template also occurs in val/test: 6

## train
594 lines, 378 templates, tokens p50/p95/max: 7/15/46

| system | lines | templates |
|---|---|---|
| Apache | 10 | 4 |
| BGL | 120 | 76 |
| HDFS | 24 | 9 |
| HPC | 56 | 29 |
| Hadoop | 113 | 72 |
| HealthApp | 65 | 47 |
| Linux | 84 | 71 |
| OpenSSH | 36 | 16 |
| Spark | 33 | 23 |
| Zookeeper | 53 | 31 |

Top-10 templates:

- 3 × `BLOCK* NameSystem.delete: <*> is added to invalidSet of <*>:<*>`
- 3 × `jk2_init() Found child <*> in scoreboard slot <*>`
- 3 × `<*>:<*> Served block <*> to <*>`
- 3 × `Closed socket connection for client <*>:<*> which had sessionid <*>`
- 3 × `onExtend:<*> <*> <*> <*>`
- 3 × `CE sym <*>, at <*>, mask <*>`
- 3 × `JVM with ID: <*> given task: <*>`
- 3 × `Received connection request <*>:<*>`
- 3 × `Failed password for invalid user <*> from <*> port <*> ssh2`
- 3 × `Started reading broadcast variable <*>`

## val
200 lines, 12 templates, tokens p50/p95/max: 2/8/105

| system | lines | templates |
|---|---|---|
| BGL | 129 | 1 |
| HDFS | 1 | 1 |
| HPC | 9 | 3 |
| Hadoop | 4 | 3 |
| HealthApp | 1 | 1 |
| Linux | 1 | 1 |
| Spark | 55 | 2 |

Top-10 templates:

- 129 × `generating core.<*>`
- 49 × `Running task <*> in stage <*> (TID <*>)`
- 6 × `Reading broadcast variable <*> took <*> ms`
- 6 × `NIFF: node node-<*> has detected an available network connection on network <*> via interface alt0`
- 2 × `ambient=<*>`
- 2 × `Diagnostics report from <*>: Error: java.net.NoRouteToHostException: No Route to Host from MININT-<*>/<*> to <*>:<*> failed on socket timeout exception: java.net.NoRouteToHostException: No route to host: no further information; For more details see: http://wiki.apache.org/hadoop/NoRouteToHost`
- 1 × `<*> TaskAttempt Transitioned from ASSIGNED to RUNNING`
- 1 × `BLOCK* ask <*>:<*> to delete <*>`
- 1 × `Command has completed successfully`
- 1 × `InsertCallBack() onSuccess type = <*> data=<*>`

## test_heldout
4128 lines, 541 templates, tokens p50/p95/max: 10/18/123

| system | lines | templates |
|---|---|---|
| Mac | 1185 | 341 |
| OpenStack | 1548 | 43 |
| Proxifier | 1056 | 8 |
| Thunderbird | 339 | 149 |

Top-10 templates:

- 930 × `<*> "GET <*>" status: <*> len: <*> time: <*>`
- 789 × `<*> close, <*> <*>, <*> <*>, lifetime <*>`
- 214 × `<*>:<*> open through proxy <*>:<*> HTTPS`
- 162 × `com.apple.<*>: scheduler_evaluate_activity told me to run this job; however, but the start time isn't for <*> seconds. Ignoring.`
- 71 × `Cocoa scripting error for '<*>': four character codes must be four characters long.`
- 64 × `<*> "POST <*>" status: <*> len: <*> time: <*>`
- 33 × `Warning: we failed to resolve data source name <*>`
- 31 × `CCFile::captureLogRun Skipping current file Dir file [<*>-<*>-<*>,<*>,<*>]-<*>, Current File [<*>-<*>-<*>,<*>,<*>]-<*>`
- 28 × `ARPT: <*>: wl0: MDNS: IPV6 Addr: <*>`
- 28 × `data_thread() got not answer from any [<*>] datasource`

## test_template_disjoint
2480 lines, 182 templates, tokens p50/p95/max: 7/14/75

| system | lines | templates |
|---|---|---|
| Apache | 33 | 2 |
| BGL | 182 | 36 |
| HDFS | 627 | 4 |
| HPC | 61 | 14 |
| Hadoop | 83 | 34 |
| HealthApp | 626 | 23 |
| Linux | 38 | 35 |
| OpenSSH | 156 | 8 |
| Spark | 589 | 11 |
| Zookeeper | 85 | 15 |

Top-10 templates:

- 314 × `BLOCK* NameSystem.addStoredBlock: blockMap updated: <*>:<*> is added to <*> size <*>`
- 300 × `Finished task <*> in stage <*> (TID <*>). <*> bytes result sent to driver`
- 292 × `Receiving block <*> src: <*>:<*> dest: <*>:<*>`
- 241 × `getTodayTotalDetailSteps = <*>##<*>##<*>##<*>##<*>##<*>`
- 241 × `setTodayTotalDetailSteps=<*>`
- 118 × `calculateCaloriesWithCache totalCalories=<*>`
- 112 × `Block <*> stored as bytes in memory (estimated size <*>, free <*>)`
- 77 × `Invalid user <*> from <*>`
- 75 × `Found block <*> locally`
- 66 × `<*> double-hummer alignment exceptions`
