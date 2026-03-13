#!/usr/bin/env python3
"""Naver Land CLI — Search apartments for sale/rent via Naver Real Estate API.

Usage:
    # Search by district
    cli-anything-naver-land search region -d 강남구 -t 매매
    cli-anything-naver-land search region -d 서초구 -t 전세 --type 30평대

    # Search by complex name
    cli-anything-naver-land search complex -n 래미안 -d 강남구

    # JSON output
    cli-anything-naver-land --json search region -d 종로구 -n 5

    # Interactive REPL
    cli-anything-naver-land
"""

from __future__ import annotations

import sys
import os
import json

import click
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli_anything.naver_land.core.session import Session
from cli_anything.naver_land.core.districts import (
    TRADE_TYPES,
    PROPERTY_TYPES,
    SORT_OPTIONS,
    find_city,
    find_district,
    list_cities,
    list_districts,
    load_districts,
)
from cli_anything.naver_land.core.search import (
    search_region as do_search_region,
    search_complex as do_search_complex,
    NaverListing,
)
from cli_anything.naver_land.core.filter import FilterCriteria, apply_filters
from cli_anything.naver_land.core import export as export_mod
from cli_anything.naver_land.utils.formatters import format_table, format_json, format_summary

_session: Optional[Session] = None
_json_output = False
_repl_mode = False
_current_listings: list[NaverListing] = []
_current_filter: FilterCriteria = FilterCriteria()
_config: dict = {
    "delay_mean": 5.0,
    "delay_std": 1.5,
    "delay_min": 3.0,
    "delay_max": 10.0,
}


def get_session() -> Session:
    global _session
    if _session is None:
        from pathlib import Path
        sf = str(Path.home() / ".cli-anything-naver-land" / "session.json")
        _session = Session(session_file=sf)
    return _session


def output(data, message: str = ""):
    if _json_output:
        click.echo(json.dumps(data, indent=2, default=str, ensure_ascii=False))
    else:
        if message:
            click.echo(message)
        if isinstance(data, dict):
            _print_dict(data)
        elif isinstance(data, list) and data and not isinstance(data[0], NaverListing):
            _print_list(data)


def _print_dict(d: dict, indent: int = 0):
    prefix = "  " * indent
    for k, v in d.items():
        if isinstance(v, dict):
            click.echo(f"{prefix}{k}:")
            _print_dict(v, indent + 1)
        elif isinstance(v, list):
            click.echo(f"{prefix}{k}:")
            _print_list(v, indent + 1)
        else:
            click.echo(f"{prefix}{k}: {v}")


def _print_list(items: list, indent: int = 0):
    prefix = "  " * indent
    for i, item in enumerate(items):
        if isinstance(item, dict):
            click.echo(f"{prefix}[{i}]")
            _print_dict(item, indent + 1)
        else:
            click.echo(f"{prefix}- {item}")


def handle_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValueError, RuntimeError, FileNotFoundError, TimeoutError) as e:
            if _json_output:
                click.echo(json.dumps({"error": str(e), "type": type(e).__name__}))
            else:
                click.echo(f"Error: {e}", err=True)
            if not _repl_mode:
                sys.exit(1)
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


# ── Main CLI Group ──────────────────────────────────────────────

@click.group(invoke_without_command=True)
@click.option("--json", "use_json", is_flag=True, help="Output as JSON")
@click.pass_context
def cli(ctx, use_json):
    """Naver Land CLI — 전국 부동산 매물 검색 (네이버 부동산)"""
    global _json_output
    _json_output = use_json
    ctx.ensure_object(dict)

    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


# ── Search Command Group ────────────────────────────────────────

@cli.group()
def search():
    """Search listings — by region or complex name."""
    pass


@search.command("region")
@click.option("--city", "-c", default=None, help="시/도 (예: 서울시, 부산시, 경기도)")
@click.option("--district", "-d", required=True, help="구/군/시 이름 (필수)")
@click.option("--trade-type", "-t", multiple=True,
              help="거래유형: 매매/전세/월세/단기임대 (복수 가능)")
@click.option("--property", "-p", "property_type",
              default=None, help="부동산 유형 (기본: APT:JGC)")
@click.option("--type", "size_type",
              type=click.Choice(["소형", "20평대", "30평대", "중대형"]),
              default=None, help="평형 분류")
