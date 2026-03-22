import subprocess
import sys


class Qalculate:
    def __init__(self, qalculate_bin: str) -> None:
        self.qalculate_bin = qalculate_bin

    def qalc(self, expression: str) -> str:
        raw_result = subprocess.check_output(
            [self.qalculate_bin, expression], shell=sys.platform == "win32"
        )
        try:
            return raw_result.decode("utf-8")
        except UnicodeDecodeError:
            return raw_result.decode("gbk")

    def get_version(self) -> str:
        return self.qalc("--version")

    def check_qalculate(self) -> bool:
        try:
            self.get_version()
            return True
        except:  # noqa
            return False
