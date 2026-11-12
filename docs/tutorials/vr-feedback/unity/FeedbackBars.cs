// EXAMPLE, NOT TESTED. This code has not been run in Unity or on a headset: it is a possible way to do it.
//
// Draws the ROS2neuro feedback as one bar per class, like ros2neuro_feedback_bar and the WebXR page of this
// tutorial. It only RECEIVES: the VR is passive.
//
//   the flow (RosbridgeClient.OnFlow):
//     fields / values       -> the class codes and their values: the height of each bar
//                              then "threshold:<code>" and the thresholds in force: the white line of each bar
//   the event bus (RosbridgeClient.OnEvent):
//     786 fixation (cross), the class code (cue), 897 Hit, 898 Miss, 899 Timeout, and each + 32768 when it ends
//
// Setup: an empty GameObject with RosbridgeClient and FeedbackBars; drag the client in "client".
// The scene must have a light and a camera (or an XR rig). "thresholds" is only what the lines have until the flow
// brings the real ones (they follow ros2 param set /control thresholds).
using System.Collections.Generic;
using UnityEngine;

public class FeedbackBars : MonoBehaviour
{
    public RosbridgeClient client;
    public float[] thresholds = { 0.7f, 0.7f };
    public float barHeight = 1.5f;
    public float barWidth = 0.35f;
    public float gap = 0.25f;

    const int Fixation = 786, Hit = 897, Miss = 898, Timeout = 899, Off = 32768, Shown = 16384, Rest = 783;

    // a class is colored by its POSITION in the list, never by its code (the rest is yellow)
    static readonly Color[] Palette =
    {
        new Color(0.25f, 0.41f, 0.88f), new Color(0.70f, 0.13f, 0.13f), new Color(0.13f, 0.55f, 0.13f),
        new Color(0.58f, 0.44f, 0.86f), new Color(1.00f, 0.08f, 0.58f)
    };
    static readonly Color RestColor = new Color(1f, 0.83f, 0f);

    string[] fields;
    readonly List<Transform> bars = new List<Transform>();
    readonly List<Transform> lines = new List<Transform>();
    readonly List<Color> colors = new List<Color>();
    float[] current;                       // the threshold of each bar in force
    GameObject cross, cue;
    TextMesh outcomeLabel;

    void OnEnable()  { if (client != null) { client.OnFlow += HandleFlow; client.OnEvent += HandleEvent; } }
    void OnDisable() { if (client != null) { client.OnFlow -= HandleFlow; client.OnEvent -= HandleEvent; } }

    // the flow: the class codes first, then "threshold:<code>" for each of them
    void HandleFlow(NeuroControlMsg m)
    {
        if (m.fields == null || m.values == null) return;
        var codes = new List<string>();
        var thresholdOf = new Dictionary<string, float>();
        for (int i = 0; i < m.fields.Length && i < m.values.Length; i++)
        {
            if (m.fields[i].StartsWith("threshold:")) thresholdOf[m.fields[i].Substring("threshold:".Length)] = m.values[i];
            else codes.Add(m.fields[i]);
        }
        if (bars.Count == 0 && codes.Count > 0) Build(codes.ToArray());
        if (bars.Count == 0) return;

        for (int i = 0; i < bars.Count; i++)
        {
            int k = System.Array.IndexOf(m.fields, fields[i]);
            float v = Mathf.Clamp01(k >= 0 && k < m.values.Length ? m.values[k] : 0f);
            float h = Mathf.Max(0.01f, v * barHeight);
            var t = bars[i];
            t.localScale = new Vector3(barWidth * 0.9f, h, 0.1f);
            t.localPosition = new Vector3(t.localPosition.x, h / 2f, 0f);

            // the line follows the threshold in force
            if (thresholdOf.TryGetValue(fields[i], out float th)) current[i] = th;
            if (current[i] > 0f)
            {
                lines[i].gameObject.SetActive(true);
                lines[i].localPosition = new Vector3(lines[i].localPosition.x, current[i] * barHeight, -0.07f);
            }
        }
    }

    // the event bus: the phases of the trial (it does not matter that the events and the values are not in order)
    void HandleEvent(NeuroEventMsg m)
    {
        if (bars.Count == 0) return;
        int e = m.event_id;
        if (e == Hit || e == Miss || e == Timeout)
            outcomeLabel.text = e == Hit ? "Hit" : e == Miss ? "Miss" : "Timeout";
        else if (e - Off == Hit || e - Off == Miss || e - Off == Timeout) outcomeLabel.text = "";
        else if (e == Fixation) cross.SetActive(true);
        else if (e == Fixation + Off) cross.SetActive(false);
        else if (e >= Shown && e < Off) { /* "this was shown" (id + 16384) of a feedback: not a phase */ }
        else if (e >= Off) cue.SetActive(false);       // the end of the cue; the end of Start and CFeedback come here too and change nothing
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

    void Build(string[] f)
    {
        fields = f;
        current = new float[f.Length];
        for (int i = 0; i < f.Length; i++) current[i] = i < thresholds.Length ? thresholds[i] : 0f;
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

            // the threshold line: hidden until there is a threshold for this bar
            var line = GameObject.CreatePrimitive(PrimitiveType.Cube);
            line.transform.SetParent(transform, false);
            line.transform.localPosition = new Vector3(x, current[i] * barHeight, -0.07f);
            line.transform.localScale = new Vector3(barWidth * 1.25f, 0.02f, 0.02f);
            line.SetActive(current[i] > 0f);
            lines.Add(line.transform);
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
