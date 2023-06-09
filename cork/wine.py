import subprocess
import os
import pwd
import time
from datetime import datetime


class WineSession:
    def __init__(self, prefix, dist="", launcher=[], environment={}, launch_type="wine", wine64=False, log_directory=""):
        self.dist = dist
        self.prefix = os.path.abspath(prefix)
        self.environment = environment
        self.launch_type = launch_type
        self.launcher = launcher
        self.wine64 = wine64
        self.log_directory = log_directory
    
    def execute(self, arguments, binary_name="", cwd=""):
        wine_environment = os.environ.copy() | self.environment

        if cwd == "":
            cwd = self.prefix

        start_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

        if self.launch_type != "proton" or self.dist == "":
            if binary_name == "":
                binary_name = "wine64" if self.wine64 else "wine"

            wine_binary = binary_name

            if self.dist != "":
                wine_binary = os.path.join(os.path.abspath(
                    self.dist), "bin", binary_name)
            
            wine_environment["WINEPREFIX"] = self.prefix

            return subprocess.run(self.launcher + [wine_binary] + arguments, env=wine_environment, cwd=cwd,
                                  stderr=None if self.log_directory == "" else open(os.path.join(self.log_directory, f"{binary_name}-{start_time}-stderr.log"), "w+"))
        else:
            proton_binary = os.path.join(os.path.abspath(
                    self.dist), "..", "proton")
            
            if binary_name != "":
                proton_binary = os.path.join(os.path.abspath(
                    self.dist), "bin", binary_name)
            
            wine_environment["STEAM_COMPAT_DATA_PATH"] = os.path.join(self.prefix, "..")
            
            return subprocess.run(self.launcher + [proton_binary, "run"] + arguments, env=wine_environment, cwd=cwd)


    def initialize_prefix(self):
        return self.execute(["wineboot"])

    def shutdown_prefix(self):
        return self.execute(["-k"], binary_name="wineserver")

    def wait_prefix(self):
        return self.execute(["-wk"], binary_name="wineserver")

    def get_drive(self) -> str:
        return os.path.join(self.prefix, "drive_c")

    def get_user(self) -> str:
        return pwd.getpwuid(os.getuid())[0]
