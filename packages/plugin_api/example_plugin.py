"""Example plugin for testing the plugin API registry."""

from .command import Command


class ExamplePlugin:
    id = "example.hello"
    name = "Example Hello Plugin"
    version = "0.1.0"

    def __init__(self) -> None:
        self.activated = False

    def activate(self, context) -> None:
        self.activated = True
        context.register_command(
            Command(
                id="example.say_hello",
                title="Say Hello",
                handler=self.say_hello,
                description="Return a test greeting without touching UI or DB.",
            )
        )

    def deactivate(self) -> None:
        self.activated = False

    def say_hello(self) -> str:
        return "hello"
