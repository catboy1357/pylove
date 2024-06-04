"""
Simple wrapper lib to interface with the lan game mode found here:
https://developer.lovense.com/docs/standard-solutions/standard-api.html#game-mode
Direct the user to Lovense Remote App > Discover > Game Mode > Enable LAN
Get the user info about Local IP, and Port and feed it into LovenseGameMode
class constructor. The "Accepting control from third-party apps"
should show your app name. The home tab section should also say "Toy controlled
by" your app name.
"""
from typing import Any, Dict, List, Optional, Union
from enum import StrEnum
import json
import requests


class Actions(StrEnum):
    """Data class to hold the magic string values for Actions"""
    VIBRATE = "Vibrate"
    VIBRATE1 = "Vibrate1"
    VIBRATE2 = "Vibrate2"
    VIBRATE3 = "Vibrate3"
    ROTATE = "Rotate"
    PUMP = "Pump"
    THRUSTING = "Thrusting"
    FINGERING = "Fingering"
    SUCTION = "Suction"
    DEPTH = "Depth"
    ALL = "All"


class Presets(StrEnum):
    """Data class to hold the magic string values for Presets"""
    PULSE = "pulse"
    WAVE = "wave"
    FIREWORKS = "fireworks"
    EARTHQUAKE = "earthquake"


