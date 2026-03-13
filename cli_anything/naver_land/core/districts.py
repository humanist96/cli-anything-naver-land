"""District data — Seoul 25 districts with bounding box coordinates for Naver Land API."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class District:
    code: str
    name: str
    city_code: str
    city_name: str
    zoom: int
    btm: float
    lft: float
    top: float
    rgt: float

    @property
    def cortarNo(self) -> str:
        return f"{self.city_code}{self.code}00000"

    @property
    def coord_params(self) -> str:
        return (
            f"&z={self.zoom}"
            f"&btm={self.btm}&lft={self.lft}"
            f"&top={self.top}&rgt={self.rgt}"
        )


def _parse_coords(s: str) -> dict:
    """Parse coordinate string like '&z=13&btm=37.5138176&lft=126.8804177&top=37.6321853&rgt=127.0788583'."""
    params = {}
    for part in s.strip("&").split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            params[k] = v
    return params


def _build_district(code: str, name: str, coord_str: str,
                    city_code: str = "11", city_name: str = "서울시") -> District:
    p = _parse_coords(coord_str)
    return District(
        code=code,
        name=name,
        city_code=city_code,
        city_name=city_name,
        zoom=int(p.get("z", 13)),
        btm=float(p["btm"]),
        lft=float(p["lft"]),
        top=float(p["top"]),
        rgt=float(p["rgt"]),
    )


# Seoul 25 districts — extracted from crawl_naver.py
_SEOUL_DATA = {
    "110": ("종로구", "&z=13&btm=37.5138176&lft=126.8804177&top=37.6321853&rgt=127.0788583"),
    "140": ("중구", "&z=13&btm=37.5046273&lft=126.8867068&top=37.6230096&rgt=127.1084932"),
    "170": ("용산구", "&z=13&btm=37.4795905&lft=126.8757428&top=37.5980125&rgt=127.0549572"),
    "200": ("성동구", "&z=13&btm=37.5042601&lft=126.9472308&top=37.6226429&rgt=127.1264452"),
    "215": ("광진구", "&z=13&btm=37.4793823&lft=126.9927678&top=37.5978047&rgt=127.1719822"),
    "230": ("동대문구", "&z=13&btm=37.5152868&lft=126.9501578&top=37.6336522&rgt=127.1293722"),
    "260": ("중랑구", "&z=13&btm=37.5471431&lft=127.0029768&top=37.6654578&rgt=127.1821912"),
    "290": ("성북구", "&z=13&btm=37.5282041&lft=126.9311218&top=37.6465489&rgt=127.1103362"),
    "305": ("강북구", "&z=13&btm=37.5805857&lft=126.9358808&top=37.6988473&rgt=127.1150952"),
    "320": ("도봉구", "&z=13&btm=37.6096368&lft=126.9575558&top=37.7278521&rgt=127.1367702"),
    "350": ("노원구", "&z=13&btm=37.5951433&lft=126.9668038&top=37.7133817&rgt=127.1460182"),
    "380": ("은평구", "&z=13&btm=37.5435963&lft=126.8395558&top=37.6619167&rgt=127.0187702"),
    "410": ("서대문구", "&z=13&btm=37.5200226&lft=126.8471928&top=37.6383804&rgt=127.0264072"),
    "440": ("마포구", "&z=13&btm=37.5043021&lft=126.8187928&top=37.6226849&rgt=126.9980072"),
    "470": ("양천구", "&z=13&btm=37.4577552&lft=126.7769388&top=37.5762118&rgt=126.9561532"),
    "500": ("강서구", "&z=13&btm=37.4917601&lft=126.7599268&top=37.6101628&rgt=126.9391412"),
    "530": ("구로구", "&z=13&btm=37.4362411&lft=126.7979248&top=37.5547319&rgt=126.9771392"),
    "545": ("금천구", "&z=13&btm=37.3926566&lft=126.8124678&top=37.5112164&rgt=126.9916822"),
    "560": ("영등포구", "&z=13&btm=37.4671226&lft=126.8066058&top=37.5855644&rgt=126.9858202"),
    "590": ("동작구", "&z=13&btm=37.4531945&lft=126.8498928&top=37.5716584&rgt=127.0291072"),
    "620": ("관악구", "&z=13&btm=37.4217406&lft=126.8619938&top=37.5402544&rgt=127.0412082"),
    "650": ("서초구", "&z=13&btm=37.4242856&lft=126.9429868&top=37.5427954&rgt=127.1222012"),
    "680": ("강남구", "&z=13&btm=37.4581565&lft=126.9577058&top=37.5766125&rgt=127.1369202"),
    "710": ("송파구", "&z=13&btm=37.4553382&lft=127.0162558&top=37.5737987&rgt=127.1954702"),
    "740": ("강동구", "&z=13&btm=37.4708846&lft=127.0341638&top=37.5893204&rgt=127.2133782"),
}

SEOUL_DISTRICTS: dict[str, District] = {}
for _code, (_name, _coords) in _SEOUL_DATA.items():
    SEOUL_DISTRICTS[_code] = _build_district(_code, _name, _coords)

# Name-based lookup (Korean name → District)
DISTRICT_BY_NAME: dict[str, District] = {}
for d in SEOUL_DISTRICTS.values():
    DISTRICT_BY_NAME[d.name] = d
    # Also allow without 구 suffix
    if d.name.endswith("구"):
        DISTRICT_BY_NAME[d.name[:-1]] = d


# Trade type mappings
TRADE_TYPES = {
    "매매": "A1",
    "전세": "B1",
    "월세": "B2",
    "단기임대": "B3",
}

TRADE_TYPE_NAMES = {v: k for k, v in TRADE_TYPES.items()}

# Property type mappings
PROPERTY_TYPES = {
    "APT": "아파트",
    "VL": "빌라/연립",
    "OPST": "오피스텔",
    "OR": "주거용오피스텔",
    "ABYG": "아파트분양권",
    "JGC": "재건축",
    "DDDGG": "단독/다가구",
}

# Sort options
SORT_OPTIONS = {
    "rank": "추천순",
    "prc": "가격순",
    "spc": "면적순",
    "date": "최신순",
}


def find_district(name: str) -> District | None:
    """Find a district by name (supports partial match)."""
    name = name.strip()
    if name in DISTRICT_BY_NAME:
        return DISTRICT_BY_NAME[name]
    # Partial match
    for dname, district in DISTRICT_BY_NAME.items():
        if name in dname:
            return district
    return None


def list_districts() -> list[District]:
    """Return all districts sorted by name."""
    return sorted(SEOUL_DISTRICTS.values(), key=lambda d: d.code)
