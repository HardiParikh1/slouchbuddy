import pytest
from PIL import ImageChops

from slouchbuddy import koala


@pytest.mark.parametrize("mood", koala.MOODS)
def test_every_mood_renders_a_visible_transparent_image(mood):
    img = koala.render(mood, t=0.7, size=64)
    assert img.size == (64, 64) and img.mode == "RGBA"
    alpha = img.getchannel("A")
    assert alpha.getbbox() is not None  # something was drawn
    assert alpha.getpixel((0, 0)) == 0  # corners stay transparent


def test_moods_look_different():
    images = {m: koala.render(m, t=0.7, size=64) for m in koala.MOODS}
    moods = list(images)
    for i, a in enumerate(moods):
        for b in moods[i + 1:]:
            assert ImageChops.difference(images[a], images[b]).getbbox() is not None, (a, b)


def test_animation_changes_over_time():
    a = koala.render("happy", t=0.0, size=64)
    b = koala.render("happy", t=0.4, size=64)
    assert ImageChops.difference(a, b).getbbox() is not None


def test_icon_frames_are_cached(tmp_path):
    paths = koala.icon_frame_paths("happy", str(tmp_path), size=24)
    assert len(paths) == koala.FRAMES_PER_MOOD
    first_mtime = [p for p in paths][0]
    import os
    m1 = os.path.getmtime(first_mtime)
    koala.icon_frame_paths("happy", str(tmp_path), size=24)
    assert os.path.getmtime(first_mtime) == m1