@click.option("--min-area", type=float, default=None, help="최소 전용면적(㎡)")
@click.option("--max-area", type=float, default=None, help="최대 전용면적(㎡)")
@click.option("--min-price", default=None, help="최소 가격 (예: 5억, 50000)")
@click.option("--max-price", default=None, help="최대 가격 (예: 15억)")
@click.option("--floor", default=None, help="층 필터 (예: 10+, 3-10)")
@click.option("--sort", type=click.Choice(list(SORT_OPTIONS.keys())),
              default="rank", help="정렬")
@click.option("--limit", "-n", type=int, default=1000, help="최대 결과 수 (기본: 전체)")
@handle_error
def search_region(city, district, trade_type, property_type, size_type,
                  min_area, max_area, min_price, max_price, floor, sort, limit):
    """Search listings in a district (전국 지원)."""
    global _current_listings, _current_filter

    trade_types = list(trade_type) if trade_type else None

    # If city specified, load its districts
    if city:
        city_obj = find_city(city)
        if city_obj:
            load_districts(city_obj.code)

    # property_type: None → use default (APT:JGC), or user-specified
    effective_property = property_type or "APT:JGC"

    if not _json_output:
        district_obj = find_district(district, city_name=city)
        if district_obj:
            trade_desc = ", ".join(trade_types) if trade_types else "전체"
            prop_desc = effective_property
            city_desc = district_obj.city_name
            click.echo(f"  검색: {city_desc} {district_obj.name} | {prop_desc} | {trade_desc}")

    def on_progress(page, total):
        if not _json_output:
            click.echo(f"  ... 페이지 {page} ({total}건 수집)")

    listings = do_search_region(
        district_name=district,
        trade_types=trade_types,
        property_type=effective_property,
        sort=sort,
        limit=limit,
        on_progress=on_progress,
        city_name=city,
    )

    criteria = FilterCriteria(
        size_type=size_type,
        min_area=min_area,
        max_area=max_area,
        min_price=min_price,
        max_price=max_price,
        floor=floor,
    )

    if not criteria.is_empty:
        listings = apply_filters(listings, criteria)
        _current_filter = criteria

    _current_listings = listings

    sess = get_session()
    sess.record("search region", {
        "district": district,
        "trade_types": trade_types,
        "property_type": property_type,
        "limit": limit,
    }, {"count": len(listings)})

    if _json_output:
        output([l.to_dict() for l in listings])
    else:
        format_table(listings)
        summary = format_summary(listings, district)
        if summary.get("trade_types"):
            parts = [f"{k}: {v}" for k, v in summary["trade_types"].items()]
            click.echo(f"  거래유형: {', '.join(parts)}")
        if summary.get("size_types"):
            parts = [f"{k}: {v}" for k, v in summary["size_types"].items()]
            click.echo(f"  평형분류: {', '.join(parts)}")


@search.command("complex")
@click.option("--name", "-n", required=True, help="단지명 (부분 일치)")
@click.option("--district", "-d", required=True, help="구/군/시 이름")
@click.option("--city", "-c", default=None, help="시/도 (예: 부산시, 경기도)")
@click.option("--trade-type", "-t", multiple=True,
              help="거래유형: 매매/전세/월세/단기임대")
@click.option("--property", "-p", "property_type",
              default=None, help="부동산 유형 (기본: APT:JGC)")
@click.option("--limit", "-n", "max_results", type=int, default=1000, help="최대 결과 수")
@handle_error
def search_complex(name, district, city, trade_type, property_type, max_results):
    """Search listings by complex (apartment) name — 전국 지원."""
    global _current_listings

    trade_types = list(trade_type) if trade_type else None
    effective_property = property_type or "APT:JGC"

    if city:
        city_obj = find_city(city)
        if city_obj:
            load_districts(city_obj.code)

    if not _json_output:
        city_desc = f"{city} " if city else ""
        click.echo(f"  단지명 검색: '{name}' in {city_desc}{district}")

    listings = do_search_complex(
        complex_name=name,
        district_name=district,
        trade_types=trade_types,
        property_type=effective_property,
        limit=max_results,
        city_name=city,
    )

    _current_listings = listings

    sess = get_session()
    sess.record("search complex", {
        "name": name, "district": district,
    }, {"count": len(listings)})

    if _json_output:
        output([l.to_dict() for l in listings])
    else:
        format_table(listings)


@search.command("cities")
@handle_error
def search_cities():
    """List all supported cities/provinces (시/도 목록)."""
    cities = list_cities()
    if _json_output:
        output([{"code": c.code, "name": c.name, "cortarNo": c.cortarNo}
                for c in cities])
    else:
        click.echo(f"  지원 시/도 ({len(cities)}개):")
        for c in cities:
            click.echo(f"    {c.name} (코드: {c.code})")


