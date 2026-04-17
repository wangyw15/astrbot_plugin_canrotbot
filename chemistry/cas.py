import re


class CAS:
    CAS_PATTERN = r"(\d{2,7})-(\d{2})-(\d)"

    def validate(self, cas_number: str) -> bool:
        if match := re.fullmatch(self.CAS_PATTERN, cas_number):
            part1 = match[1]
            part2 = match[2]
            part3 = match[3]

            check_digit = 0
            for i, digit in enumerate(reversed(part1 + part2)):
                check_digit += int(digit) * (i + 1)
            check_digit = check_digit % 10

            if part3 == str(check_digit):
                return True

        return False
