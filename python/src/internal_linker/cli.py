"""CLI entry point for the internal linking tool."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click
import yaml

from .config import PipelineConfig
from .pipeline.orchestrator import run_pipeline


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _progress_cli(stage: str, current: int, total: int, detail: str = "") -> None:
    pct = int(current / total * 100) if total else 0
    bar_len = 30
    filled = int(bar_len * current / total) if total else 0
    bar = "█" * filled + "░" * (bar_len - filled)
    click.echo(f"\r  [{bar}] {pct:3d}% | {stage}: {detail}", nl=False)
    if current >= total:
        click.echo()


@click.group()
@click.version_option(version="0.1.0")
def main() -> None:
    """Automate Internal Linking — NLP-powered link suggestion engine."""
    pass


@main.command()
@click.option("--url", "-u", multiple=True, help="URL to analyze (can specify multiple times)")
@click.option("--urls-file", "-f", type=click.Path(exists=True), help="File with one URL per line")
@click.option("--output", "-o", type=click.Path(), default=None, help="Output file path (default: stdout)")
@click.option("--config", "-c", type=click.Path(exists=True), default=None, help="YAML config file")
@click.option("--max-links", type=int, default=None, help="Max suggestions per source page")
@click.option("--format", "output_format", type=click.Choice(["json", "csv"]), default="json")
@click.option("--verbose", "-v", is_flag=True, default=False)
def analyze(
    url: tuple[str, ...],
    urls_file: str | None,
    output: str | None,
    config: str | None,
    max_links: int | None,
    output_format: str,
    verbose: bool,
) -> None:
    """Analyze URLs and suggest internal links."""
    _setup_logging(verbose)

    # Collect URLs
    all_urls: list[str] = list(url)
    if urls_file:
        with open(urls_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    all_urls.append(line)

    if not all_urls:
        click.echo("Error: No URLs provided. Use --url or --urls-file.", err=True)
        sys.exit(1)

    if len(all_urls) < 2:
        click.echo("Error: Need at least 2 URLs to find internal linking opportunities.", err=True)
        sys.exit(1)

    click.echo(f"Analyzing {len(all_urls)} URLs for internal linking opportunities...\n")

    # Load config
    pipeline_config = PipelineConfig()
    if config:
        with open(config) as f:
            overrides = yaml.safe_load(f)
        if overrides:
            pipeline_config = PipelineConfig(**overrides)

    if max_links is not None:
        pipeline_config.max_suggestions_per_source = max_links

    pipeline_config.output_format = output_format

    # Run pipeline
    result = run_pipeline(all_urls, pipeline_config, on_progress=_progress_cli)

    # Output
    if result.errors:
        click.echo(f"\nWarnings: {len(result.errors)}", err=True)
        for err in result.errors:
            click.echo(f"  - {err}", err=True)

    click.echo(f"\n{json.dumps(result.stats, indent=2)}")

    if output_format == "json":
        json_output = result.to_json()
        if output:
            Path(output).write_text(json_output, encoding="utf-8")
            click.echo(f"\nResults written to {output}")
        else:
            click.echo(json_output)
    elif output_format == "csv":
        _write_csv(result, output)


def _write_csv(result, output_path: str | None) -> None:
    """Write results as CSV."""
    import csv
    import io

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "source_url", "target_url", "anchor_text", "confidence_score",
        "match_reason", "risk_flags", "context_snippet",
        "paragraph_index", "sentence_index",
    ])

    for source_url, suggestions in result.suggestions.items():
        for s in suggestions:
            writer.writerow([
                s.source_url,
                s.target_url,
                s.anchor_text,
                s.confidence_score,
                s.match_reason,
                "; ".join(s.risk_flags),
                s.context_snippet,
                s.insertion_hint.paragraph_index if s.insertion_hint else "",
                s.insertion_hint.sentence_index if s.insertion_hint else "",
            ])

    csv_text = buf.getvalue()
    if output_path:
        Path(output_path).write_text(csv_text, encoding="utf-8")
        click.echo(f"\nCSV results written to {output_path}")
    else:
        click.echo(csv_text)


if __name__ == "__main__":
    main()
