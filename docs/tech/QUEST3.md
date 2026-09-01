# Meta Quest 3

The Meta Quest 3 is a standalone VR headset: untethered, running its own
Android-based OS, carrying the reference WebXR browser. It is the hardware
either VR route (#127) would run on.

*Hardware facts here are general knowledge except where an issue or repo doc
is cited.*

## Hardware facts that matter here

- **Standalone.** No PC required to run either candidate room build: a Unity
  app installs on the device; a WebXR page opens in the built-in browser.
- **Reference WebXR browser.** The built-in Meta Quest Browser is the
  reference target for WebXR content, including quad layers for crisp
  in-headset text — a Quest-only benefit (see WEBXR.md).
- **Optics sufficient for label-heavy screens.** Good enough to read a
  label-dense situation screen in-headset, which is what the globe is.
- **Colour passthrough.** The headset can show the real room in colour
  behind virtual content, so a demo can keep users oriented in the space.
- **USB-C Link for tethered development.** A Link cable connects the headset
  to the development laptop.
- **Quest 3S** is the budget sibling and acceptable here — #75 asks about
  any Quest headset, and #128 records the 3S as acceptable.
- **"Oculus" is the retired brand name.** Older docs and search results that
  say Oculus mean the same product line.

## Sourcing state

Open — issue #75 ("is a Quest headset available to you?"). The owner's
comment on the issue: "Likely - will reach out to contact." PLAN.md records
the working default: assumed yes; the issue stays open until confirmed.
Availability gates the on-device work: `docs/XR_GLOBE_FEASIBILITY.md` gates
the local in-headset variants on an on-device check, because CesiumJS
running flat in the Quest browser at usable framerates is unproven.

## Day one with the device

1. **Enable developer mode** on the headset (needs a Meta account and the
   phone app). Required for installing development builds and USB debugging.
2. **Plug in the Link cable** (USB-C) to the development laptop.
3. **First smoke test: open the globe page in the headset browser.** Start
   the laptop server, put headset and laptop on the same network, and browse
   to the laptop's address at `/globe?game=<session id>` in the Quest
   browser. This single test answers the unproven question above — whether
   the shipped CesiumJS page runs at usable framerates on the device —
   before any route-specific work.
