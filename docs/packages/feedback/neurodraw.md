# neurodraw

!!! info ""
    Package: [`neurodraw`](https://github.com/neurorobotics-iaslab/neurodraw) · used by the [Wheel](wheel.md) and [Bar](bar.md) feedback plugins · part of [Feedback](index.md)

neurodraw is the library that draws the feedback windows of ROS2neuro. It is **required** by the two feedback plugins, `ros2neuro_feedback_wheel` and `ros2neuro_feedback_bar`, and by nothing else in the stack. It is not a ROS package: it is a plain CMake library, found by the plugins with `find_package(neurodraw CONFIG REQUIRED)`. How the feedback uses it is explained in [Feedback](index.md#neurodraw-the-drawing-library-required).

NeuroDraw is a compact C++ graphics library for 2D neurofeedback and BCI-style visual interfaces. It is built on SDL2, OpenGL, SDL2_ttf, and SDL2_image, and provides:

- primitive shapes with transforms and styling
- text and image drawables
- a `Window` abstraction with input callbacks
- a threaded `Engine` for continuous rendering
- scene composition with `Group` and `Layer`
- simple time-based animations with `Tween`
- a companion `neurochrono` utility library with `Timer` and `Rate`

## Dependencies
On Ubuntu:

```bash
sudo apt-get install libsdl2-dev
sudo apt-get install libsdl2-image-dev
sudo apt-get install libsdl2-ttf-dev
```

## Build

```bash
git clone https://github.com/neurorobotics-iaslab/neurodraw.git
cd neurodraw
cmake -S . -B build
cmake --build build
```

To disable the examples:

```bash
cmake -S . -B build -DNEURODRAW_BUILD_EXAMPLES=OFF
```

## Test

```bash
ctest --test-dir build --output-on-failure
```

The test suite currently covers:

- shape geometry and transforms
- hit testing and grouping
- tween progression
- text and image layout metrics
- `neurochrono` timing utilities
- a CMake package-consumer smoke test

## Install

```bash
cmake -S . -B build
cmake --build build
sudo cmake --install build
```

Custom prefix:

```bash
cmake -S . -B build -DCMAKE_INSTALL_PREFIX=$HOME/Local
cmake --build build
cmake --install build
```

## Using From Another CMake Project

NeuroDraw exports a proper CMake package and can be consumed with `find_package(neurodraw CONFIG REQUIRED)`.

```cmake
find_package(neurodraw CONFIG REQUIRED)

add_executable(my_app main.cpp)
target_link_libraries(my_app PRIVATE neurodraw::neurodraw neurodraw::neurochrono)
```

To consume the package directly from a build tree:

```bash
cmake -S consumer -B consumer-build -Dneurodraw_DIR=/path/to/neurodraw/build/cmake
cmake --build consumer-build
```

## Examples

The repository includes six example applications:

```bash
./build/example_feature_showcase
./build/example_engine_showcase
./build/example_gallery
./build/example_text_showcase
./build/example_image_showcase
./build/example_scene_showcase
```

Example sources live in `examples/`.

- `example_feature_showcase`: fill/stroke styling, alpha, stroke width, transforms, and direct `Window` usage
- `example_engine_showcase`: threaded `Engine` usage and interactive scene updates
- `example_gallery`: compact visual overview of the main primitives
- `example_text_showcase`: text alignment, wrapping, multiline text, and font rendering
- `example_image_showcase`: image loading (`png`, `jpg`, `gif`, `bmp`, `ppm`) plus `contain` / `cover` / `stretch`
- `example_scene_showcase`: `Group`, `Layer`, `Tween`, and hit testing together

## API Overview

### Coordinate system
The origin `(0, 0)` is at the center of the window. The smallest visible dimension is mapped to `[-1, 1]`, so content placed inside the box `(-1, -1)` to `(1, 1)` always fits on screen.

### Colors
`Color` values in `Palette` use 0-255 RGB channels. Alpha is managed separately via `set_alpha`, `set_fill_alpha`, and `set_stroke_alpha`.

### Core drawables
The main drawable classes are:

- `Line`
- `Triangle`
- `Rectangle`
- `Cross`
- `Arrow`
- `RegularShape`
- `Circle`
- `Arc`
- `Ring`
- `Text`
- `Image`
- `Group`
- `Layer`

### Shape
`Shape` is the common base class for all drawables. Key capabilities:

- transforms: `move`, `relmove`, `rotate`, `relrotate`
- visibility/opacity: `show`, `hide`, `set_alpha`
- styling: `set_fill_color`, `set_stroke_color`, `set_stroke_width`
- bounds and hit testing: `bounds`, `contains`, `hit`

### Text
`Text` supports:

- custom font path and size
- horizontal and vertical alignment
- wrap width in pixels
- multiline layout
- line spacing
- `width`, `height`, and bounds queries

### Image
`Image` supports:

- loading from file
- `png`, `jpg`, `gif`, `bmp`, and `ppm`
- alpha control
- explicit size via `set_width`, `set_height`, `set_size`
- fit modes: `Contain`, `Cover`, `Stretch`
- alignment and bounds queries

### Window
`Window` handles:

- creation and close
- buffer swap
- background color
- event polling
- callbacks: `on_quit`, `on_redraw`, `on_keyboard`, `on_mouse`

### Engine
`Engine` provides a threaded render loop with:

- `add`, `erase`, `clear`
- `mouse_to_world`
- `hit`
- `add_tween`, `clear_tweens`, `tween_count`
- keyboard and mouse callback forwarding

### Tween
`Tween` animates one property of a shape over time:

- properties: `X`, `Y`, `Rotation`, `Alpha`
- easing: `Linear`, `EaseIn`, `EaseOut`, `EaseInOut`

### neurochrono
The companion `neurochrono` library currently provides:

- `Timer<unit>` and aliases such as `timer_msecs`
- `Rate`, a ROS-style fixed-rate sleep helper

## Notes

- Rendering still uses legacy OpenGL for now.
- Hit testing is currently bounding-box based, which is good for layout and interaction scaffolding but not yet exact for all non-rectangular primitives.
