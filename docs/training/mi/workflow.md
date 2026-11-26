# The training workflow

The graphical trainer is organised as **seven tabs**, to be used from left to right. Behind them there is one pipeline, with the same order every time.

## The tabs

| # | Tab | What you do |
|---|---|---|
| 1 | **File** | choose the recordings and the event codes to ignore or discard |
| 2 | **Processing** | channels; temporal filters (DC, high-pass, low-pass, band-pass, resample; none active by default); spatial filters (CAR, small and large Laplacian, computed from the channel names on the 10-10 grid); normalisation (z-score, deep learning only) |
| 3 | **Epochs and split** | the classes, how the epochs are computed, and the assignment of every trial to train, validation, test or *exclude* (an automatic split is stratified by class, 75 / 15 / 10) |
| 4 | **Model** | the preset (machine learning or deep learning), the windowing, the features (a table: PSD, CSP, FBCSP, with their parameters) and the **selection of the features** on a score map, the model, the output folder and name |
| 5 | **Training** | the configuration of the chosen model (deep learning: epochs, optimizer, callbacks; machine learning: estimator parameters, grid, cross validation) and the **log** |
| 6 | **ERD/ERS + Fisher** | the event-related desynchronisation maps and the Fisher score of the data |
| 7 | **Metrics** | accuracy and the other metrics, the probabilities and the confusion matrix |

The order of the preprocessing is fixed: channels, DC, temporal filters, CAR, Laplacian, resample.

## What happens to the data

```text
continuous recordings
  -> preprocessing        pick channels, DC, causal filters, CAR, Laplacian, resample
  -> trial extraction     the label is the cue; the onset is the next CFeedback (781)
  -> split by trial       train / validation / test / exclude: a trial is never divided
  -> windows              dynamic duration, margins at onset and offset, shift (global or per class)
  -> transforms           z-score computed on the TRAIN windows only (deep learning)
  -> features + model     (machine learning) or network (deep learning)
  -> evaluation           per window, per trial, per run, per day
  -> model folder         manifest + model + the yaml of the nodes before the decoder
```

Three rules make the result trustworthy:

* **Trials are indivisible.** Every trial is identified by its recording, the sample of its cue and the cue code. The split is saved with those identifiers, so when you reload the files the trials that disappeared are removed and the new ones enter as *exclude*: nothing leaks from train to test.
* **Statistics come from the training set only.** The z-score uses the mean and the standard deviation of the train windows, never those of validation or test. For the machine-learning models the feature extractor, the selection and the model are redone **inside every fold** of the cross validation, on the training trials of that fold.
* **Filters are causal.** The interface offers only phases that exist online (forward for IIR filters, minimum phase for FIR): the library describes the preprocessing, but it does not keep the filter state online, so a non-causal filter of an old model loads with a warning.

## Real-time compatibility

What you train offline must be what runs online. The trainer therefore checks the choices against what the ROS 2 nodes do, and prints **warnings** (they do not stop the training) about what ROS 2 does not reproduce exactly:

* the DC filter of ROS 2 works **per frame** (one `NeuroFrame`), not on the whole recording;
* a single band-pass: ROS 2 uses a high-pass followed by a low-pass;
* the **large** Laplacian: the [Laplacian filter](../../packages/filters/laplacian.md) of ROS 2 uses the four adjacent electrodes, which is the small one;
* the resample.

With the small Laplacian, causal filters and the *frame online* windowing (windows of 1 s, shift of one frame) the features coincide with those of the Matlab trainer used before, to within rounding.

Next: [Models and outputs](models.md).
