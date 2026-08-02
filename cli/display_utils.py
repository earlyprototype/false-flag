"""Shared display helpers for the two CLI front-ends.

cli.main (classic scrolling UI) and cli.main_dashboard (dashboard UI) render
the same post-adjudication output. Keeping that logic here prevents the two
copies from drifting apart ("fixed in one file, not the other" bugs).
"""

import re

import typer
from rich.panel import Panel
from rich.markup import escape as rich_escape

from cli import aesthetics as ae
from cli.rich_ui import console, format_markdown, RICH_ENABLED
from cli.theme import theme_manager, SYMBOLS


_MD_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_MD_ITALIC_RE = re.compile(r"(?<!\*)\*([^*\n]+?)\*(?!\*)")


# Internal persona names (initial_conditions.yaml roles) -> the cabinet titles
# the fiction uses everywhere else. Display-time only: internal IDs, LLM
# prompts, transcripts and save formats keep the original names.
_ROLE_DISPLAY_TITLES = {
    "military commander": "Chief of the Defence Staff",
    "intelligence coordinator": "National Security Advisor",
    "diplomatic lead": "Foreign Secretary",
    "domestic security": "Home Secretary",
    "legal advisor": "Attorney General",
    "government leader": "Prime Minister",
}


def display_role(role: str) -> str:
    """Map an internal persona name to its cabinet title for display.

    Unknown names pass through unchanged, so LLM-invented or already-correct
    speaker labels are unaffected.
    """
    return _ROLE_DISPLAY_TITLES.get(role.strip().lower(), role)


# Quality grades -> in-fiction phrases for immersive/emergent adjudication
# display (classic mode keeps the raw mechanical assessment).
_QUALITY_PHRASES = {
    "exceptional": "Around the table, your advisors regard the response as "
                   "masterly — the right move at the right moment.",
    "good": "Your advisors regard the response as sound.",
    "adequate": "Your advisors regard the response as measured.",
    "poor": "Around the table, your advisors are visibly uneasy about the response.",
    "catastrophic": "Your advisors are alarmed — more than one believes this "
                    "course invites disaster.",
}


def narrative_assessment(reasoning: str) -> str:
    """Rewrite the adjudicator's assessment for immersive/emergent display.

    Replaces the mechanical "Action Quality: ADEQUATE" grade line with an
    in-fiction phrase and drops the "Reasoning:" label. Transcripts and saves
    keep the original text; classic mode displays it unchanged.
    """
    out = []
    for line in reasoning.split("\n"):
        stripped = line.strip()
        lower = stripped.lower()
        if lower.startswith("action quality:"):
            quality = stripped.split(":", 1)[1].strip().lower()
            out.append(_QUALITY_PHRASES.get(
                quality, "Your advisors take stock of the response."))
        elif lower.startswith("reasoning:"):
            out.append(stripped.split(":", 1)[1].strip())
        else:
            out.append(line)
    return "\n".join(out)


def markdown_to_rich(text: str) -> str:
    """Convert basic markdown emphasis (**bold**, *italic*) to Rich markup.

    LLM and scenario text frequently arrives with markdown decoration; anywhere
    it reaches the screen outside a Markdown-rendering panel this keeps players
    from seeing raw asterisks.
    """
    if "*" not in text:
        return text
    text = _MD_BOLD_RE.sub(r"[bold]\1[/bold]", text)
    text = _MD_ITALIC_RE.sub(r"[italic]\1[/italic]", text)
    return text


def format_vibe_line(vibe, colors: dict) -> str:
    """Render a VibeLevel as a Rich-markup line using themed glyphs (no emoji).

    Same information as VibeLevel.to_string() - name, 5-dot level, descriptor,
    trend arrow - with the dots coloured by severity.
    """
    trend_arrow = {"rising": "↗", "falling": "↘", "stable": "→"}.get(vibe.trend, "→")
    if vibe.level >= 4:
        dot_color = colors["danger"]
    elif vibe.level >= 2:
        dot_color = colors["warning"]
    else:
        dot_color = colors["success"]
    filled = "●" * vibe.level
    empty = "○" * (5 - vibe.level)
    dots = f"[{dot_color}]{filled}[/{dot_color}][{colors['muted']}]{empty}[/{colors['muted']}]"
    return f"{vibe.name:<20} {dots} {vibe.descriptor} {trend_arrow}"


def advisor_attitude_lines(narrative_state, include_stance: bool = False) -> list:
    """Plain-text advisor attitude rows (trust bar + relationship).

    Shared by the post-adjudication display and the /status advisors command
    in both CLI front-ends.

    Foreign liaisons (e.g. the US National Security Advisor) are listed in a
    separate WASHINGTON section below the UK cabinet, so they never read as
    members of it.
    """
    def rows(char_attitude):
        trust_level = char_attitude.trust // 20  # 0-5 scale
        trust_bar = "█" * trust_level + "░" * (5 - trust_level)
        relationship_symbol = {
            "allied": "✓",
            "neutral": "○",
            "hostile": "✗",
            "unknown": "?"
        }.get(char_attitude.relationship, "○")
        out = [f"{char_attitude.name:<30} {trust_bar} {relationship_symbol} {char_attitude.relationship.upper()}"]
        if include_stance and char_attitude.stance_summary:
            out.append(f"  {char_attitude.stance_summary}")
        return out

    lines = []
    foreign = []
    for char_id, char_attitude in narrative_state.characters.items():
        if char_id.startswith("uk_"):
            lines.extend(rows(char_attitude))
        else:
            foreign.extend(rows(char_attitude))
    if foreign:
        if lines:
            lines.append("")
        lines.append("──── WASHINGTON " + "─" * 24)
        lines.extend(foreign)
    return lines


