import os
import json
import urllib.parse
import asyncio
from typing import Tuple
from desktop_notifier.base import Urgency
from cork import rbxcdn
from cork.wine import WineSession
from desktop_notifier import DesktopNotifier


class RobloxSession(WineSession):
    def __init__(self, prefix, dist="", environment={}, fflags={}, launch_type="wine", wine64=False):
        WineSession.__init__(self, prefix, dist,
                             environment, launch_type, wine64)
        self.fflags = fflags

    def get_player(self, channel="", version_override="") -> Tuple[str, str]:
        version = version_override if version_override != "" else rbxcdn.get_version(
            "WindowsPlayer", channel)["clientVersionUpload"]

        version_directory = os.path.join(
            self.get_drive(), "Roblox", "Versions", version)

        if not os.path.isdir(version_directory) or not os.path.exists(os.path.join(version_directory, "RobloxPlayerBeta.exe")):
            notifier = DesktopNotifier()
            loop = asyncio.new_event_loop()
            notification = loop.run_until_complete(notifier.send(
                title="Cork", icon="roblox-player", message=f"Installing {version}...", urgency=Urgency.Critical))

            rbxcdn.install_version(
                version, version_directory, channel, rbxcdn.package_dictionaries["Player"])

            loop.run_until_complete(notifier.clear(notification))
            loop.run_until_complete(notifier.send(title="Cork", icon="roblox-player",
                                                  message=f"{version} has been installed!", urgency=Urgency.Normal))

        exe_path = os.path.join("C:/", os.path.relpath(os.path.join(
            version_directory, "RobloxPlayerBeta.exe"), self.get_drive()))

        return exe_path, version_directory

    def get_studio(self, channel="", version_override="") -> Tuple[str, str]:
        version = version_override if version_override != "" else rbxcdn.get_version(
            "WindowsStudio", channel)["clientVersionUpload"]

        version_directory = os.path.join(
            self.get_drive(), "Roblox", "Versions", version)

        if not os.path.isdir(version_directory) or not os.path.exists(os.path.join(version_directory, "RobloxStudioBeta.exe")):
            notifier = DesktopNotifier()
            loop = asyncio.new_event_loop()
            notification = loop.run_until_complete(notifier.send(
                title="Cork", icon="roblox-studio", message=f"Installing {version}...", urgency=Urgency.Critical))
            
            rbxcdn.install_version(
                version, version_directory, channel, rbxcdn.package_dictionaries["Studio"])
            
            loop.run_until_complete(notifier.clear(notification))
            loop.run_until_complete(notifier.send(title="Cork", icon="roblox-studio",
                                                  message=f"{version} has been installed!", urgency=Urgency.Normal))

        exe_path = os.path.join("C:/", os.path.relpath(os.path.join(
            version_directory, "RobloxStudioBeta.exe"), self.get_drive()))

        return exe_path, version_directory

    def apply_fflags(self, player_directory):
        if not os.path.isdir(os.path.join(player_directory, "ClientSettings")):
            os.makedirs(os.path.join(player_directory, "ClientSettings"))

        with open(os.path.join(player_directory, "ClientSettings", "ClientAppSettings.json"), "w") as file:
            file.write(json.dumps(self.fflags, indent=4))

    def execute_player(self, arguments, launcher="", channel="live", version=""):
        if len(arguments) > 0 and arguments[0].startswith("roblox-player:1+launchmode:"):
            argument_dictionary = {
                "launchmode":       "--",
                "gameinfo":         "-t ",
                "placelauncherurl": "-j ",
                "launchtime":       "--launchtime=",
                "browsertrackerid": "-b ",
                "robloxLocale":     "--rloc ",
                "gameLocale":       "--gloc ",
                "channel":          "-channel "
            }
            startup_argument = arguments[0]

            arguments = []
            for argument_piece in startup_argument.split("+"):
                argument_parts = argument_piece.split(":")

                if argument_parts[0] == "launchmode" and argument_parts[1] == "play":
                    argument_parts[1] = "app"
                if argument_parts[0] == "placelauncherurl":
                    argument_parts[1] = urllib.parse.unquote(argument_parts[1])
                if argument_parts[0] == "channel":
                    if channel == "live":
                        channel = argument_parts[1].lower()
                    else:
                        argument_parts[1] = channel

                if argument_parts[0] in argument_dictionary:
                    arguments.append(
                        argument_dictionary[argument_parts[0]] + argument_parts[1])

        player_exe, player_directory = self.get_player(
            channel=channel, version_override=version)

        self.apply_fflags(player_directory)

        return self.execute([player_exe] + arguments, cwd=player_directory, launcher=launcher)

    def execute_studio(self, arguments, launcher="", channel="live", version=""):
        if channel == "live":
            channel = ""

        studio_exe, studio_directory = self.get_studio(
            channel=channel, version_override=version)

        return self.execute([studio_exe] + arguments, cwd=studio_directory, launcher=launcher)
