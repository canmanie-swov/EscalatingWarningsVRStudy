# Escalating Warnings VR Study

Welcome to the code base for the VR study on escalating distraction warnings! This code runs on Windows, and some changes will be required (e.g. path format, use of `subprocess` library to open Carla executable) for it to run on different machines. To run this experiment, you must have [DReyeVR](https://github.com/HARPLab/DReyeVR) (and therefore also Carla and UNREAL4) installed and built. Please see [their documentation](https://github.com/HARPLab/DReyeVR/blob/main/Docs/Install.md) for more details. 

Important:
The assets in the zip file `UnrealAssets` contain physical changes we made to the vehicle in order to display a task on a screen added to the vehicle and also display an icon on the dashboard. These need to be integrated into the package in order to spawn everything correctly. Also, the `configs/DReyeVR.config` file has some changes we made such as the camera position initialization and inclusion of a flag to enable/disable manual takeover and can directly replace the default config.

## Running the experiment

`cd` to this directory and execute `python run_experiment.py`. The default condition will be the baseline; you can change this by adding the flag `--condition=escalating`. The options are `baseline`, `escalating`, and `non-escalating`.

The CarlaUE4 window needs to be the active window in order to send sound to the VR headset and to allow for steering wheel or pedal input.

### Disabling manual takeover

If you want to disable the ability for participants to take over control, edit the config file at `PACKAGE_LOCATION\WindowsNoEditor\CarlaUE4\Config\DReyeVRConfig.ini` and set `DisableControls` to `True`. This requires a restart of the CarlaUE4 simulator.

# FAQ

### I see `ModuleNotFoundError: No module named 'DReyeVR_utils'` or `ModuleNotFoundError: No module named 'carla'`.

Open command prompt, `cd` to this directory and run `set_paths.bat`.

### The speedometer is in MPH instead of KPH.

In the package, open `CarlaUE4\Config\DReyeVRConfig` and set the line `SpeedometerInMPH=True;` to `False`.

# Changes we made to the DReyeVR/Carla codebase

Not all of these changes are necessary. Most are the result of a messy hack used to disable all traffic lights because we wanted to disable a specific light on the experimental route (and had trouble doing this fully for only a single light). The other major change was to accomodate the addition of a flag to enable/disable manual tackeover.

## Editor

### Map: Town04
- **IMPORTANT** Commented out the function `SetTrafficLightsState` on line `102` in `PATH_TO_CARLA\CarlaUE4\Plugins\Carla\Source\Carla\Traffic\TrafficLightController.cpp` to disable the use of traffic lights because we were getting errors after destroying lights. **This means traffic lights cannot be used in this package!**
-  **IMPORTANT** Forced a 90 speed limit at all times on line `14` in `PATH_TO_CARLA\CarlaUE4\Plugins\Carla\Source\Carla\Traffic\SpeedLimitComopnent.cpp`. (This is extremely sub-optimal, but works)
- In the SUBLAYER map for traffic signs, changed all BP_SpeedLimit60 and 30 to 90, both for traffic sign state and limit. (This is a hack to see if we can stop other cars from slowing down at the intersection) (Update: this did not seem to affect the main map at all. Should revert.)
- Changed all rectangular `BP_SpeedLimit60_*` and `BP_SpeedLimit30_*` signs on the "highway" to be 90 for limit and traffic sign state and hid them in game. Did the same in Town04_Opt to the blueprints. (Update: this also did not seem to affect the phantom signs at all.)
- Changed all rectangular `BP_SpeedLimit60_*` and `BP_SpeedLimit30_*` blueprints to 'Do not spawn' and 'Hidden in game'. (Update: this also did not seem to affect the phantom signs at all.)

## C++
These files can be found in `PATH_TO_CARLA\Unreal\CarlaUE4\Source\CarlaUE4`.
- In `EgoVehicle.h` initialized the `bDisableControls` variable. 
- In `EgoVehicle.cpp`, added line to read in the `bDisableControls` variable from the config file. 
- In `EgoInputs.cpp`, changed the functions `SetSteering`, `SetThrottle`, `SetBrake`, and `PressReverse` to not actually trigger any movement if `bDisableControls=True`. We still want the vehicle input to be set so that this is logged in the data recorder.

# Acknowledgements

This work was funded by the European Union Horizon 2020 research and innovation programme as part of the [MEDIATOR project](https://mediatorproject.eu/) (grant agreement 814735). We would like to thank the team that developed and released DReyeVR, and particularly Gustavo Silvera for his support while we built our experiment.

# License

This code is distributed under the MIT License.