def parse_interpretation_simple(interpretation: str) -> dict:
    """Parse LLM interpretation into key sections for display.

    Args:
        interpretation: Full interpretation text

    Returns:
        Dict with parsed sections
    """
    sections = {
        "summary": "",
        "forces": [],
        "timeline": "",
        "concerns": ""
    }

    lines = interpretation.split('\n')
    current_section = None

    for line in lines:
        line = line.strip()

        if line.startswith("INTERPRETATION:"):
            sections["summary"] = line.replace("INTERPRETATION:", "").strip()
        elif line.startswith("FORCES INVOLVED:"):
            # Inline value ("FORCES INVOLVED: a, b") or bullet list on
            # following lines - support both.
            inline = line.replace("FORCES INVOLVED:", "").strip()
            if inline:
                sections["forces"] = [f.strip() for f in inline.split(",") if f.strip()][:5]
            current_section = "forces"
        elif line.startswith("TIMELINE:"):
            inline = line.replace("TIMELINE:", "").strip()
            if inline:
                sections["timeline"] = inline
            current_section = "timeline"
        elif line.startswith("FEASIBILITY:"):
            if "impossible" in line.lower() or "requires clarification" in line.lower():
                sections["concerns"] = line.replace("FEASIBILITY:", "").strip()
            current_section = None
        elif current_section == "forces" and line and line.startswith("*"):
            # Extract force name from bullet point
            force = line.lstrip("* ").split(":")[0] if ":" in line else line.lstrip("* ")
            if force and len(sections["forces"]) < 5:  # Max 5 forces shown
                sections["forces"].append(force)
        elif current_section == "timeline" and line and not sections["timeline"]:
            sections["timeline"] = line

    return sections


def display_decision_summary(action: str, interpretation: str, show_details: bool = False):
    """Display decision interpretation in player-friendly format.

    Args:
        action: Player's original decision text
        interpretation: Full LLM interpretation
        show_details: If True, show full interpretation
    """
    COLORS = theme_manager.get_colors()

    # Show player's exact words in a box
    console.print("")
    console.print(Panel(f"[italic]{rich_escape(action)}[/italic]", title="[bold]YOUR DECISION[/bold]", border_style="white"))
    console.print("")

    if show_details:
        # Show full interpretation
        console.print(Panel(format_markdown(interpretation), title="[bold]FULL INTERPRETATION (DETAILED)[/bold]", border_style="blue"))
        console.print("")
    else:
        # Show simplified summary
        parsed = parse_interpretation_simple(interpretation)

        # Build content for panel
        content = []

        # Show summary if we extracted one
        if parsed["summary"]:
            content.append(markdown_to_rich(parsed["summary"]))
            content.append("")

        # Show key forces
        if parsed["forces"]:
            content.append(f"[{COLORS['success']}]Forces Deployed:[/{COLORS['success']}]")
            for force in parsed["forces"]:
                content.append(f"  • {markdown_to_rich(force)}")
            content.append("")

        # Show timeline
        if parsed["timeline"]:
            content.append(f"[{COLORS['accent']}]Estimated Timeline:[/{COLORS['accent']}] {markdown_to_rich(parsed['timeline'])}")
            content.append("")

        # Show concerns
        if parsed["concerns"]:
            content.append(f"[{COLORS['warning']}]{SYMBOLS['warning']} Operational Concerns: {markdown_to_rich(parsed['concerns'])}[/{COLORS['warning']}]")
            content.append("")

        # Nothing parsed from the structured format: fall back to the raw
        # interpretation (trimmed) rather than showing an empty panel.
        if not any([parsed["summary"], parsed["forces"], parsed["timeline"], parsed["concerns"]]):
            fallback = " ".join(interpretation.split())
            if len(fallback) > 400:
                fallback = fallback[:400].rstrip() + "..."
            content.append(markdown_to_rich(fallback) if fallback else rich_escape(action))
            content.append("")

        # Drop the trailing blank line so the panel ends cleanly
        if content and content[-1] == "":
            content.pop()

        console.print(Panel("\n".join(content), title="[bold]OPERATIONAL ORDER[/bold]", border_style="cyan"))


