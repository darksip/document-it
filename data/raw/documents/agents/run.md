# Agent.run()

Use the `Agent.run()` function to run the agent and return the response as a `RunResponse` object or a stream of `RunResponse` objects.

```python
from typing import Iterator
from agno.agent import Agent, RunResponse
from agno.models.openai import OpenAIChat
from agno.utils.pprint import pprint_run_response

agent = Agent(model=OpenAIChat(id="gpt-4o-mini"))

# Run agent and return the response as a variable
response: RunResponse = agent.run("Tell me a 5 second short story about a robot")
# Run agent and return the response as a stream
response_stream: Iterator[RunResponse] = agent.run("Tell me a 5 second short story about a lion", stream=True)

# Print the response in markdown format
pprint_run_response(response, markdown=True)
# Print the response stream in markdown format
pprint_run_response(response_stream, markdown=True)
```

<Note>Set `stream=True` to return a stream of `RunResponse` objects.</Note>

## RunResponse

The `Agent.run()` function returns either a `RunResponse` object or an `Iterator[RunResponse]` when `stream=True`. It has the following attributes:

### RunResponse Attributes

| Attribute        | Type                   | Default                       | Description                                                                                                                      |
| ---------------- | ---------------------- | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `content`        | `Any`                  | `None`                        | Content of the response.                                                                                                         |
| `content_type`   | `str`                  | `"str"`                       | Specifies the data type of the content.                                                                                          |
| `context`        | `List[MessageContext]` | `None`                        | The context added to the response for RAG.                                                                                       |
| `event`          | `str`                  | `RunEvent.run_response.value` | Event type of the response.                                                                                                      |
| `event_data`     | `Dict[str, Any]`       | `None`                        | Data associated with the event.                                                                                                  |
| `messages`       | `List[Message]`        | `None`                        | A list of messages included in the response.                                                                                     |
| `metrics`        | `Dict[str, Any]`       | `None`                        | Usage metrics of the run.                                                                                                        |
| `model`          | `str`                  | `None`                        | The model used in the run.                                                                                                       |
| `run_id`         | `str`                  | `None`                        | Run Id.                                                                                                                          |
| `agent_id`       | `str`                  | `None`                        | Agent Id for the run.                                                                                                            |
| `session_id`     | `str`                  | `None`                        | Session Id for the run.                                                                                                          |
| `tools`          | `List[Dict[str, Any]]` | `None`                        | List of tools provided to the model.                                                                                             |
| `images`         | `List[Image]`          | `None`                        | List of images the model produced.                                                                                               |
| `videos`         | `List[Video]`          | `None`                        | List of videos the model produced.                                                                                               |
| `audio`          | `List[Audio]`          | `None`                        | List of audio snippets the model produced.                                                                                       |
| `response_audio` | `ModelResponseAudio`   | `None`                        | The model's raw response in audio.                                                                                               |
| `created_at`     | `int`                  | -                             | Unix timestamp of the response creation.                                                                                         |
| `extra_data`     | `RunResponseExtraData` | `None`                        | Extra data containing optional fields like `references`, `add_messages`, `history`, `reasoning_steps`, and `reasoning_messages`. |
