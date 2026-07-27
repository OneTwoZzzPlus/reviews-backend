from services.reviews import normalize


def test_normalize_empty_or_none():
    assert normalize("") == ""
    assert normalize(None) == ""


def test_normalize_basic_text():
    assert normalize("Привет, Мир!") == "привет мир"


def test_normalize_yo_replacement():
    assert normalize("Ёлка Фёдор") == "елка федор"


def test_normalize_duplicate_letters():
    # Регулярка (.)\1+ сжимает повторяющиеся символы
    assert normalize("Пррииввеетт") == "привет"


def test_normalize_special_characters():
    assert normalize("Иванов И.И. (профессор) @123!") == "иванов ии професор 123"
