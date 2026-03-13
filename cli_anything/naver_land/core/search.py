"""Search orchestration — NaverListing data model and search logic."""

from __future__ import annotations

from dataclasses import dataclass

from cli_anything.naver_land.core.districts import (
    District,
    TRADE_TYPES,
    TRADE_TYPE_NAMES,
    find_district,
)
from cli_anything.naver_land.utils.naver_api import NaverLandApiClient


def classify_size(spc1: float) -> str:
    """Classify area into size type based on spc1 (exclusive area in sqm)."""
    if spc1 < 66:
        return "소형"
    elif spc1 <= 99:
        return "20평대"
    elif spc1 <= 132:
        return "30평대"
    else:
        return "중대형"


def sqm_to_pyeong(sqm: float) -> float:
    """Convert square meters to pyeong."""
    return round(sqm / 3.3058, 1)


@dataclass(frozen=True)
class NaverListing:
    atcl_no: str
    atcl_nm: str
    trad_tp_cd: str
    trad_tp_nm: str
    rlet_tp_nm: str
    cortarNo: str
    spc1: float
    spc2: float
    prc: str
    rent_prc: str | None
    lat: float
    lng: float
    flr_info: str | None
    cfm_ymd: str | None
    tag_list: list[str]
    size_type: str
    pyeong: float

    @classmethod
    def from_api_response(cls, item: dict) -> "NaverListing":
        # API returns spc2=전용면적, spc1=공급면적 (reversed from older API)
        # We use spc2 (전용면적) for size classification
        raw_spc1 = _safe_float(item.get("spc1", "0"))
        raw_spc2 = _safe_float(item.get("spc2", "0"))

        # Determine which is 전용 vs 공급: 전용 < 공급 always
        if raw_spc1 > 0 and raw_spc2 > 0:
            exclusive_area = min(raw_spc1, raw_spc2)
            supply_area = max(raw_spc1, raw_spc2)
        else:
            exclusive_area = raw_spc2 if raw_spc2 > 0 else raw_spc1
            supply_area = raw_spc1 if raw_spc1 > 0 else raw_spc2

        trad_tp_cd = item.get("tradTpCd", "")

        # tagList can be a list (new API) or comma-separated string (old API)
        raw_tags = item.get("tagList", "")
        if isinstance(raw_tags, list):
            tags = [str(t).strip() for t in raw_tags if t]
        elif isinstance(raw_tags, str) and raw_tags:
            tags = [t.strip() for t in raw_tags.split(",")]
        else:
            tags = []

        # prc can be numeric (new API) or string; hanPrc has Korean format
        raw_prc = item.get("prc", "")
        han_prc = item.get("hanPrc", "")
        prc_str = han_prc if han_prc else str(raw_prc)

        # rentPrc: 0 means no rent
        raw_rent = item.get("rentPrc", 0)
        rent_prc = str(raw_rent) if raw_rent and raw_rent != 0 else None

        # cfmYmd: try both old and new field names
        cfm_ymd = item.get("atclCfmYmd") or item.get("cfmYmd") or None

        return cls(
            atcl_no=str(item.get("atclNo", "")),
            atcl_nm=item.get("atclNm", ""),
            trad_tp_cd=trad_tp_cd,
            trad_tp_nm=TRADE_TYPE_NAMES.get(trad_tp_cd, item.get("tradTpNm", "")),
            rlet_tp_nm=item.get("rletTpNm", ""),
            cortarNo=item.get("cortarNo", ""),
            spc1=exclusive_area,
            spc2=supply_area,
            prc=prc_str,
            rent_prc=rent_prc,
            lat=_safe_float(item.get("lat", "0")),
            lng=_safe_float(item.get("lng", "0")),
            flr_info=item.get("flrInfo") or None,
            cfm_ymd=cfm_ymd,
            tag_list=tags,
            size_type=classify_size(exclusive_area),
            pyeong=sqm_to_pyeong(exclusive_area),
        )

    def to_dict(self) -> dict:
        return {
            "atcl_no": self.atcl_no,
            "atcl_nm": self.atcl_nm,
            "trad_tp_nm": self.trad_tp_nm,
            "rlet_tp_nm": self.rlet_tp_nm,
            "cortarNo": self.cortarNo,
            "spc1": self.spc1,
            "spc2": self.spc2,
            "pyeong": self.pyeong,
            "size_type": self.size_type,
            "prc": self.prc,
            "rent_prc": self.rent_prc,
            "flr_info": self.flr_info,
            "cfm_ymd": self.cfm_ymd,
            "tag_list": self.tag_list,
        }

    def to_table_row(self) -> list[str]:
        price = self.prc
        if self.rent_prc:
            price = f"{self.prc}/{self.rent_prc}"
        return [
            self.atcl_nm,
            self.trad_tp_nm,
            f"{self.pyeong}평 ({self.spc1}㎡)",
            self.size_type,
            price,
            self.flr_info or "-",
            self.cortarNo,
        ]


def _safe_float(val) -> float:
    try:
        return float(str(val).replace(",", ""))
    except (ValueError, TypeError):
        return 0.0


def search_region(
    district_name: str,
    trade_types: list[str] | None = None,
    property_type: str = "APT",
    sort: str = "rank",
    limit: int = 50,
    client: NaverLandApiClient | None = None,
    on_progress: callable = None,
) -> list[NaverListing]:
    """Search listings in a district.

    Args:
        district_name: Korean name of the district (e.g. "강남구")
        trade_types: List of trade type names (매매/전세/월세/단기임대). None = all.
        property_type: Property type code (APT/VL/OPST/OR/ABYG/JGC/DDDGG).
        sort: Sort order (rank/prc/spc/date).
        limit: Maximum number of results.
        client: Optional API client (created if not provided).
        on_progress: Optional callback(page, total_so_far).

    Returns:
        List of NaverListing objects.
    """
    district = find_district(district_name)
    if district is None:
        raise ValueError(f"구를 찾을 수 없습니다: {district_name}")

    # Build trade type code string
    if trade_types:
        codes = []
        for tt in trade_types:
            code = TRADE_TYPES.get(tt)
            if code is None:
                raise ValueError(f"알 수 없는 거래유형: {tt} (가능: {', '.join(TRADE_TYPES.keys())})")
            codes.append(code)
        trad_tp_cd = ":".join(codes)
    else:
        trad_tp_cd = "A1:B1:B2:B3"

    own_client = client is None
    if own_client:
        client = NaverLandApiClient()

    try:
        raw_articles = client.fetch_all_pages(
            cortarNo=district.cortarNo,
            coord_params=district.coord_params,
            rletTpCd=property_type,
            tradTpCd=trad_tp_cd,
            sort=sort,
            limit=limit,
            on_progress=on_progress,
        )
    finally:
        if own_client:
            client.close()

    listings = []
    for item in raw_articles:
        try:
            listings.append(NaverListing.from_api_response(item))
        except Exception:
            continue

    return listings


def search_complex(
    complex_name: str,
    district_name: str | None = None,
    trade_types: list[str] | None = None,
    property_type: str = "APT",
    limit: int = 50,
    client: NaverLandApiClient | None = None,
) -> list[NaverListing]:
    """Search listings by complex (apartment) name.

    Fetches all listings from the district, then filters by complex name.
    """
    if district_name is None:
        raise ValueError("단지명 검색 시 구(-d)를 지정해야 합니다.")

    all_listings = search_region(
        district_name=district_name,
        trade_types=trade_types,
        property_type=property_type,
        limit=500,
        client=client,
    )

    matched = [
        listing for listing in all_listings
        if complex_name in listing.atcl_nm
    ]

    return matched[:limit]
