# Creating Grist service-account tokens with Pygrister/Gry

## Answer

**Yes.** Pygrister can create a Grist service account and its credential. Grist calls that credential an **API key**, not an OAuth access token or JWT. The Python method is:

```python
GristApi.add_service_account(
    expire: str,
    label: str = "",
    description: str = "",
) -> Apiresp
```

On success, Pygrister returns `(http_status, (service_account_id, api_key))`. Its implementation sends `POST /api/service-accounts` with `expiresAt` and any non-empty label and description, then reduces Grist's response to `(id, key)` ([pinned Pygrister implementation](https://github.com/ricpol/pygrister/blob/8990dc5ffd462cb4d577cd1c7d905e33f7505e32/src/pygrister/api.py#L125-L153)). `Apiresp` is an alias for `tuple[int, Any]` ([pinned response type](https://github.com/ricpol/pygrister/blob/8990dc5ffd462cb4d577cd1c7d905e33f7505e32/src/pygrister/apicaller.py#L24-L25)).

## Runnable Python

Install the package and authenticate as the **regular Grist user that will own the service account**:

```bash
python -m pip install pygrister
export GRIST_API_KEY='the-owner-users-api-key'
export GRIST_TEAM_SITE='docs'  # or the team-site subdomain
```

Then create the account and capture its key:

```python
from pygrister.api import GristApi

client = GristApi()
status, created = client.add_service_account(
    expire="2042-10-10",
    label="data-import",
    description="Imports conference data",
)
assert status == 200
service_account_id, service_api_key = created
print(service_account_id)
# Store service_api_key in a secret manager; do not print it in real code.
```

The identical call works in Gry's preconfigured Python shell (the shell binds a `GristApi` instance to `gry`):

```text
$ gry python
>>> status, (service_account_id, service_api_key) = gry.add_service_account(
...     "2042-10-10", "data-import", "Imports conference data"
... )
```

That binding is created by Gry's [Python startup module](https://github.com/ricpol/pygrister/blob/8990dc5ffd462cb4d577cd1c7d905e33f7505e32/src/pygrister/_pygrystart.py#L5-L22).

The official request schema requires `expiresAt`; `label` and `description` are optional. Grist's full response also contains `login`, account metadata, `hasValidKey`, and `key`, but Pygrister intentionally returns only the ID and key ([official create endpoint](https://support.getgrist.com/api/#tag/service-accounts/operation/createServiceAccount)).

A service-account key is subsequently used like any other Grist API key:

```python
service_client = GristApi(config={"GRIST_API_KEY": service_api_key})
status, orgs = service_client.list_team_sites()
```

