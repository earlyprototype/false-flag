"""The six data layers every surface filters the event stream by.

One enum, one tag: events are tagged at the bus (api/server.py push_event),
never inside the engine. ``channel`` is already the authoring-side tag on
injects (scripted episodes and the generator alike); layer_for_channel
canonicalises every channel value observed in the wild onto a layer. The live
contract is documented in docs/tech/SERVER_STREAMING.md.

Leaf module: importable by engine, api and surfaces with no heavy imports.
"""

from enum import Enum
from typing import Optional


class Layer(str, Enum):
    """Who a piece of the stream is for. REFEREE never reaches a player."""

    SITREP = "sitrep"          # Common operating picture: summary, vibes, clock, ending
    INTEL = "intel"            # Intelligence products, assessments
    DIPLOMATIC = "diplomatic"  # Channels, calls, cables
    DOMESTIC = "domestic"      # Domestic mood and media (MEDIA merged in for now)
    CABINET = "cabinet"        # Advisor lines, pushback, concerns
    REFEREE = "referee"        # Hidden truth: raw metrics, verdicts, call log


#: Layers a player browser may receive. REFEREE is filtered server-side.
PLAYER_LAYERS = frozenset(
    layer for layer in Layer if layer is not Layer.REFEREE
)


#: Channel vocabulary observed in the wild -> layer.
#: Scripted episodes use: briefing / intelligence / emergency / flash_alert /
#: diplomatic. The inject generator prompt requests: briefing / intelligence /
#: media / military. The legacy display path also knew: intel / breaking.
CHANNEL_LAYER_MAP = {
    # SITREP updates in place; emergency and flash_alert seize focus but are
    # still the common operating picture, as are military
    # posture developments.
    "briefing": Layer.SITREP,
    "emergency": Layer.SITREP,
    "flash_alert": Layer.SITREP,
    "military": Layer.SITREP,
    "breaking": Layer.SITREP,
    # The INTEL folder
    "intelligence": Layer.INTEL,
    "intel": Layer.INTEL,
    # The red phone
    "diplomatic": Layer.DIPLOMATIC,
    # The TV wall
    "media": Layer.DOMESTIC,
}


def layer_for_channel(channel: Optional[str],
                      default: Layer = Layer.SITREP) -> Layer:
    """Map an inject ``channel`` value onto its layer.

    Canonicalises case, surrounding whitespace and hyphen/underscore
    variants ("Flash-Alert" == "flash_alert"). Unknown or missing channels
    land on the default: SITREP is the common operating picture, so an
    untagged event stays player-visible rather than vanishing.
    """
    if not channel or not isinstance(channel, str):
        return default
    key = channel.strip().lower().replace("-", "_")
    return CHANNEL_LAYER_MAP.get(key, default)
