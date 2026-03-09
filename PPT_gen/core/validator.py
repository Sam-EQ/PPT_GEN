def validate_deck(deck):
    assert len(deck.slides) > 0, "Deck has no slides"

    for slide in deck.slides:
        assert slide.type, "Slide missing type"

        if slide.type == "bullet":
            assert slide.bullets, "Bullet slide missing bullets"

        if slide.type == "timeline":
            assert slide.timeline, "Timeline slide missing data"

        if slide.type == "scorecard":
            assert slide.scorecard, "Scorecard slide missing data"

    return True
    