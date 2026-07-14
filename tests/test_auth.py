from src.auth import credentials_match


def test_credentials_match_valid_credentials():
    assert credentials_match("Manager", "correct horse battery staple", "manager", "correct horse battery staple")


def test_credentials_match_rejects_wrong_or_empty_values():
    assert not credentials_match("manager", "wrong", "manager", "correct")
    assert not credentials_match("", "correct", "manager", "correct")
    assert not credentials_match("manager", "correct", "", "correct")
