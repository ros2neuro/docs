// EXAMPLE, NOT TESTED. This code has not been run in Unity or on a headset: it is a possible way to do it,
// written from the rosbridge protocol and the NativeWebSocket API. Expect to adapt it.
//
// Connects to a rosbridge WebSocket server and subscribes to the two things a ROS2neuro feedback hears:
//   the flow of control_feedback (ros2neuro_msgs/msg/NeuroControl): the values and the thresholds
//   the event bus /neuroevent (ros2neuro_msgs/msg/NeuroEvent): the phases of the trial
// and raises a C# event for every message of each.
//
// Needs the package NativeWebSocket (Package Manager > Add package from git URL):
//   https://github.com/endel/NativeWebSocket.git#upm
using System;
using System.Text;
using UnityEngine;
using NativeWebSocket;

// The part of ros2neuro_msgs/msg/NeuroControl that the feedback needs. JsonUtility ignores the other fields.
[Serializable]
public class NeuroControlMsg
{
    public string[] fields;      // the class codes ("773", "771"), then "threshold:773", "threshold:771"
    public float[] values;       // the normalized value of each class, then the thresholds in force: same order as fields
}

// The part of ros2neuro_msgs/msg/NeuroEvent that the feedback needs.
[Serializable]
public class NeuroEventMsg
{
    public int event_id;         // 786 fixation, the class code (cue), 897 / 898 / 899 outcome, and each + 32768 when it ends
}

[Serializable]
class RosbridgeHeader            // the start of every message: {"op": "publish", "topic": "...", "msg": {...}}
{
    public string op;
    public string topic;
}

[Serializable]
class FlowEnvelope { public string op; public string topic; public NeuroControlMsg msg; }

[Serializable]
class EventEnvelope { public string op; public string topic; public NeuroEventMsg msg; }

[Serializable]
class RosbridgeSubscribe         // {"op": "subscribe", "topic": "...", "type": "..."}
{
    public string op = "subscribe";
    public string topic;
    public string type;
}

public class RosbridgeClient : MonoBehaviour
{
    public string url = "ws://localhost:9090";
    public string topic = "/control_feedback/probabilities";
    public string eventTopic = "/neuroevent";

    // Raised on the main thread, once per message.
    public event Action<NeuroControlMsg> OnFlow;
    public event Action<NeuroEventMsg> OnEvent;

    WebSocket ws;

    async void Start()
    {
        ws = new WebSocket(url);

        ws.OnOpen += () =>
        {
            Debug.Log($"rosbridge: connected to {url}");
            ws.SendText(JsonUtility.ToJson(new RosbridgeSubscribe { topic = topic, type = "ros2neuro_msgs/msg/NeuroControl" }));
            ws.SendText(JsonUtility.ToJson(new RosbridgeSubscribe { topic = eventTopic, type = "ros2neuro_msgs/msg/NeuroEvent" }));
        };

        ws.OnMessage += bytes =>
        {
            // JsonUtility cannot read a "msg" of two different types: read the topic first, then the right envelope
            var text = Encoding.UTF8.GetString(bytes);
            var head = JsonUtility.FromJson<RosbridgeHeader>(text);
            if (head == null || head.op != "publish") return;
            if (head.topic == topic)
            {
                var flow = JsonUtility.FromJson<FlowEnvelope>(text);
                if (flow?.msg != null) OnFlow?.Invoke(flow.msg);
            }
            else if (head.topic == eventTopic)
            {
                var ev = JsonUtility.FromJson<EventEnvelope>(text);
                if (ev?.msg != null) OnEvent?.Invoke(ev.msg);
            }
        };

        ws.OnError += error => Debug.LogWarning($"rosbridge error: {error}");
        ws.OnClose += code => Debug.Log($"rosbridge closed: {code}");

        await ws.Connect();
    }

    void Update()
    {
        // NativeWebSocket queues the messages: hand them to Unity on the main thread
#if !UNITY_WEBGL || UNITY_EDITOR
        ws?.DispatchMessageQueue();
#endif
    }

    async void OnDestroy()
    {
        if (ws != null) await ws.Close();
    }
}
