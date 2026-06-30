## DEEP API fetcher

Set `API_KEY` in a `.env` file or your shell environment, then run:

```bash
uv run .\main.py avoidance --projecttype Industry
```

Available endpoints:

- `saving`
- `payback`
- `avoidance`
- `kpis`

Common filters supported by the script:

- `--projecttype Building|Industry`
- `--country <ISO code or EU>`
- `--measuretype <measure name>`
- `--companysize MICRO|SMALL|MEDIUM|LARGE`
- `--buildingtype <building code>`
- `--verification Verified|Non-verified|Unknown`
