from decimal import Decimal, ROUND_HALF_UP

THAI_NUM = ["ศูนย์", "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า"]
THAI_POS = ["", "สิบ", "ร้อย", "พัน", "หมื่น", "แสน", "ล้าน"]


def _read_under_million(number: int) -> str:
    if number == 0:
        return ""
    words = ""
    digits = list(map(int, str(number)))
    length = len(digits)
    for i, digit in enumerate(digits):
        pos = length - i - 1
        if digit == 0:
            continue
        if pos == 1:
            if digit == 1:
                words += "สิบ"
                continue
            if digit == 2:
                words += "ยี่สิบ"
                continue
        if pos == 0 and digit == 1 and length > 1:
            words += "เอ็ด"
            continue
        words += THAI_NUM[digit] + THAI_POS[pos]
    return words


def _read_number(number: int) -> str:
    if number == 0:
        return THAI_NUM[0]
    words = ""
    million = 1_000_000
    if number >= million:
        high = number // million
        low = number % million
        words += _read_number(high) + "ล้าน"
        if low > 0:
            words += _read_under_million(low)
        return words
    return _read_under_million(number)


def baht_text(amount: Decimal) -> str:
    amt = Decimal(amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    baht = int(amt)
    satang = int((amt - Decimal(baht)) * 100)
    if baht == 0:
        words = "ศูนย์บาท"
    else:
        words = _read_number(baht) + "บาท"
    if satang == 0:
        return words + "ถ้วน"
    return words + _read_number(satang) + "สตางค์"
