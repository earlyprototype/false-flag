"""Shared display helpers for the two CLI front-ends.

cli.main (classic scrolling UI) and cli.main_dashboard (dashboard UI) render
the same post-adjudication output. Keeping that logic here prevents the two
copies from drifting apart ("fixed in one file, not the other" bugs).
"""

import typer
from rich.panel import Panel
from rich.markup import escape as rich_escape

from cli.rich_ui import console, format_markdown, RICH_ENABLED


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
            console.print(f"[{colors['accent']} bold]EFFECTS[/]")
            console.print(f"[{colors['accent']}]" + "═" * 60 + f"[/{colors['accent']}]")
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
            console.print(f"[{colors['accent']} bold]ADVISOR REACTIONS[/]")
            console.print(f"[{colors['accent']}]" + "═" * 60 + f"[/{colors['accent']}]")
        else:
            typer.echo("=" * 60)
            typer.echo("ADVISOR REACTIONS")
            typer.echo("=" * 60)
        typer.echo("")

        for char_name, response in character_responses:
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
            console.print(f"[{colors['accent']} bold]INTERNATIONAL REACTIONS[/]")
            console.print(f"[{colors['accent']}]" + "═" * 60 + f"[/{colors['accent']}]")
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

            if RICH_ENABLED:
                color = colors['success'] if trust_delta > 0 else colors['danger'] if trust_delta < 0 else colors['muted']
                console.print(f"[{colors['primary']} bold]{actor_name}:[/{colors['primary']} bold] [{color}]({trust_delta:+d})[/{color}]")
                console.print(f"  \"{response.public_response}\"")
            else:
                typer.echo(f"{actor_name}: ({trust_delta:+d})")
                typer.echo(f"  \"{response.public_response}\"")
            typer.echo("")