@search.command("districts")
@click.option("--city", "-c", default=None, help="시/도 (미지정 시 서울)")
@handle_error
def search_districts(city):
    """List districts in a city (구/군 목록)."""
    try:
        districts = list_districts(city_name=city)
    except ValueError as e:
        raise ValueError(str(e))
    city_label = city if city else "서울시"
    if _json_output:
        output([{"code": d.code, "name": d.name, "city": d.city_name, "cortarNo": d.cortarNo}
                for d in districts])
    else:
        click.echo(f"  {city_label} 지역 ({len(districts)}개):")
        for d in districts:
            click.echo(f"    {d.name} (코드: {d.code}, cortarNo: {d.cortarNo})")


# ── Filter Command Group ────────────────────────────────────────

@cli.group()
def filter():
    """Filter current results — apply, clear, show."""
    pass


@filter.command("apply")
@click.option("--type", "size_type",
              type=click.Choice(["소형", "20평대", "30평대", "중대형"]),
              default=None, help="평형 분류")
@click.option("--min-area", type=float, default=None, help="최소 전용면적(㎡)")
@click.option("--max-area", type=float, default=None, help="최대 전용면적(㎡)")
@click.option("--min-price", default=None, help="최소 가격")
@click.option("--max-price", default=None, help="최대 가격")
@click.option("--floor", default=None, help="층 필터")
@handle_error
def filter_apply(size_type, min_area, max_area, min_price, max_price, floor):
    """Apply additional filters to current results."""
    global _current_listings, _current_filter

    if not _current_listings:
        raise ValueError("필터를 적용할 검색 결과가 없습니다. 먼저 search를 실행하세요.")

    criteria = FilterCriteria(
        size_type=size_type,
        min_area=min_area,
        max_area=max_area,
        min_price=min_price,
        max_price=max_price,
        floor=floor,
    )

    _current_listings = apply_filters(_current_listings, criteria)
    _current_filter = criteria

    if _json_output:
        output([l.to_dict() for l in _current_listings])
    else:
        click.echo(f"  필터 적용 완료: {len(_current_listings)}건")
        format_table(_current_listings)


@filter.command("clear")
@handle_error
def filter_clear():
    """Clear all filters (requires re-search)."""
    global _current_filter
    _current_filter = FilterCriteria()
    click.echo("  필터가 초기화되었습니다.")


@filter.command("show")
@handle_error
def filter_show():
    """Show current filter criteria."""
    if _current_filter.is_empty:
        output({}, "  적용된 필터 없음")
    else:
        output(_current_filter.to_dict(), "  현재 필터:")


# ── Export Command Group ────────────────────────────────────────

@cli.group()
def export():
    """Export results — CSV, JSON, Excel."""
    pass


@export.command("csv")
@click.option("--output", "-o", "output_path", required=True, help="출력 파일 경로")
@handle_error
def export_csv(output_path):
    """Export current results to CSV."""
    if not _current_listings:
        raise ValueError("내보낼 검색 결과가 없습니다.")
    result = export_mod.export_csv(_current_listings, output_path)
    sess = get_session()
    sess.record("export csv", {"path": output_path}, result)
    output(result, f"  CSV 저장 완료: {result['path']} ({result['count']}건, {result['size']:,} bytes)")


@export.command("json")
@click.option("--output", "-o", "output_path", required=True, help="출력 파일 경로")
@handle_error
def export_json_cmd(output_path):
    """Export current results to JSON."""
    if not _current_listings:
        raise ValueError("내보낼 검색 결과가 없습니다.")
    result = export_mod.export_json(_current_listings, output_path)
    sess = get_session()
    sess.record("export json", {"path": output_path}, result)
    output(result, f"  JSON 저장 완료: {result['path']} ({result['count']}건, {result['size']:,} bytes)")


@export.command("excel")
@click.option("--output", "-o", "output_path", required=True, help="출력 파일 경로")
@handle_error
def export_excel(output_path):
    """Export current results to Excel."""
    if not _current_listings:
        raise ValueError("내보낼 검색 결과가 없습니다.")
    result = export_mod.export_excel(_current_listings, output_path)
    sess = get_session()
    sess.record("export excel", {"path": output_path}, result)
    output(result, f"  Excel 저장 완료: {result['path']} ({result['count']}건, {result['size']:,} bytes)")


# ── Config Command Group ────────────────────────────────────────

