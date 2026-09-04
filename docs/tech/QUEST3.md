# Meta Quest 3

The Meta Quest 3 is the target device for measuring the WebXR operations room.
This brief records only the project-relevant checks; current platform setup
steps must be rechecked against Meta's documentation when the device is in
hand.

## Hardware facts that matter here

- **Standalone browser target.** The WebXR room opens in the headset browser;
  the laptop still serves the game session and may render the streamed screen
  source.
- **Composition-layer target.** The local-rendering branch requires WebXR
  layers, including a quad layer for the situation screen. Support must be
  proved on the device; the standard alone is not a compatibility guarantee
  (see [WEBXR.md](WEBXR.md)).
- **Label-heavy screens are plausible, not proved.** Quest 3's published
  resolution and optics justify testing this route, but the actual globe's
  legibility remains an on-device acceptance measurement.
- **Colour passthrough.** The headset can show the real room in colour
  behind virtual content, so a demo can keep users oriented in the space.
- **USB development path.** A data-capable USB-C connection is useful for
  device setup and debugging; exact current Meta tooling is checked when the
  device arrives.
- **Quest 3S** is the budget sibling and acceptable here — #75 asks about
  any Quest headset, and [#128](https://github.com/earlyprototype/false-flag/issues/128)
  records the 3S as acceptable.

## Sourcing state

Open — issue #75 ("is a Quest headset available to you?"). The owner's
comment on the issue is "Likely - will reach out to contact," but availability
remains unconfirmed. It gates the measurement, not the portable room build.
CesiumJS running flat in the Quest browser at usable frame times remains
unproven.

## On-device measurement procedure

1. Confirm the headset, browser and development tooling are updated and that
   the laptop page is reachable over the test network.
2. Open the shipped globe at `/globe?game=<session id>` and record frame time,
   thermal behaviour and label legibility.
3. Open the portable WebXR room and repeat the measurement with the screen
   active.
4. Test input latency and recovery after headset sleep or page reload.
5. Record the result against the acceptance fields in
   [`PLAN.md`](../../PLAN.md#xr-ops-room). That evidence chooses
   the local quad-layer or streamed-source branch.

## References

- [Canonical XR Ops Room stream](../../PLAN.md#xr-ops-room)
- [WebXR room brief](WEBXR.md)
- [WebXR Layers specification](https://immersive-web.github.io/layers/)
- [Meta Quest Browser overview](https://developers.meta.com/horizon/documentation/web/)
- [Meta Quest Browser feature-detection guidance](https://developers.meta.com/horizon/documentation/web/browser-specs/)
- [Meta Quest Browser USB debugging](https://developers.meta.com/horizon/documentation/web/browser-remote-debugging/)
- [Meta Quest 3 device comparison](https://developers.meta.com/horizon/resources/device-optimization-comparison/)
- [Quest availability issue #75](https://github.com/earlyprototype/false-flag/issues/75)
