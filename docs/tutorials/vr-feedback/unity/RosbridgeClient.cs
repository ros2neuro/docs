// EXAMPLE, NOT TESTED. This code has not been run in Unity or on a headset: it is a possible way to do it,
// written from the rosbridge protocol and the NativeWebSocket API. Expect to adapt it.
//
// Connects to a rosbridge WebSocket server, subscribes to the flow that the ROS2neuro manager sends to the
// feedback (ros2neuro_msgs/msg/NeuroControl) and raises an event for every message.
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
    public string[] fields;      // class codes as strings, e.g. "773", "771"
    public float[] values;       // normalized value of each class, same order as fields
    public string[] actions;     // "seq", "event" or "outcome"
    public int[] commands;       // value of each action
}

[Serializable]
class RosbridgeEnvelope          // {"op": "publish", "topic": "...", "msg": {...}}
{
    public string op;
    public string topic;
    public NeuroControlMsg msg;
}

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
    public string topic = "/manager_control/probabilities";

    // Raised on the main thread, once per message of the flow.
    public event Action<NeuroControlMsg> OnFlow;

    WebSocket ws;

    async void Start()
    {
        ws = new WebSocket(url);

        ws.OnOpen += () =>
        {
            Debug.Log($"rosbridge: connected to {url}");
            var request = new RosbridgeSubscribe { topic = topic, type = "ros2neuro_msgs/msg/NeuroControl" };
            ws.SendText(JsonUtility.ToJson(request));
        };

        ws.OnMessage += bytes =>
        {
            var envelope = JsonUtility.FromJson<RosbridgeEnvelope>(Encoding.UTF8.GetString(bytes));
            if (envelope != null && envelope.op == "publish" && envelope.msg != null)
                OnFlow?.Invoke(envelope.msg);
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
