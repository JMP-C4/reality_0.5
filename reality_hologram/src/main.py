"""Entry point for the reality_hologram module."""

from .controllers.command_router import CommandRouter
from .core.pipeline import RealityPipeline


def main():
    pipeline = RealityPipeline()
    router = CommandRouter(pipeline=pipeline)
    router.route_command("boot", {"scene": "default"})
    router.route_command("render_frame")
    router.route_command("shutdown")


if __name__ == "__main__":
    main()

