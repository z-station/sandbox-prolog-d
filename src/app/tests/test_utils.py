from app.utils import clean_str


def test_clean_str__first_new_line__not_remove():

    # arrange
    value = (
        '\n'
        '1 9\n'
        'ДА'
    )

    # act
    result = clean_str(value)

    # assert
    assert result == (
        '\n'
        '1 9\n'
        'ДА'
    )


def test_clean_str__last_new_line__remove():

    # arrange
    value = (
        '\n'
        '1 9\n'
        'ДА\n\n'
    )

    # act
    result = clean_str(value)

    # assert
    assert result == (
        '\n'
        '1 9\n'
        'ДА'
    )


def test_clean_str__char_carriage_return__remove():

    # arrange
    value = (
        '1 9\n\r'
        '1 9\n\r'
        'ДА'
    )

    # act
    result = clean_str(value)

    # assert
    assert result == (
        '1 9\n'
        '1 9\n'
        'ДА'
    )