Pygrister puts the configured key in `Authorization: Bearer <key>` on every request ([pinned request code](https://github.com/ricpol/pygrister/blob/8990dc5ffd462cb4d577cd1c7d905e33f7505e32/src/pygrister/apicaller.py#L74-L105)); Grist documents the same bearer scheme ([official authentication reference](https://support.getgrist.com/api/#section/Authentication/ApiKey)). The generated account starts as a distinct Grist identity: use the `login` exposed by list/detail calls when assigning that identity the specific rights its workflow needs.

## Authentication and availability prerequisites

- The creating client itself needs a valid **user API key** in `GRIST_API_KEY`. Pygrister loads it from its configuration file or environment, with environment variables taking precedence, and recommends the environment for this secret ([Pygrister configuration docs](https://pygrister.readthedocs.io/en/latest/conf.html#where-configuration-is-stored), [pinned configuration source](https://github.com/ricpol/pygrister/blob/8990dc5ffd462cb4d577cd1c7d905e33f7505e32/src/pygrister/config.py#L22-L57)).
- The authenticated caller must be a regular login user. Grist creates the service account under that owner, and management operations check that same ownership ([pinned Grist manager source](https://github.com/gristlabs/grist-core/blob/dca55bbf31955069233459c3146aa45952bf3b47/app/gen-server/lib/homedb/ServiceAccountsManager.ts#L35-L65), [pinned ownership checks](https://github.com/gristlabs/grist-core/blob/dca55bbf31955069233459c3146aa45952bf3b47/app/gen-server/lib/homedb/ServiceAccountsManager.ts#L250-L266)). The public API documents HTTP 403 when the caller is not allowed to create or manage an account.
- On self-managed Grist, these routes exist only when `GRIST_ENABLE_SERVICE_ACCOUNTS` is affirmative ([pinned Grist routes](https://github.com/gristlabs/grist-core/blob/dca55bbf31955069233459c3146aa45952bf3b47/app/gen-server/ApiServer.ts#L696-L722)). Configure Pygrister's `GRIST_SELF_MANAGED*` settings as described in its [self-hosting documentation](https://pygrister.readthedocs.io/en/latest/conf_advanced.html#self-hosted-support).
- `add_service_account` is a write operation and is blocked when Pygrister's `GRIST_SAFEMODE` is `Y` ([pinned decorator and method](https://github.com/ricpol/pygrister/blob/8990dc5ffd462cb4d577cd1c7d905e33f7505e32/src/pygrister/api.py#L46-L60)). By default Pygrister also raises `requests.HTTPError` for HTTP status codes of 300 or greater rather than merely returning the error tuple ([pinned caller behavior](https://github.com/ricpol/pygrister/blob/8990dc5ffd462cb4d577cd1c7d905e33f7505e32/src/pygrister/apicaller.py#L74-L125)).

## Key handling, rotation, and revocation

Treat `service_api_key` as a password: capture it from creation, store it outside source control (preferably in a secret manager or environment variable), and avoid logging it. List and detail responses expose `hasValidKey` but do **not** return the key, so there is no API method for retrieving the original key later ([official list and detail endpoints](https://support.getgrist.com/api/#tag/service-accounts)). Pygrister masks a configured `GRIST_API_KEY` in configuration/debug output, but that does not protect a newly returned key that application code prints or logs ([pinned masking code](https://github.com/ricpol/pygrister/blob/8990dc5ffd462cb4d577cd1c7d905e33f7505e32/src/pygrister/config.py#L35-L40)).

The same Python client supports inventory, rotation, and revocation:

```python
# Inventory: records contain id, login, label, description, expiresAt,
# and hasValidKey, but not the secret key.
status, accounts = client.list_service_accounts()
status, account = client.see_service_account(service_account_id)

# Rotate: replaces the credential and returns the new key string.
status, replacement_key = client.update_service_account_key(service_account_id)

# Revoke only the credential; the account remains and cannot authenticate
# until a new key is generated.
status, result = client.delete_service_account_key(service_account_id)
assert result is None

# Or remove the service account entirely.
status, result = client.delete_service_account(service_account_id)
assert result is None
```

The exact management signatures and successful return transformations are in Pygrister's [service-account methods](https://github.com/ricpol/pygrister/blob/8990dc5ffd462cb4d577cd1c7d905e33f7505e32/src/pygrister/api.py#L125-L193). Grist explicitly recommends regeneration when a key leaks, and says deleting the key prevents authentication until another is generated ([official regeneration endpoint](https://support.getgrist.com/api/#tag/service-accounts/operation/regenerateServiceAccountApiKey), [official key-deletion endpoint](https://support.getgrist.com/api/#tag/service-accounts/operation/deleteServiceAccountApiKey)). These are API-key operations; Pygrister/Gry has no separate service-account OAuth-token issuance or revocation flow.

For completeness, the CLI exposes the same operations as `gry sacc new`, `list`, `see`, `new-key`, `delete-key`, and `delete` ([pinned Gry commands](https://github.com/ricpol/pygrister/blob/8990dc5ffd462cb4d577cd1c7d905e33f7505e32/src/pygrister/cli.py#L548-L630)).
