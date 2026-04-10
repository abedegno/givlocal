"""Tests for the pagination utility."""


def test_paginate_first_page():
    from givlocal.api.pagination import paginate

    items = list(range(25))
    result = paginate(items, page=1, per_page=10, base_url="/test")

    assert len(result.data) == 10
    assert result.data[0] == 0
    assert result.meta.total == 25
    assert result.meta.current_page == 1
    assert result.meta.last_page == 3
    assert result.links.prev is None
    assert result.links.next is not None


def test_paginate_last_page():
    from givlocal.api.pagination import paginate

    items = list(range(25))
    result = paginate(items, page=3, per_page=10, base_url="/test")

    assert len(result.data) == 5
    assert result.links.next is None
    assert result.links.prev is not None
