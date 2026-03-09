from app.services.template import render_value, resolve_path


class TestResolvePath:
    def test_resolves_top_level_key(self) -> None:
        assert resolve_path({"foo": "bar"}, "foo") == "bar"

    def test_resolves_nested_key(self) -> None:
        assert resolve_path({"trigger": {"payload": {"email": "a@b.com"}}}, "trigger.payload.email") == "a@b.com"

    def test_returns_none_for_missing_key(self) -> None:
        assert resolve_path({"foo": "bar"}, "foo.missing") is None

    def test_returns_none_for_empty_context(self) -> None:
        assert resolve_path({}, "any.path") is None

    def test_resolves_non_string_value(self) -> None:
        assert resolve_path({"count": 42}, "count") == 42


class TestRenderValue:
    def test_simple_string_substitution(self) -> None:
        ctx = {"trigger": {"payload": {"email": "x@y.com"}}}
        result = render_value("{{trigger.payload.email}}", ctx)
        assert result == "x@y.com"

    def test_preserves_string_without_tokens(self) -> None:
        assert render_value("hello world", {}) == "hello world"

    def test_missing_token_replaced_with_empty_string(self) -> None:
        result = render_value("Hello {{trigger.payload.name}}", {})
        assert result == "Hello "

    def test_multiple_tokens_in_one_string(self) -> None:
        ctx = {"trigger": {"payload": {"first": "Ana", "last": "Lopez"}}}
        result = render_value("{{trigger.payload.first}} {{trigger.payload.last}}", ctx)
        assert result == "Ana Lopez"

    def test_single_token_preserves_type(self) -> None:
        ctx = {"steps": {"step_a": {"count": 7}}}
        result = render_value("{{steps.step_a.count}}", ctx)
        assert result == 7

    def test_renders_dict_recursively(self) -> None:
        ctx = {"trigger": {"payload": {"email": "a@b.com"}}}
        result = render_value({"to": "{{trigger.payload.email}}"}, ctx)
        assert result == {"to": "a@b.com"}

    def test_renders_list_recursively(self) -> None:
        ctx = {"trigger": {"payload": {"name": "Bob"}}}
        result = render_value(["{{trigger.payload.name}}", "static"], ctx)
        assert result == ["Bob", "static"]

    def test_non_string_value_returned_as_is(self) -> None:
        assert render_value(42, {}) == 42
        assert render_value(True, {}) is True
        assert render_value(None, {}) is None

    def test_whitespace_around_token_is_trimmed(self) -> None:
        ctx = {"trigger": {"payload": {"val": "ok"}}}
        result = render_value("{{ trigger.payload.val }}", ctx)
        assert result == "ok"
