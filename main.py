import argparse
import json
import os

import requests
from dotenv import load_dotenv


BASE_URL = "https://deep.ec.europa.eu/external/api"
ENDPOINTS = {
    "saving": "/factsheet/saving/",
    "payback": "/factsheet/payback/",
    "avoidance": "/factsheet/avoidance/",
    "kpis": "/kpis",
}


def load_api_key() -> str | None:
    load_dotenv()
    return os.getenv("API_KEY") or os.getenv("api_key")


def fetch_data(endpoint: str, api_key: str, params: dict[str, str] | None = None):
    request_params = dict(params or {})
    request_params["apikey"] = api_key

    response = requests.get(f"{BASE_URL}{ENDPOINTS[endpoint]}", params=request_params, timeout=30)
    response.raise_for_status()
    return response.json()


BUILDING_MEASURE_TYPES = [
    "Building Fabric Measures",
    "Combination of Building Fabric and HVAC",
    "Integrated Renovation",
    "Lighting",
    "HVAC Plant",
    "Ventilation and air conditioning",
    "Other",
]

INDUSTRY_MEASURE_TYPES = [
    "Compressed Air",
    "Cooling",
    "Heating",
    "ICT",
    "Metering, Monitoring and Energy Management",
    "Motors",
    "Power Systems",
    "Pumps",
    "Refrigeration",
    "Street Lighting",
    "Waste heat (without power generation)",
    "Waste heat (with power generation)",
    "Other",
]

BUILDING_TYPES = [
    "DETACHED", "SINGLE", "MULTI4", "MULTI5",
    "PRIVATE", "PUBLIC", "WHOLESALE", "HOTEL",
    "HEALTH", "EDUCATION", "SPORT", "INDUSTRY",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch data from the DEEP API")
    parser.add_argument("endpoint", choices=ENDPOINTS.keys(), nargs="?", default="avoidance")
    parser.add_argument("--projecttype", choices=["Building", "Industry"])
    parser.add_argument(
        "--country",
        metavar="ISO_CODE",
        help="ISO country code (e.g. DE, EL) or 'EU' for all EU countries",
    )
    parser.add_argument(
        "--measuretype",
        metavar="MEASURE",
        help=(
            f"Building: {', '.join(BUILDING_MEASURE_TYPES)}. "
            f"Industry: {', '.join(INDUSTRY_MEASURE_TYPES)}"
        ),
    )
    parser.add_argument(
        "--companysize",
        choices=["MICRO", "SMALL", "MEDIUM", "LARGE"],
        help="Company size (industry projects only)",
    )
    parser.add_argument(
        "--buildingtype",
        choices=BUILDING_TYPES,
        help="Building type (building projects only)",
    )
    parser.add_argument("--verification", choices=["Verified", "Non-verified", "Unknown"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    api_key = load_api_key()

    if not api_key:
        raise SystemExit("Missing API key. Set API_KEY (or api_key) in your environment or .env file.")

    params = {
        key: value
        for key, value in {
            "projecttype": args.projecttype,
            "country": args.country,
            "measuretype": args.measuretype,
            "companysize": args.companysize,
            "buildingtype": args.buildingtype,
            "verification": args.verification,
        }.items()
        if value is not None
    }

    try:
        data = fetch_data(args.endpoint, api_key, params)
    except requests.HTTPError as exc:
        response = exc.response
        raise SystemExit(f"Request failed with status {response.status_code}: {response.text}") from exc
    except requests.RequestException as exc:
        raise SystemExit(f"An error occurred while calling the API: {exc}") from exc

    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()