"""
Example usage of the pylove game wrapper.
The GameModeWrapper class has several methods to interface with the API.
All major endpoints are listed here. Uncomment some to try them out.

These basic examples use the `time` keyword argument. You can experiment with
others. Time is optional and the commands will run indefinitely if not set.

All commands return a response code from the app.
Enabling logging will show more info about what is happening behind the scenes.

Most commands use the `send_command()` method internally.
They save their command JSON to the `last_command` variable.
You can use this to save on processing.

Most commands support the `self.actions.x` StrEnum.
This lets you target individual events based on the connected hardware.
By default, these use the `actions.ALL` action to trigger all devices.

Most errors are caught in the class and `None` is returned instead.
"""
from pylove.lan import GameModeWrapper


if __name__ == "__main__":
    # Initialize the GameModeWrapper with your app name and IP address.
    # The port is often 20010 unless something else has bound to this port.
    love = GameModeWrapper("My Cool App", "10.0.0.69", logging=False)

    # Gets details about the connected hardware.
    print(love.get_toys())
    # print(love.get_toys_name())

    # Send one of the presets to the app. Can also call user made presets.
    # This example sends the PULSE preset for 5 seconds.
    # love.preset_request(love.presets.PULSE, time=5)

    # Send a basic custom command to the app.
    # This example sets the strength of all devices to 2 for 5 seconds.
    # love.function_request({love.actions.ALL: 2}, time=5)

    # Send a set of strength values over time to the app.
    # The following two methods achieve the same result, but `_raw` follows
    # the docs closer and is called by the normal version.
    # This example sends a pattern of strengths with a default interval of
    # 100 ms for 5 seconds time.
    # love.pattern_request([1, 2, 3, 4, 5, 20], time=5)
    # love.pattern_request_raw("1;2;3;4;5;20", time=5)

    # Send a raw JSON command to the app.
    # This example is the raw JSON for love.get_toys_name()
    # command = {
    #     "command": "GetToyName"
    # }
    # love.send_command(command)

    # Use the JSON of the last command to execute it again.
    # If a command was previously sent, it can be saved and/or re-executed
    # if love.last_command:
    #     love.send_command(love.last_command)

    # Stops all running commands. This is only required if you don't use the
    # `time` keyword argument. Without the `time` argument, commands run until
    # stopped manually.
    input("Press enter to stop all commands")
    love.stop()
