from slouchbuddy import buddy_brain as moods
from slouchbuddy import dashboard_art as art


def test_hero_mood_follows_score():
    assert art.hero_message(None)[0] == moods.SLEEPING
    assert art.hero_message(95)[0] == moods.HAPPY
    assert art.hero_message(75)[0] == moods.COFFEE
    assert art.hero_message(55)[0] == moods.SLOUCHING
    assert art.hero_message(20)[0] == moods.WORRIED


def test_every_message_has_text():
    for score in (None, 95, 75, 55, 20):
        assert art.hero_message(score)[1]


def test_koala_uri_is_an_embeddable_png():
    uri = art.koala_uri(moods.HAPPY, 64)
    assert uri.startswith("data:image/png;base64,") and len(uri) > 200
    assert art.koala_uri(moods.HAPPY, 64) is uri  # cached


def test_leaves_html_has_each_leaf():
    html = art.leaves_html()
    assert html.count('class="sb-leaf"') == art.LEAF_COUNT
