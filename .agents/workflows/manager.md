---
description: Manage and interact with the local Antigravity Manager proxy service and account pool.
---

# Antigravity Manager Integration Command

Provides commands to view status, list accounts, switch accounts, and start/stop the manager's proxy daemon.

## Usage

* Check proxy status:
  `/manager status`

* List all configured accounts:
  `/manager list`

* Switch the active account:
  `/manager switch --account <email-or-id>`

* Start the proxy service:
  `/manager start`

* Stop the proxy service:
  `/manager stop`

## Arguments

$ARGUMENTS:
- `[action]` required action string: `status`, `list`, `switch`, `start`, `stop`
- `--account <email-or-id>` required for `switch` action

## Execution Instructions for the Agent

When this command is invoked, perform the corresponding actions below:

### 1. status
* Check if the process `antigravity_tools.exe` is running:
  `Get-Process -Name "antigravity_tools" -ErrorAction SilentlyContinue`
* Verify if port `8045` is listening and respond to health check.
* Retrieve the `api_key` from `%USERPROFILE%\.antigravity_tools\gui_config.json` (or `$HOME/.antigravity_tools/gui_config.json` on Linux/macOS).
* Query `http://127.0.0.1:8045/api/proxy/status` or `http://127.0.0.1:8045/api/health` with header `Authorization: Bearer <api_key>` (or `x-api-key: <api_key>`).
* Output a summary including:
  * Proxy daemon status (running/stopped)
  * Listen address & port
  * Active client API key
  * Cloudflared tunnel status (if configured)

### 2. list
* Send a GET request to `http://127.0.0.1:8045/api/accounts` using `x-api-key` auth.
* Format the returned accounts into a markdown table showing:
  * **Current Active**: Indicated with a star or checkmark
  * **Email**: Account email address
  * **Label/Name**: Custom label (if set)
  * **Fingerprint Status**: Yes/No
  * **Disabled**: Active/Disabled
  * **Last Used**: Relative timestamp

### 3. switch
* Find the matching account ID for the given `--account` parameter (email or account ID).
* Send a POST request to `http://127.0.0.1:8045/api/accounts/switch` with JSON payload `{"accountId": "<id>"}` and header `x-api-key`.
* Confirm database injection status and report process restart events.

### 4. start
* Check if `antigravity_tools.exe` is already running. If so, report status.
* If not running, start it in headless mode:
  `Start-Process -FilePath "$env:LOCALAPPDATA\Antigravity Tools\antigravity_tools.exe" -ArgumentList "--headless" -NoNewWindow`
* Wait 3 seconds and verify port `8045` responds.

### 5. stop
* Kill the `antigravity_tools.exe` process:
  `Stop-Process -Name "antigravity_tools" -Force`
* Verify the proxy server has stopped listening on port `8045`.
