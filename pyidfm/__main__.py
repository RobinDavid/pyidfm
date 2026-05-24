import dataclasses
import json
import logging
import sys
from datetime import datetime, timezone

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from pyidfm.idfm import IDFMApi
from pyidfm.dataset import Dataset
from pyidfm.models import TransportType

console = Console()


# ---------------------------------------------------------------------------
# JSON serialization helpers
# ---------------------------------------------------------------------------

def _json_default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, tuple):
        return list(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _to_json(data: list | object) -> str:
    if isinstance(data, list):
        return json.dumps([dataclasses.asdict(d) for d in data], default=_json_default, indent=2)
    return json.dumps(dataclasses.asdict(data), default=_json_default, indent=2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.group()
@click.option("--debug", is_flag=True, default=False, help="Enable debug logging.")
@click.pass_context
def cli(ctx: click.Context, debug: bool):
    """pyidfm — Île-de-France Mobilités CLI."""
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )


# ── search ──────────────────────────────────────────────────────────────────

@cli.group()
def search():
    """Search static data (lines, stops) from local IDFM datasets."""
    pass


@search.command("lines")
@click.option(
    "--mode",
    type=click.Choice([t.value for t in TransportType]),
    default=None,
    help="Filter by transport mode.",
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def search_lines(mode: str | None, as_json: bool):
    """List available lines, optionally filtered by transport mode."""
    dataset = Dataset()

    modes = [mode] if mode else list(dataset.lines.keys())

    results = []
    for m in modes:
        if m in dataset.lines:
            for name, line_id in dataset.lines[m].items():
                results.append({"mode": m, "name": name, "id": line_id})

    if as_json:
        print(json.dumps(results, indent=2))
        return

    table = Table(title="Lines")
    table.add_column("Mode", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("ID", style="yellow")
    for r in results:
        table.add_row(r["mode"], r["name"], r["id"])
    console.print(table)


@search.command("stops")
@click.argument("line_id")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def search_stops(line_id: str, as_json: bool):
    """List stops for a given LINE_ID (use 'search lines' to find IDs)."""
    # dataset = Dataset()

    idfm = IDFMApi(None)

    stops = idfm.get_stops(line_id)
    if not stops:
        click.echo(f"No stops found for line ID '{line_id}'.", err=True)
        sys.exit(1)

    if as_json:
        print(json.dumps(stops, indent=2))
        return

    table = Table(title=f"Stops for line {line_id}")
    table.add_column("Name", style="green")
    table.add_column("City", style="cyan")
    table.add_column("Stop ID", style="yellow")
    table.add_column("Exchange Area ID", style="blue")
    table.add_column("Exchange Area", style="magenta")
    for s in stops:
        table.add_row(
            s.name,
            s.city,
            s.stop_id,
            s.exchange_area_id,
            s.exchange_area_name
        )
    console.print(table)


# ── traffic ──────────────────────────────────────────────────────────────────

@cli.command("traffic")
@click.option(
    "--stop-id",
    required=True,
    help="Stop area ID (use 'search stops' to find IDs).",
)
@click.option(
    "--apikey",
    envvar="IDFM_API_KEY",
    required=True,
    help="IDFM API key (or set IDFM_API_KEY env var).",
)
@click.option("--line-id", default=None, help="Filter by line ID.")
@click.option("--destination", default=None, help="Filter by destination name.")
@click.option("--direction", default=None, help="Filter by direction name.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def traffic(
    stop_id: str,
    apikey: str,  # noqa: stop_id comes from --stop-id, click converts kebab to snake
    line_id: str | None,
    destination: str | None,
    direction: str | None,
    as_json: bool,
):
    """Get next schedules for a stop (STOP_ID)."""
    idfm = IDFMApi(apikey)
    results = idfm.get_traffic(
        stop_id,
        destination_name=destination,
        direction_name=direction,
        line_id=line_id,
    )

    if as_json:
        print(_to_json(results))
        return

    if not results:
        print("No schedules found.")
        return

    _sentinel = datetime.max.replace(tzinfo=timezone.utc)
    sorted_results = sorted(results, key=lambda t: t.schedule or _sentinel)

    groups: dict[str, list] = {}
    for t in sorted_results:
        groups.setdefault(t.line_id, []).append(t)

    for line_id, entries in groups.items():
        line_name = idfm.get_line(line_id)
        table = Table(title=f"{line_name} ({line_id})", show_lines=False)
        table.add_column("Time", style="cyan", no_wrap=True)
        table.add_column("Status", style="yellow")
        table.add_column("Stop", style="magenta")
        table.add_column("Destination", style="green")
        table.add_column("Direction")
        table.add_column("Platform")
        table.add_column("Note")

        for t in entries:
            local_time = t.schedule.astimezone().strftime("%H:%M:%S") if t.schedule else "N/A"
            status = t.status.value if t.status else ""
            if t.delayed:
                status += " [DELAYED]"
            
            if t.note and t.call_note:
                note = f"{t.note} / {t.call_note}"
            else:
                note = t.note or t.call_note or ""

            table.add_row(
                local_time,
                status,
                t.stop_point_name + (f" (a quai!)" if t.at_stop else ""),
                t.destination_name or "",
                t.direction or "",
                t.platform or "",
                note,
            )

        console.print(table)


# ── line-report ───────────────────────────────────────────────────────────────

@cli.command("line-report")
@click.argument("line_id")
@click.option(
    "--apikey",
    envvar="IDFM_API_KEY",
    required=True,
    help="IDFM API key (or set IDFM_API_KEY env var).",
)
@click.option(
    "--include-elevators",
    is_flag=True,
    default=False,
    help="Include elevator failure reports.",
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def line_report(line_id: str, apikey: str, include_elevators: bool, as_json: bool):
    """Get traffic disruption reports for a line (LINE_ID)."""
    api = IDFMApi(apikey)
    results = api.get_line_reports(line_id, exclude_elevator=not include_elevators)

    if as_json:
        print(_to_json(results))
        return

    if not results:
        print("No disruptions reported.")
        return

    for r in results:
        periods_str = ", ".join(
            f"{start.strftime('%d/%m %H:%M')} → {end.strftime('%d/%m %H:%M')}"
            for start, end in r.periods
        )

        meta = Table.grid(padding=(0, 2))
        meta.add_column(style="bold")
        meta.add_column()
        meta.add_row("Type", r.type or "")
        meta.add_row("Severity", str(r.severity))
        meta.add_row("Effect", r.effect or "")
        meta.add_row("Cause", r.cause or "")
        meta.add_row("Periods", periods_str)
        if r.message:
            meta.add_row("Details", r.message)

        title = Text(r.name or r.id, style="bold yellow")
        console.print(Panel(meta, title=title, border_style="blue"))


# ── messages ──────────────────────────────────────────────────────────────────

@cli.command("messages")
@click.option(
    "--apikey",
    envvar="IDFM_API_KEY",
    required=True,
    help="IDFM API key (or set IDFM_API_KEY env var).",
)
@click.option("--line-id", default=None, help="Filter by line ID (mutually exclusive with --stop-id).")
@click.option("--stop-id", default=None, help="Filter by stop ID (mutually exclusive with --line-id).")
@click.option(
    "--channel",
    type=click.Choice(["Information", "Perturbation", "Commercial"]),
    default=None,
    help="Filter by message channel.",
)
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
def messages(apikey: str, line_id: str | None, stop_id: str | None, channel: str | None, as_json: bool):
    """Get traffic messages for a line or stop."""
    if line_id and stop_id:
        raise click.UsageError("--line-id and --stop-id are mutually exclusive.")

    api = IDFMApi(apikey)
    try:
        stop_id = int(stop_id) if stop_id else None
    except ValueError:
        pass
    results = api.get_messages(line_id=line_id, stop_id=stop_id, channel=channel)

    if as_json:
        print(json.dumps(results, indent=2))
        return

    if not results:
        print("No messages found.")
        return

    for msg in results:
        console.print(Panel(json.dumps(msg, indent=2), border_style="cyan"))


# ---------------------------------------------------------------------------

def main():
    cli()


if __name__ == "__main__":
    main()
