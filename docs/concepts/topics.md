# Topics and services

The names below are the **defaults** of each node. Launch files remap them, so the real names depend on the
node name you give: a node called `acquisition` publishes `~/neurodata` as `/acquisition/neurodata`.

```mermaid
flowchart LR
    ACQ[acquisition] -->|"/acquisition/neurodata"| FIL[filters]
    FIL -->|"/processing/filtered"| WEL[welch]
    WEL -->|"/processing/psd"| DEC[decoder]
    DEC -->|"/classification/prediction"| INT[integrator]
    INT -->|"/integrated/raw"| MAN[manager]
    MAN -->|"/manager_control/probabilities"| FB[feedback]
    MAN -->|"/neuroevent"| REC[recorder]
    MAN -.->|"reset service"| INT
    ACQ -->|"neurodata and neurodata_info"| REC
    ACQ --> VIZ[visualizer]
```

The diagram uses the remaps of the `ros2neuro_devel_test` launchers.

## Topics

| Node | Direction | Default topic | Type | Purpose |
|---|---|---|---|---|
| acquisition | publishes | `~/neurodata` | `NeuroFrame` | raw samples |
| acquisition | publishes | `~/neurodata_info` | `NeuroFrameInfo` | stream metadata (`transient_local`) |
| filter chain | subscribes | `/neurodata` | `NeuroFrame` | signal to filter |
| filter chain | publishes | `~/filtered` | `NeuroFrame` | filtered signal |
| FFT / Welch / spectrogram | subscribes | `/neurodata` | `NeuroFrame` | signal to analyse |
| FFT | publishes | `~/fft` | `NeuroFeature` | spectrum |
| Welch | publishes | `~/psd` | `NeuroFeature` | power spectral density |
| spectrogram | publishes | `~/spectrogram` | `NeuroFeature` | time-frequency map |
| decoder | subscribes | `/features` | `NeuroFeature` | feature to classify |
| decoder | publishes | `~/prediction` | `NeuroPrediction` | class values |
| integrator | subscribes | `/prediction` (`input_topic`) | `NeuroPrediction` | decoder output |
| integrator | publishes | `~/control` (`output_topic`) | `NeuroControl` | integrated values |
| integrator | subscribes | `/neuroevent` (`event_topic`) | `NeuroEvent` | optional reset on an event |
| manager | subscribes | `/integrated/raw` (`integrated_topic`) | `NeuroControl` | integrator output |
| manager | publishes | `/manager_control/probabilities` (`control_topic`) | `NeuroControl` | flow for the feedback |
| manager | publishes | `/neuroevent` (`event_topic`) | `NeuroEvent` | trial events |
| manager (Training plugin) | publishes | `/protocol_ended` | `std_msgs/Empty` | end of the protocol (`transient_local`) |
| feedback | subscribes | `/manager_control/probabilities` (`control_topic`) | `NeuroControl` | what to draw |
| feedback | publishes | `/neuroevent` | `NeuroEvent` | display events, only with `publish_display_events` |
| recorder | subscribes | `/neurodata`, `/neurodata_info`, `/neuroevent` | `NeuroFrame`, `NeuroFrameInfo`, `NeuroEvent` | what to write |
| visualizer | subscribes | `/acquisition/neurodata` (selectable) | `NeuroFrame` | scope |

!!! note "Defaults vs launch files"
    The integrator defaults (`/prediction`, `~/control`) differ from the topics used in the test launchers
    (`/classification/prediction`, `/integrated/raw`), which set them through parameters. Always check
    `ros2 topic list` and `ros2 node info` on a running system.

## Services

| Node | Service | Type | Purpose |
|---|---|---|---|
| acquisition | `~/start`, `~/stop`, `~/quit` | `std_srvs/Empty` | control the device |
| integrator | `reset` (relative name, so `/reset`) | `std_srvs/Empty` | reset the integrated values to 1/K |
| manager | client of the integrator reset (`reset_service`, default `/integrator/reset`) | `std_srvs/Empty` | ask for a reset |

The launchers pass `reset_service:=/reset`.

## Useful commands

```bash
ros2 topic list -t                      # topics and their types
ros2 topic hz /acquisition/neurodata    # frame rate
ros2 topic echo /neuroevent             # watch the events
ros2 node info /manager                 # publishers, subscribers, services of a node
ros2 param list /filters                # parameters of a node
```
