# Postman collections: Singapore Mobile Proxy and cloudf.one

Ready-to-import [Postman](https://www.postman.com/) collections for three APIs:

| Collection | What it's for | Requests |
|---|---|---|
| [Singapore Mobile Proxy - Customer API](collections/singapore-mobile-proxy-customer-api.postman_collection.json) | Buy, renew, rotate and manage dedicated Singapore mobile proxies (Singtel or M1 SIMs) | 12 |
| [Singapore Mobile Proxy - Reseller API](collections/singapore-mobile-proxy-reseller-api.postman_collection.json) | Create and manage proxies for your own customers at reseller pricing | 15 |
| [cloudf.one - Cloud Phone API](collections/cloudfone-api.postman_collection.json) | List and lock the real Android phones on your cloudf.one account, plus partner ordering | 13 |

Every request has a description and saved example responses, including the error cases worth handling
(402 over credit, 409 out of stock, 429 cooldown).

## Use it

1. In Postman: **Import** and drop in a collection file plus its matching file from [`environments/`](environments/).
2. Select the environment and fill in the secret:
   - **Singapore Mobile Proxy:** `apiKey`. Customers make one in the
     [client dashboard](https://singaporemobileproxy.com/client?utm_source=github&utm_medium=repo);
     resellers use `/shop/api-keys`. Each key works on one API only.
   - **cloudf.one:** `accessToken`. Log in, open your phone once, then generate one under
     cloudf.one/#!/settings > Access tokens. `partnerKey` is only for partner accounts we've issued one to.
3. Start with the read-only requests (`List my proxies`, `My account`, `List my phones`).

Or from the command line with [newman](https://github.com/postmanlabs/newman):

```sh
newman run collections/cloudfone-api.postman_collection.json \
  -e environments/cloudfone.postman_environment.json \
  --env-var accessToken=YOUR_TOKEN --folder Devices
```

## Heads-up: some requests spend money

Folders are named so you can't miss it:

- **SMP Customer > Buy & renew (charges money):** purchases charge credit, then your saved card, with no confirmation step.
- **SMP Reseller > Create ports (bills daily):** each port bills its daily cost against your credit limit from creation.
- **cloudf.one > Partner orders:** orders spend prepaid credit. Reuse an `Idempotency-Key` only to retry the same order.

Running the whole collection with a real key will run these. Use `--folder` to pick what you run.

## What the APIs don't do

- **cloudf.one:** no adb over the internet (a WireGuard tunnel is available on request), no input injection or
  screenshots over REST, no APK install, no credit top-ups over the API. Details on
  [cloudf.one/developers](https://cloudf.one/developers?utm_source=github&utm_medium=repo).
- **Singapore Mobile Proxy:** proxies are Singtel or M1. The customer API picks the carrier for you; the reseller API
  takes `telco`.

## Docs

- Customer API: https://singaporemobileproxy.com/api-docs
- Reseller API: https://singaporemobileproxy.com/reseller-api-docs
- cloudf.one API: https://cloudf.one/developers (full STF spec: https://cloudf.one/api/v1/swagger.json)

New to them? Singapore Mobile Proxy has a
[free 24-hour trial](https://singaporemobileproxy.com/?utm_source=github&utm_medium=repo), then $4/day or $13/week.
cloudf.one phones start at $5/day on [cloudf.one](https://cloudf.one/?utm_source=github&utm_medium=repo).

## Contributing

The JSON is generated. Edit [`build.py`](build.py), run `python build.py`, and commit both. CI checks the files
match `build.py`, validates them against the Postman v2.1 schema, rejects committed credentials, and runs every
request with newman against a local mock (never the live APIs).

Found an endpoint that behaves differently from what's here? Open an issue.

## License

MIT
