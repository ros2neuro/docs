# ROS 2 essentials: nodes, topics and launch files

ROS2neuro is a set of ROS 2 nodes. Before you use it, you need a handful of ROS 2 ideas: **nodes**, **topics**,
**services**, **parameters** and **launch files**. This page explains them with a small example that comes with ROS 2, and
every command works in the same terminal you will use for the rest of the tutorials.

**Goal.** Start two nodes, see that they talk through a topic, call a service, read a parameter, and know which command to use for each.

**You need** ROS 2 Jazzy and ROS2neuro [installed](../../installation/index.md). No hardware, no code.

!!! note "Where do I type the commands?"
    In a terminal where ROS 2 is *sourced*. If you use the container of the [installation](../../installation/index.md) (Distrobox), enter it first:

    ```bash
    distrobox enter ros2neuro
    source /opt/ros/jazzy/setup.bash
    ```

    Every new terminal needs the `source` line again. If you built a workspace, also `source install/setup.bash`.

## 1. The five ideas

| Idea | What it is | In ROS2neuro |
|---|---|---|
| **Node** | a program that does one thing | `acquisition`, `filters`, `decoder`, ... |
| **Topic** | a named channel on which a node *publishes* messages and others *subscribe* | `/acquisition/neurodata`, `/neuroevent` |
| **Message** | the type of what travels on a topic | `NeuroFrame`, `NeuroEvent`, ... ([messages](../../concepts/messages.md)) |
| **Service** | a question with an answer: a node asks, another replies | `/reset` of the integrator |
| **Parameter** | a setting of a node, with a name and a value | `acquisition.framerate`, `cutoff` of a filter |

The idea of ROS2neuro is that each stage of the BCI is a node and the nodes are chained **only** by topics. You can
replace the node of a stage, or add a new one that listens to the same topic, without touching the others
(see the [architecture](../../concepts/architecture.md)).

!!! info "No `roscore` in ROS 2"
    In ROS 1 you started a master (`roscore`) first. ROS 2 has no master: nodes find each other by themselves, so you just start them.

## 2. Start two nodes

Open **two terminals**. In the first one start a node that publishes a message every second:

```bash
ros2 run demo_nodes_cpp talker
```

```text
[INFO] [1795525058.286604749] [talker]: Publishing: 'Hello World: 1'
[INFO] [1795525059.286685617] [talker]: Publishing: 'Hello World: 2'
```

`ros2 run <package> <executable>` starts one node. In the second terminal start a node that listens:

```bash
ros2 run demo_nodes_cpp listener
```

```text
[INFO] [1795525894.993229185] [listener]: I heard: [Hello World: 1]
```

Stop each node with **Ctrl+C**. Leave the talker running for the next steps.

## 3. Look at the graph

In a new terminal ask ROS 2 what is running:

```bash
ros2 node list      # the nodes
ros2 topic list     # the topics
```

```text
/talker
/chatter
/parameter_events
/rosout
```

`/chatter` is the topic of the talker. Two topics are always there: `/rosout` (the log of every node) and
`/parameter_events` (a parameter changed). Ask for the type and listen to it:

```bash
ros2 topic list -t                  # topics with their message type
ros2 topic echo /chatter            # print every message
ros2 topic hz /chatter              # how many messages per second
ros2 interface show std_msgs/msg/String   # the fields of the message
```

!!! tip "The four commands you will use all the time"
    `ros2 node list`, `ros2 topic list -t`, `ros2 topic echo <topic>` and `ros2 topic hz <topic>`: they are how you check
    that a pipeline is alive. With ROS2neuro you add `--field <name>` to `echo` to print one field of a long
    message, for example `ros2 topic echo /neuroevent --field event_id`.

## 4. A service

Start another node, this one offers a service that adds two integers:

```bash
ros2 run demo_nodes_cpp add_two_ints_server
```

```bash
ros2 service list -t
ros2 service call /add_two_ints example_interfaces/srv/AddTwoInts "{a: 2, b: 3}"
```

```text
/add_two_ints [example_interfaces/srv/AddTwoInts]
...
response:
example_interfaces.srv.AddTwoInts_Response(sum=5)
```

A service call waits for the reply. In ROS2neuro they are used for the commands: `/reset` empties the integrator,
`~/start` and `~/stop` control the acquisition.

## 5. Parameters

Every node has parameters. List the ones of the talker and read one:

```bash
ros2 param list /talker
ros2 param get /talker use_sim_time
```

```text
Boolean value is: False
```

You change a parameter when you start a node, with `--ros-args -p name:=value`, or with a **YAML file**, which is how ROS2neuro
is configured (all the parameters of a node are in one file):

```bash
ros2 run demo_nodes_cpp talker --ros-args -p use_sim_time:=false
ros2 run my_package my_node --ros-args --params-file my_config.yaml
```

```yaml
my_node:                # the name of the node
  ros__parameters:
    threshold: 0.7
    channel: 9
```

!!! warning "The section of the YAML is the name of the node"
    A parameter file is read by the node whose **name** is the first line of its section. If you start a node with another name
    (`-r __node:=other`, or `name="other"` in a launch file) it will not find its parameters. This is the most common reason for
    "my parameters are ignored".

## 6. Launch files: many nodes, one command

A real pipeline has many nodes. Typing a `ros2 run` for each one is tedious, so a **launch file** lists them. It is
written in Python (`.launch.py`), XML or YAML. This one starts the talker and the listener:

```xml
<launch>
  <node pkg="demo_nodes_cpp" exec="talker" name="talker" output="screen"/>
  <node pkg="demo_nodes_cpp" exec="listener" name="listener" output="screen"/>
</launch>
```

```bash
ros2 launch my_package my_launch.launch.xml
ros2 launch my_package my_launch.launch.xml some_argument:=value
```

`ros2 launch <package> <file>` finds the file in the installed package. Ctrl+C stops all the nodes together. The [next tutorial](../publisher-subscriber/index.md)
writes the talker and the listener and starts them with a launch file of its own; the ones after it use launch files to start the acquisition, the filters and the
visualizer.

## What you learned

| To... | Command |
|---|---|
| start a node | `ros2 run <package> <executable>` |
| start many nodes | `ros2 launch <package> <file>` |
| see the nodes, the topics | `ros2 node list`, `ros2 topic list -t` |
| look at the messages | `ros2 topic echo <topic>`, `ros2 topic hz <topic>` |
| call a service | `ros2 service call <service> <type> "<values>"` |
| read or set a parameter | `ros2 param get <node> <name>`, `--ros-args -p name:=value` |

Next: [Your first publisher and subscriber](../publisher-subscriber/index.md).