def strip_effect_boxes(lines: list) -> list:
    """Remove the numeric 'Effect: metric +N (-> value)' boxes from briefing lines.

    Used by immersive/emergent modes, which promise vibes instead of raw numbers.
    The boxes are three lines: a top border, the 'Effect: ...' content, and a
    bottom border.
    """
    out = []
    drop_bottom_border = False
    for line in lines:
        stripped = line.strip()
        if "Effect: " in stripped:
            # Drop the top border that preceded this content line
            if out and out[-1].strip() and set(out[-1].strip()) <= set("┌─┐"):
                out.pop()
            drop_bottom_border = True
            continue
        if drop_bottom_border:
            drop_bottom_border = False
            if stripped and set(stripped) <= set("└─┘"):
                continue
        out.append(line)
    return out


def display_adjudication_results(
    colors: dict,
    play_mode: str,
    reasoning: str,
    final_effects: dict,
    character_responses: list,
    actor_responses: list,
    world,
) -> None:
    """Render the post-adjudication display block.

    Shows the ACTION ASSESSMENT panel, the numeric EFFECTS list (classic mode
    only; immersive and emergent modes communicate consequences through vibes
    and narrative), ADVISOR REACTIONS, and INTERNATIONAL REACTIONS.

    Args:
        colors: Color palette dict in scope at the call site (the dashboard UI
            may be using dashboard.COLORS rather than the theme colors).
        play_mode: "classic", "immersive", or "emergent".
        reasoning: Adjudicator quality-assessment text.
        final_effects: Mapping of metric name -> delta.
        character_responses: List of (char_name, response) tuples.
        actor_responses: List of actor response objects (multi-agent sim).
        world: WorldState, used to resolve actor full names.
    """
    # Non-classic modes speak in fiction: no ALL-CAPS quality grades and no
    # numeric deltas anywhere in the post-adjudication display.
    if play_mode != "classic":
        reasoning = narrative_assessment(reasoning)

    # Display quality reasoning
    typer.echo("")
    if RICH_ENABLED:
        console.print(Panel(format_markdown(reasoning), title=f"[{colors['accent']} bold]ACTION ASSESSMENT[/]", border_style=colors['accent']))
    else:
        typer.echo("=" * 60)
        typer.echo("ACTION ASSESSMENT")
        typer.echo("=" * 60)
        typer.echo("")
        typer.echo(reasoning)
    typer.echo("")

    # Display effects (numeric deltas are classic-mode only; immersive and
    # emergent modes communicate consequences through vibes and narrative)
    if play_mode == "classic":
        if RICH_ENABLED:
            console.print(ae.phase_banner("EFFECTS"))
        else:
            typer.echo("=" * 60)
            typer.echo("EFFECTS")
            typer.echo("=" * 60)
        typer.echo("")

        for metric, delta in final_effects.items():
            if RICH_ENABLED:
                color = colors['success'] if delta > 0 else colors['danger'] if delta < 0 else colors['muted']
                console.print(f"  [{color}]{metric}: {delta:+d}[/{color}]")
            else:
                typer.echo(f"  {metric}: {delta:+d}")
        typer.echo("")

    # Display character responses
    if character_responses:
        if RICH_ENABLED:
            console.print(ae.phase_banner("ADVISOR REACTIONS"))
        else:
            typer.echo("=" * 60)
            typer.echo("ADVISOR REACTIONS")
            typer.echo("=" * 60)
        typer.echo("")

        for char_name, response in character_responses:
            char_name = display_role(char_name)
            if RICH_ENABLED:
                console.print(f"[{colors['secondary']} bold]{rich_escape(char_name)}:[/{colors['secondary']} bold]")
                console.print(f"  \"{rich_escape(response)}\"")
            else:
                typer.echo(f"{char_name}:")
                typer.echo(f"  \"{response}\"")
            typer.echo("")

    # Display international reactions (multi-agent simulation)
    if actor_responses:
        if RICH_ENABLED:
            console.print(ae.phase_banner("INTERNATIONAL REACTIONS"))
        else:
            typer.echo("=" * 60)
            typer.echo("INTERNATIONAL REACTIONS")
            typer.echo("=" * 60)
        typer.echo("")

        for response in actor_responses:
            trust_delta = response.trust_change
            actor_id = response.actor_id

            # Get full name if available
            actor_name = actor_id
            if world.actor_system:
                actor = world.actor_system.get_actor(actor_id)
                if actor:
                    actor_name = actor.full_name

            # Numeric trust deltas are classic-mode only; immersive/emergent
            # let the reaction text carry the weight
            if RICH_ENABLED:
                if play_mode == "classic":
                    color = colors['success'] if trust_delta > 0 else colors['danger'] if trust_delta < 0 else colors['muted']
                    console.print(f"[{colors['primary']} bold]{actor_name}:[/{colors['primary']} bold] [{color}]({trust_delta:+d})[/{color}]")
                else:
                    console.print(f"[{colors['primary']} bold]{actor_name}:[/{colors['primary']} bold]")
                console.print(f"  \"{response.public_response}\"")
            else:
                if play_mode == "classic":
                    typer.echo(f"{actor_name}: ({trust_delta:+d})")
                else:
                    typer.echo(f"{actor_name}:")
                typer.echo(f"  \"{response.public_response}\"")
            typer.echo("")
