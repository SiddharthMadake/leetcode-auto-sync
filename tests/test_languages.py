from leetcode_sync.languages import normalize_language


def test_supported_languages():
    assert normalize_language("python3").extension == "py"
    assert normalize_language("javascript").extension == "js"
    assert normalize_language("typescript").extension == "ts"
    assert normalize_language("cpp").extension == "cpp"
    assert normalize_language("java").extension == "java"
    assert normalize_language("golang").extension == "go"
    assert normalize_language("rust").extension == "rs"


def test_unsupported_language():
    assert normalize_language("mysql") is None
