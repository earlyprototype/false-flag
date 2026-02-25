from terminaltexteffects.effects import typewriter, slide
import time

def main() -> None:
    # Intro line with typewriter effect
    effect = typewriter.Typewriter("Good evening, I'm your AI news anchor...", speed=45)
    effect.run()
    time.sleep(0.8)

    # Simple ticker using slide effect for a few headlines
    headlines = [
        "BREAKING: Terminal text effects demo running",
        "WEATHER: Clear skies expected",
        "SPORTS: Local team wins again",
    ]
    for h in headlines:
        slide.Slide(h, direction="left").run()
        time.sleep(0.5)

if __name__ == "__main__":
    main()