class GameModeWrapper():
    """
    ## API wrapper to deal with the LAN/Game Mode version of the Lovense
    Standard Solutions API

    ### Args:
    - app_name: The name of your application.
    - local_ip: the ip of the device to connect to
    - port: the port of the device to connect to
    - ssl_port: unused but in the Lovense app
    - logging: enable logging in the class

    ### Methods:
    - send_command(): Send a JSON command directly to the app (advanced)
    - get_toys(): Gets the toy(s) connect to the Lovense app
    - get_toys_name(): Same as get_toys() but just the name of the devices
    - function_request(): Send a single Pattern immediately
    - stop(): Sends a stop immediately command
    - pattern_request(): Avoids network pressure of multiple function commands
    - pattern_request_raw(): More api accurate version for patterns (advanced)
    - preset_request(): Send one of the pre-made or user created patterns

    ### Attributes
    - app_name: The name of the app
    - api_endpoint: The destination the data is sent to
    - log: enable logging in the class. Only has print for now
    - actions: a reference to the Actions StrEnum
    - presets: a reference to the Presets StrEnum
    - error_codes: A dict of all the expected error codes
    """

    def __init__(
        self,
        app_name: str,
        local_ip: str,
        port: int = 20010,
        ssl_port: int = 30010,
        logging: bool = False
    ) -> None:

        # Define the server's API endpoint
        self.app_name = app_name
        self.api_endpoint = f"http://{local_ip}:{port}/command"
        self._ssl_port = ssl_port
        self.log = logging

        # References to the StrEnums
        self.actions = Actions
        self.presets = Presets

        # the last command sent, can be used to send again
        self.last_command = None

        # A list of all the error code from the docs
        self.error_codes = {
            200: "OK",
            400: "Invalid Command",
            401: "Toy Not Found",
            402: "Toy Not Connected",
            403: "Toy Doesn't Support This Command",
            404: "Invalid Parameter",
            500: "HTTP server not started or disabled",
            506: "Server Error. Restart Lovense Connect."
        }

        # clamp values for the function_request
        self._function_range = {
            Actions.VIBRATE: {"min": 0, "max": 20},
            Actions.VIBRATE1: {"min": 0, "max": 20},
            Actions.VIBRATE2: {"min": 0, "max": 20},
            Actions.VIBRATE3: {"min": 0, "max": 20},
            Actions.ROTATE: {"min": 0, "max": 20},
            Actions.PUMP: {"min": 0, "max": 3},
            Actions.THRUSTING: {"min": 0, "max": 20},
            Actions.FINGERING: {"min": 0, "max": 20},
            Actions.SUCTION: {"min": 0, "max": 20},
            Actions.DEPTH: {"min": 0, "max": 3},
            Actions.ALL: {"min": 0, "max": 20}
        }

    def _parse_json(
        self,
        data: Union[str, dict, list]
    ) -> Dict[str, Any]:
        """refactor request for nested encoded objects into json/dict objects

        Args:
            data (str | dict | list): The data to parse, can be a JSON string.

        Returns:
            Dict[str, Any]: The refactored json data
        """
        # linter warnings ignore because this is a recursive function,
        # should always be a dict return
        if isinstance(data, str):
            try:
                return json.loads(data)
            except ValueError:
                return data  # type: ignore
        elif isinstance(data, dict):
            return {k: self._parse_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._parse_json(item) for item in data]  # type: ignore
        else:
            return data

    def send_command(
        self,
        command_data: Dict[str, Any],
        timeout: int = 10
    ) -> Optional[Dict[str, Any]]:
        """Directly send a json command to the app and handle the response.

        Args:
            command_data (Dict[str, Any]): Json value to send to the app

        Returns:
            Optional[Dict[str, Any]]: The json response code from the app
        """
        # sets the header data to tell the app who you are.
        headers = {
            "X-platform": self.app_name
        }

        # Log the command data if logging is enabled.
        if self.log:
            print(command_data)

        self.last_command = command_data

        # make a request to the app.
        response = None
        try:
            response = requests.post(
                self.api_endpoint,
                json=command_data,
                headers=headers,
                timeout=timeout
            )
        except requests.exceptions.ConnectionError as e:
            print("Error: Failed to establish a new connection")
            if self.log:
                print(e)
            return None
        except requests.exceptions.Timeout as e:
            print("Error: Request timed out")
            if self.log:
                print(e)
            return None
        except requests.exceptions.RequestException as e:
            err_message = e
            if not self.log:
                err_message = str(e)[:50] + "... Enable logging for more info"
            print(f'Error: An error occurred in the request: {err_message}')
            return None

        # filter the response in case an error occurred.
        if not response:
            print("Error: Received no response from server.")
            return None

        if response.status_code != 200:
            print(
                "Error: Received HTTP status code",
                response.status_code, "from the server."
            )
            return None

        # Parse the JSON response.
        response_json = response.json()
        response_json = self._parse_json(response_json)

        # Retrieve and log the response code and message, if logging is enabled
        response_code = response_json.get("code")
        if isinstance(response_code, int):
            error_message = self.error_codes.get(
                response_code, "Unknown Error"
            )
            response_msg = f"Response: {response_code}, {error_message}"
        else:
            response_msg = f"Response: Unknown response code {response_code}"
        if self.log:
            print(response_msg)
            print(json.dumps(response_json, indent=4))
            print()
        return response_json

    def _function_clamp_range(
        self, actions: Dict[str, float] | dict[Actions, float]
    ) -> Dict[str, float]:
        """Clamp the values of actions within API specified ranges.

        Args:
            actions (Dict[str, int]): A dictionary containing actions as keys
                and their corresponding integer values.

        Returns:
            Dict[str, int]: A dictionary containing clamped values of actions.
        """
        clamped_actions = {}
        for action, value in actions.items():
            if action in self._function_range:
                min_val = self._function_range[action]["min"]
                max_val = self._function_range[action]["max"]
                clamped_value = max(min(value, max_val), min_val)
                clamped_actions[action] = clamped_value
            else:
                # If action not found in FUNCTION_RANGE, use the original value
                clamped_actions[action] = value
        return clamped_actions

    def function_request(
        self,
        actions: Dict[str, float] | dict[Actions, float],
        time: float = 0,
        loop_on_time: Optional[float] = None,
        loop_off_time: Optional[float] = None,
        toy_id: Optional[str] = None,
        stop_last: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        """Send a function request to the app

        Args:
            actions (Dict[str, int]): A dictionary containing actions as keys
                and their corresponding values. Use the `Actions` StrEnum.
            time (float, optional): The time in seconds for the function
                request. Defaults to 0 for indefinite time.
            loop_on_time (Optional[float], optional): The time in seconds for
                a running loop. Defaults to None.
            loop_off_time (Optional[float], optional): The time in seconds for
                the loop to pause. Defaults to None.
            toy_id (Optional[str], optional): The ID of the toy. Defaults to
                None for all devices.
            stop_last (Optional[bool], optional): Whether to stop the previous
                command. Defaults to None for yes stop.

        Returns:
            Optional[Dict[str, Any]]: A dictionary representing the response
                if the command is sent successfully, otherwise None.
        """

        # Construct the action string
        actions = self._function_clamp_range(actions)
        action = ','.join(f"{key}:{value}" for key, value in actions.items())

        # Create the required data
        payload = {
            "command": "Function",
            "action": action,
            "timeSec": time,
            "apiVer": 1
        }

        # Add optional parameters if they are provided
        if loop_on_time is not None:
            payload["loopRunningSec"] = max(loop_on_time, 1)
        if loop_off_time is not None:
            payload["loopPauseSec"] = max(loop_off_time, 1)
        if toy_id is not None:
            payload["toy"] = toy_id
        if stop_last is not None:
            payload["stopPrevious"] = 1 if stop_last else 0

        # sends combined payload
        return self.send_command(payload)

    def stop(self, toy_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Send a command to stop a function.

        Args:
            toy_id (Optional[str], optional): the ID of the toy to stop.
                Defaults to None for all toys.
        Returns:
            Optional[Dict[str, Any]]:

        """
        payload = {
            "command": "Function",
            "action": "Stop",
            "timeSec": 0,
            "apiVer": 1
        }
        if toy_id is not None:
            payload["toy"] = toy_id
        return self.send_command(payload)

    def _convert_actions_to_letters(
        self,
        actions: Union[list[str], list[Actions]]
    ) -> str:
        """Convert a list of action identifiers to a string of their
            corresponding letter codes.

        Args:
            actions (Union[list[str], list[Actions]]): A list of actions
                as either strings or instances of the `Actions` StrEnum.

        Returns:
            str: A comma-separated string of valid letter codes derived from
                the input actions. An empty string is returned for errors.
        """

        letter_codes = []
        valid_letters = ["v", "r", "p", "t", "f", "s", "d"]

        # iterate over all the Actions passed in.
        for action in actions:

            # Check type for string and that the string is not empty
            if isinstance(action, str) and len(action) > 0:
                letter = action[0].lower()

                # Only return valid codes
                if letter not in valid_letters:
                    continue
                letter_codes.append(letter)

            # Append the first letter of the action directly
            elif isinstance(action, Actions):
                letter_codes.append(action[0].lower())

            # Return Actions.All as a default value if its the wrong type
            else:
                return ""

        # Only return the codes if there are any code, else return Actions.ALL
        if letter_codes:
            return ','.join(letter_codes)
        return ""

    def pattern_request_raw(
        self,
        strength: str,
        rule: str = "V:1;F:;S:100#",
        time: float = 0,
        toy_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create and send a pattern request to a toy using raw rules and
            strengths strings.

        Args:
            strength (str): The strength string defining the pattern.
            rule (str, optional): The rule string defining the pattern.
                Defaults to "V:1;F:;S:100#".
                Rules format:
                    V:1; | version,
                    F:(...); | Features (Actions letter) comma separated,
                    S:100# | Interval 100ms
            time (float, optional): The duration of the pattern in seconds.
                Defaults to 0.
            toy_id (Optional[str], optional): The ID of the toy. Defaults to
                None for all devices.

        Returns:
            Optional[Dict[str, Any]]: A dictionary representing the response
                if the command is sent successfully, otherwise None.
        """

        # Set up the json object to send
        payload = {
            "command": "Pattern",
            "rule": rule,
            "strength": strength,
            "timeSec": time,
            "apiVer": 2
        }

        # Add optional args
        if toy_id is not None:
            payload["toy"] = toy_id

        return self.send_command(payload)

    def pattern_request(
        self,
        pattern: List[int],
        actions: Union[List[str], List[Actions], None] = None,
        interval: int = 100,
        time: float = 0,
        toy_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create and send a pattern request to a toy using abstracted parameters.

        Args:
            pattern (List[int]):  A list of integers representing the pattern
                strength over time. Limited to the first 50 elements.
            actions (Union[List[str], List[Actions], None], optional): A list
                of action identifiers (strings or Actions instances).
                Defaults to [Actions.ALL] if None.
            interval (int, optional): The interval between actions in
                milliseconds. Clamped between 100 and 1000. Defaults to 100.
            time (float, optional): The duration of the pattern in seconds.
                Defaults to 0.
            toy_id (Optional[str], optional): The ID of the toy. Defaults to
                None for all devices.

        Returns:
            Optional[Dict[str, Any]]: A dictionary representing the response
                if the command is sent successfully, otherwise None.
        """

        # sentinel value for default list values
        if actions is None:
            actions = [Actions.ALL]

        # Slice to get the first 50 elements of the list as per the docs
        # Clam the values into an acceptable range
        pattern = pattern[:50]
        pattern = [min(max(0, num), 20) for num in pattern]

        # Clam the value into an acceptable range
        # Docs does not list a maximum value, highest in samples is 1000
        # Lowest value must be above 100
        interval = min(max(interval, 100), 1000)

        # Build the rule and strength properties pythonic
        acts = self._convert_actions_to_letters(actions)
        rule = f"V:1;F:{acts};S:{interval}#"

        # Docs specifies to leave F:; blank for all functions respond
        if Actions.ALL in actions:
            rule = f"V:1;F:;S:{interval}#"
        strength = ";".join(map(str, pattern))

        # Pass the construction data over to the raw method to send.
        return self.pattern_request_raw(strength, rule, time, toy_id)

    def preset_request(
        self,
        name: str,
        time: float = 0,
        toy_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Sends a preset command to the toy.

        Args:
            name (str): The name of the preset. This can be a default preset
                from the `Presets` enum or a custom preset added by the user.
            time (float, optional): The duration for which the preset should
                be active, in seconds. Defaults to 0 for indefinite time.
            toy_id (Optional[str], optional): The ID of the toy. Defaults to
                None for all devices.
        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the response code
                and type, or None if the command fails.
        """
        payload = {
            "command": "Preset",
            "name": name,
            "timeSec": time,
            "apiVer": 1
        }

        if toy_id is not None:
            payload["toy"] = toy_id

        return self.send_command(payload)

    def get_toys(self) -> Optional[Dict[str, Any]]:
        """Send a command to retrieve information about all toys.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing information
                about all toys, or None if an error occurred.
        """
        return self.send_command({
            "command": "GetToys"
        })

    def get_toys_name(self) -> Optional[Dict[str, Any]]:
        """Send a command to retrieve names of all toys

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing names of all
                toys, or None if an error occurred.
        """
        return self.send_command({
            "command": "GetToyName"
        })


if __name__ == "__main__":
    love = GameModeWrapper("My Cool App", "10.0.0.69", logging=False)
    # example commands usage. Uncomment to try them out. basic example just
    # have the time keyword arguments. You can experiment with others.

    # print(love.get_toys())
    # print(love.get_toys_name())

    # love.function_request({love.actions.ALL: 2}, time=3)

    # love.preset_request(love.presets.PULSE, time=3)

    # love.pattern_request([1, 2, 3, 4, 5, 20], time=5)
    # love.pattern_request_raw("1;2;3;4;5;20", time=5)

    # command = {
    #     "command": "GetToyName"
    # }
    # love.send_command(command)

    # if love.last_command:
    #     love.send_command(love.last_command)

    input("Press enter to stop")
    love.stop()