@cli.group()
def config():
    """Configuration management."""
    pass


@config.command("set")
@click.argument("key")
@click.argument("value")
@handle_error
def config_set(key, value):
    """Set a configuration value."""
    if key in _config:
        try:
            _config[key] = type(_config[key])(value)
        except (ValueError, TypeError):
            _config[key] = value
    else:
        _config[key] = value
    output({"key": key, "value": _config[key]}, f"  설정: {key} = {_config[key]}")


@config.command("get")
@click.argument("key", required=False)
@handle_error
def config_get(key):
    """Get configuration value(s)."""
    if key:
        val = _config.get(key)
        output({"key": key, "value": val}, f"  {key} = {val}")
    else:
        output(_config, "  설정:")


# ── Session Command Group ───────────────────────────────────────

@cli.group()
def session():
    """Session management — history, undo, redo."""
    pass


@session.command("status")
def session_status():
    """Show session status."""
    sess = get_session()
    output(sess.status())


@session.command("history")
@click.option("--limit", "-n", type=int, default=20, help="Max entries")
def session_history(limit):
    """Show command history."""
    sess = get_session()
    entries = sess.history(limit=limit)
    if not entries:
        output([], "  히스토리 없음")
        return
    output(entries, f"  히스토리 ({len(entries)}건):")


@session.command("undo")
def session_undo():
    """Undo last command."""
    sess = get_session()
    entry = sess.undo()
    if entry:
        output(entry.to_dict(), f"  되돌림: {entry.command}")
    else:
        output({"error": "Nothing to undo"}, "  되돌릴 항목이 없습니다.")


@session.command("redo")
def session_redo():
    """Redo last undone command."""
    sess = get_session()
    entry = sess.redo()
    if entry:
        output(entry.to_dict(), f"  다시실행: {entry.command}")
    else:
        output({"error": "Nothing to redo"}, "  다시실행할 항목이 없습니다.")


@session.command("save")
@click.option("--output", "-o", "output_path", default=None, help="저장 경로")
def session_save(output_path):
    """Save session to file."""
    sess = get_session()
    if output_path:
        sess.save(output_path)
        click.echo(f"  세션 저장: {output_path}")
    else:
        click.echo("  세션이 자동 저장되었습니다.")


@session.command("load")
@click.argument("path")
def session_load(path):
    """Load session from file."""
    global _session
    _session = Session(session_file=path)
    click.echo(f"  세션 로드: {path} ({_session.history_count}건)")


# ── REPL ────────────────────────────────────────────────────────

@cli.command("repl", hidden=True)
def repl():
    """Enter interactive REPL mode."""
    global _repl_mode
    _repl_mode = True

    from cli_anything.naver_land.utils.repl_skin import ReplSkin

    skin = ReplSkin("naver_land", version="1.0.0")
    skin.print_banner()

    pt_session = skin.create_prompt_session()

    commands = {
        "search region -d <구>": "지역 검색 (예: search region -d 강남구 -t 매매)",
        "search region -c <시/도> -d <구>": "전국 검색 (예: search region -c 부산시 -d 해운대구)",
        "search complex -n <이름> -d <구>": "단지명 검색",
        "search cities": "지원 시/도 목록",
        "search districts [-c <시/도>]": "구/군 목록 (미지정 시 서울)",
        "filter apply": "필터 적용 (--type, --min-price 등)",
        "filter clear": "필터 초기화",
        "filter show": "현재 필터 보기",
        "export csv -o <파일>": "CSV 내보내기",
        "export json -o <파일>": "JSON 내보내기",
        "export excel -o <파일>": "Excel 내보내기",
        "config set <key> <val>": "설정 변경",
        "config get [key]": "설정 조회",
        "session history": "명령 히스토리",
        "session undo": "되돌리기",
        "session redo": "다시실행",
        "help": "도움말",
        "quit / exit": "종료",
    }

    while True:
        try:
            line = skin.get_input(pt_session, context="naver_land")
        except (EOFError, KeyboardInterrupt):
            skin.print_goodbye()
            break

        if not line:
            continue
        if line in ("quit", "exit", "q"):
            skin.print_goodbye()
            break
        if line == "help":
            skin.help(commands)
            continue

        parts = line.split()
        try:
            cli.main(parts, standalone_mode=False)
        except SystemExit:
            pass
        except click.exceptions.UsageError as e:
            skin.error(str(e))
        except Exception as e:
            skin.error(str(e))


def main():
    cli()


if __name__ == "__main__":
    main()
