import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.api.endpoints.stream_utils import generate_chat_stream


class MockChunkStream:
    def __init__(self, contents):
        self.contents = contents

    def __aiter__(self):
        self._iter = iter(self.contents)
        return self

    async def __anext__(self):
        try:
            content = next(self._iter)
            mock_choice = MagicMock()
            mock_choice.delta.content = content
            mock_chunk = MagicMock()
            mock_chunk.choices = [mock_choice]
            return mock_chunk
        except StopIteration:
            raise StopAsyncIteration


async def collect_stream_tokens(stream_gen):
    tokens = []
    events = []
    async for item in stream_gen:
        lines = item.strip().split("\n")
        event_type = None
        data = None
        for line in lines:
            if line.startswith("event: "):
                event_type = line[len("event: "):]
            elif line.startswith("data: "):
                data = json.loads(line[len("data: "):])
        events.append((event_type, data))
        if event_type == "token" and data and "content" in data:
            tokens.append(data["content"])
    return "".join(tokens), events


@pytest.mark.asyncio
@patch("app.api.endpoints.stream_utils.process_post_generation")
@patch("app.api.endpoints.stream_utils.AsyncOpenAI")
async def test_stream_regular_content_without_tags(mock_openai_cls, mock_post_gen):
    chunks = ["Hello, ", "this is ", "a simple ", "response."]
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = MockChunkStream(chunks)
    mock_openai_cls.return_value = mock_client

    state = {}
    stream = generate_chat_stream(uuid4(), uuid4(), {}, state)
    emitted_text, events = await collect_stream_tokens(stream)

    assert emitted_text == "Hello, this is a simple response."
    assert state.get("full_text") == "Hello, this is a simple response."
    assert events[0][0] == "message_id"
    assert events[-1][0] == "done"


@pytest.mark.asyncio
@patch("app.api.endpoints.stream_utils.process_post_generation")
@patch("app.api.endpoints.stream_utils.AsyncOpenAI")
async def test_stream_filters_tag_split_across_chunks(mock_openai_cls, mock_post_gen):
    # Tag split into two chunks: '<Inter' and 'nal_Analysis>'
    chunks = [
        "Greeting! ",
        "<Inter",
        "nal_Analysis>I am calculating my response</Internal_Analysis>Now I speak.",
    ]
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = MockChunkStream(chunks)
    mock_openai_cls.return_value = mock_client

    state = {}
    stream = generate_chat_stream(uuid4(), uuid4(), {}, state)
    emitted_text, _ = await collect_stream_tokens(stream)

    assert emitted_text == "Greeting! Now I speak."
    assert "I am calculating my response" not in emitted_text
    assert "<Internal_Analysis>" not in emitted_text
    assert "</Internal_Analysis>" not in emitted_text
    # full_text preserves everything for post-generation extraction
    assert "I am calculating my response" in state["full_text"]


@pytest.mark.asyncio
@patch("app.api.endpoints.stream_utils.process_post_generation")
@patch("app.api.endpoints.stream_utils.AsyncOpenAI")
async def test_stream_filters_closing_tag_split_across_chunks(mock_openai_cls, mock_post_gen):
    chunks = [
        "<Internal_Analysis>Secret thought</Internal",
        "_Analysis>Visible text after thought.",
    ]
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = MockChunkStream(chunks)
    mock_openai_cls.return_value = mock_client

    state = {}
    stream = generate_chat_stream(uuid4(), uuid4(), {}, state)
    emitted_text, _ = await collect_stream_tokens(stream)

    assert emitted_text == "Visible text after thought."
    assert "Secret thought" not in emitted_text


@pytest.mark.asyncio
@patch("app.api.endpoints.stream_utils.process_post_generation")
@patch("app.api.endpoints.stream_utils.AsyncOpenAI")
async def test_stream_filters_character_by_character_tag(mock_openai_cls, mock_post_gen):
    tag = "<Internal_Analysis>"
    chunks = list(tag) + ["thought", "</Internal_Analysis>", "Done!"]
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = MockChunkStream(chunks)
    mock_openai_cls.return_value = mock_client

    state = {}
    stream = generate_chat_stream(uuid4(), uuid4(), {}, state)
    emitted_text, _ = await collect_stream_tokens(stream)

    assert emitted_text == "Done!"
    assert "thought" not in emitted_text


@pytest.mark.asyncio
@patch("app.api.endpoints.stream_utils.process_post_generation")
@patch("app.api.endpoints.stream_utils.AsyncOpenAI")
async def test_stream_does_not_swallow_false_prefix(mock_openai_cls, mock_post_gen):
    # Prefix '<Inter' followed by 'net connection>' (not '<Internal_Analysis>')
    chunks = ["Check the <Inter", "net connection> right now."]
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = MockChunkStream(chunks)
    mock_openai_cls.return_value = mock_client

    state = {}
    stream = generate_chat_stream(uuid4(), uuid4(), {}, state)
    emitted_text, _ = await collect_stream_tokens(stream)

    assert emitted_text == "Check the <Internet connection> right now."


@pytest.mark.asyncio
@patch("app.api.endpoints.stream_utils.process_post_generation")
@patch("app.api.endpoints.stream_utils.AsyncOpenAI")
async def test_stream_flushes_pending_prefix_at_end_of_stream(mock_openai_cls, mock_post_gen):
    # Stream ends while buffer holds potential prefix '<Inter'
    chunks = ["Goodbye <Inter"]
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = MockChunkStream(chunks)
    mock_openai_cls.return_value = mock_client

    state = {}
    stream = generate_chat_stream(uuid4(), uuid4(), {}, state)
    emitted_text, _ = await collect_stream_tokens(stream)

    assert emitted_text == "Goodbye <Inter"
