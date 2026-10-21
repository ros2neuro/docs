// EXAMPLE, NOT TESTED. This code has not been run in Unity or on a headset: it is a possible way to do it.
//
// Draws the ROS2neuro feedback as one bar per class, like ros2neuro_feedback_bar and the WebXR page of this
// tutorial. It only RECEIVES: the VR is passive.
//
//   fields / values       -> height of each bar
//   actions / commands:
//     "event"             -> fixation 786 (cross), the cue (the class code), and their "Off" (+32768)
//     "outcome"           -> 897 Hit, 898 Miss, 899 Timeout
//
// Setup: an empty GameObject with RosbridgeClient and FeedbackBars; drag the client in "client".
// The scene must have a light and a camera (or an XR rig). The thresholds are not in the flow: set them here,
// in the order of the bars.
using System.Collections.Generic;
using UnityEngine;

public class FeedbackBars : MonoBehaviour
{
    public RosbridgeClient client;
    public float[] thresholds = { 0.7f, 0.7f };
    public float barHeight = 1.5f;
    public float barWidth = 0.35f;
    public float gap = 0.25f;

    const int Fixation = 786, Hit = 897, Miss = 898, Timeout = 899, Off = 32768, Rest = 783;

    // a class is colored by its POSITION in the list, never by its code (the rest is yellow)
    static readonly Color[] Palette =
    {
        new Color(0.25f, 0.41f, 0.88f), new Color(0.70f, 0.13f, 0.13f), new Color(0.13f, 0.55f, 0.13f),
        new Color(0.58f, 0.44f, 0.86f), new Color(1.00f, 0.08f, 0.58f)
    };
    static readonly Color RestColor = new Color(1f, 0.83f, 0f);

    string[] fields;
    readonly List<Transform> bars = new List<Transform>();
    readonly List<Color> colors = new List<Color>();
    GameObject cross, cue;
    TextMesh outcomeLabel;

    void OnEnable() { if (client != null) client.OnFlow += Handle; }
    void OnDisable() { if (client != null) client.OnFlow -= Handle; }

    void Handle(NeuroControlMsg m)
    {
        if (bars.Count == 0 && m.fields != null && m.fields.Length > 0) Build(m.fields);
        if (bars.Count == 0) return;

        // 1. the values
        for (int i = 0; i < bars.Count; i++)
        {
            int k = System.Array.IndexOf(m.fields, fields[i]);
            float v = Mathf.Clamp01(k >= 0 ? m.values[k] : 0f);
            float h = Mathf.Max(0.01f, v * barHeight);
            var t = bars[i];
            t.localScale = new Vector3(barWidth * 0.9f, h, 0.1f);
            t.localPosition = new Vector3(t.localPosition.x, h / 2f, 0f);
        }

        // 2. the phases and the outcome
        var a = new Dictionary<string, int>();
        for (int i = 0; m.actions != null && i < m.actions.Length && i < m.commands.Length; i++)
            a[m.actions[i]] = m.commands[i];

        if (a.TryGetValue("outcome", out int outcome))
        {
            outcomeLabel.text = outcome == Hit ? "Hit" : outcome == Miss ? "Miss" : outcome == Timeout ? "Timeout" : "";
        }
        else if (a.TryGetValue("event", out int e))
        {
            if (e == Fixation) cross.SetActive(true);
            else if (e == Fixation + Off) cross.SetActive(false);
            else if (e - Off == Hit || e - Off == Miss || e - Off == Timeout) outcomeLabel.text = "";
            else if (e >= Off) cue.SetActive(false);
            else
            {
                int i = System.Array.IndexOf(fields, e.ToString());
                if (i >= 0 || e == Rest)
                {
                    cue.GetComponent<Renderer>().material.color = (e == Rest || i < 0) ? RestColor : colors[i];
                    cue.SetActive(true);
                }
            }
        }
    }

    void Build(string[] f)
    {
        fields = f;
        float span = f.Length * barWidth + (f.Length - 1) * gap;
        for (int i = 0; i < f.Length; i++)
        {
            float x = -span / 2f + barWidth / 2f + i * (barWidth + gap);
            var c = (f[i] == Rest.ToString()) ? RestColor : Palette[i % Palette.Length];
            colors.Add(c);

            var bar = GameObject.CreatePrimitive(PrimitiveType.Cube);
            bar.transform.SetParent(transform, false);
            bar.transform.localPosition = new Vector3(x, 0f, 0f);
            bar.GetComponent<Renderer>().material.color = c;
            bars.Add(bar.transform);

            if (i < thresholds.Length)      // the threshold line
            {
                var line = GameObject.CreatePrimitive(PrimitiveType.Cube);
                line.transform.SetParent(transform, false);
                line.transform.localPosition = new Vector3(x, thresholds[i] * barHeight, -0.07f);
                line.transform.localScale = new Vector3(barWidth * 1.25f, 0.02f, 0.02f);
            }
        }

        float top = barHeight + 0.35f;
        cross = new GameObject("cross");
        cross.transform.SetParent(transform, false);
        cross.transform.localPosition = new Vector3(0f, top, 0f);
        var crossText = cross.AddComponent<TextMesh>();
        crossText.text = "+"; crossText.fontSize = 120; crossText.characterSize = 0.05f;
        crossText.anchor = TextAnchor.MiddleCenter;
        cross.SetActive(false);

        cue = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        cue.transform.SetParent(transform, false);
        cue.transform.localPosition = new Vector3(0f, top, 0f);
        cue.transform.localScale = Vector3.one * 0.24f;
        cue.SetActive(false);

        var label = new GameObject("outcome");
        label.transform.SetParent(transform, false);
        label.transform.localPosition = new Vector3(0f, top + 0.45f, 0f);
        outcomeLabel = label.AddComponent<TextMesh>();
        outcomeLabel.fontSize = 100; outcomeLabel.characterSize = 0.05f;
        outcomeLabel.anchor = TextAnchor.MiddleCenter;
        outcomeLabel.text = "";
    }
}
