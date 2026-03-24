import os
import re
import sys

COLOR_MAP = {
    "123456789012": "#F5F5F5",
    "123456789999": "#EBEBEB",
    "DATABASE": "#F9F9F9",
    "EXTERNAL/API": "#F2F2F2",
}

IGNORE_DOMAINS = ["github.com"]

GEAR_TO_RESOURCE = {
    "avenue": "IAM Role",
    "aws-lambda": "Lambda Function",
    "cloudwatch-rule": "CloudWatch Rule",
    "s3": "S3 Bucket",
    "dynamodb": "DynamoDB Table",
    "sqs": "SQS Queue",
    "sns": "SNS Topic",
    "api-gateway": "API Gateway",
    "ecs": "ECS Service",
    "ecr": "ECR Repository",
    "rds": "RDS Instance",
    "kinesis": "Kinesis Stream",
    "stepfunctions": "Step Function",
    "secretsmanager": "Secrets Manager Secret",
}


def _find_key_recursive(obj, key):
    """Recursively search a dict/list for a key and return its value."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            result = _find_key_recursive(v, key)
            if result is not None:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = _find_key_recursive(item, key)
            if result is not None:
                return result
    return None


def extract_bogiefile_resources():
    import yaml
    resources = []
    for name in ["bogiefile", "bogiefile.yaml"]:
        if not os.path.isfile(name):
            continue
        try:
            with open(name, "r") as f:
                data = yaml.safe_load(f)
            if not data or "environments" not in data:
                continue

            # Collect all aws_account_name values from pipeline.tasks
            pipeline_tasks = data.get("pipeline", {}).get("tasks", {})

            for env in data["environments"]:
                gear_raw = env.get("gear", "")
                gear_name = gear_raw.split(":")[0].strip()
                resource_type = GEAR_TO_RESOURCE.get(gear_name, gear_name)
                env_name = env.get("name", "unknown")
                regions = [r.get("name", "") for r in env.get("regions", [])]

                # 1. Check pipeline.tasks for aws_account_name (by env name or any nested key)
                aws_account = None
                for task_name, task_val in pipeline_tasks.items():
                    if not isinstance(task_val, dict):
                        continue
                    # Check if this env has a specific entry under the task
                    env_task = task_val.get(env_name)
                    if isinstance(env_task, dict):
                        found = _find_key_recursive(env_task, "aws_account_name")
                        if found:
                            aws_account = found
                            break
                    # Check top-level of the task section
                    if "aws_account_name" in task_val:
                        aws_account = task_val["aws_account_name"]
                        break

                # 2. If not found in tasks, search the entire pipeline section
                if not aws_account:
                    found = _find_key_recursive(pipeline_tasks, "aws_account_name")
                    if found:
                        aws_account = found

                # 3. Fall back to environments.inputs
                if not aws_account:
                    inputs = env.get("inputs", {})
                    aws_account = inputs.get("aws_account_name", None)

                # 4. Last resort: search entire environment entry
                if not aws_account:
                    aws_account = _find_key_recursive(env, "aws_account_name")

                resources.append({
                    "environment": env_name,
                    "gear": gear_raw,
                    "resource_type": resource_type,
                    "regions": ", ".join(regions) if regions else "N/A",
                    "aws_account_name": aws_account or "N/A",
                })
        except Exception:
            pass
    return resources


def extract_resources(file_path):
    found = []
    if file_path.endswith(os.path.basename(__file__)):
        return []
    if file_path.endswith("aws_api_report.html"):
        return []

    arn_pattern = r"arn:aws:([a-zA-Z0-9-]+):([a-z0-9-]+):(\d{12})?:([\w\-\/:]+)"
    url_pattern = r"https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s\"']*)?"
    db_host_pattern = r'"host"\s*:\s*"([^"]+)"'

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        for m in re.finditer(arn_pattern, content):
            acc = str(m.group(3)) if m.group(3) else "N/A"
            found.append({
                "account": acc,
                "file": os.path.relpath(file_path),
                "service": m.group(1).upper(),
                "identifier": m.group(0),
                "type": 1,
                "color": COLOR_MAP.get(acc, "#FFFFFF"),
            })

        for m in re.finditer(db_host_pattern, content, re.IGNORECASE):
            val = m.group(1)
            if val.lower() in ["localhost", "127.0.0.1", "..."]:
                continue
            found.append({
                "account": "DATABASE",
                "file": os.path.relpath(file_path),
                "service": "DB_HOST",
                "identifier": val,
                "type": 2,
                "color": COLOR_MAP.get("DATABASE", "#FFFFFF"),
            })

        for m in re.finditer(url_pattern, content):
            url = m.group(0)
            if any(d.lower() in url.lower() for d in IGNORE_DOMAINS):
                continue
            found.append({
                "account": "EXTERNAL/API",
                "file": os.path.relpath(file_path),
                "service": "HTTPS/API",
                "identifier": url,
                "type": 3,
                "color": COLOR_MAP.get("EXTERNAL/API", "#FFFFFF"),
            })
    except Exception:
        pass
    return found


CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; color: #333; }
table { width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 30px; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 12px; }
th { background: #f5f5f5; font-weight: 600; }
button { cursor: pointer; padding: 5px 10px; background: #555; color: white; border: none; border-radius: 4px; margin-right: 5px; }
button:hover { background: #333; }
.account-header { padding: 10px 15px; margin-top: 20px; border-radius: 4px; font-size: 15px; font-weight: 600; cursor: pointer; display: flex; justify-content: space-between; align-items: center; border: 1px solid #ddd; }
.account-header:hover { background: #e8e8e8; }
.badge { background: rgba(0,0,0,0.08); padding: 2px 10px; border-radius: 12px; font-size: 13px; }
.summary { display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap; }
.summary-card { background: #fafafa; border: 1px solid #ddd; border-radius: 6px; padding: 15px 20px; min-width: 150px; text-align: center; }
.summary-card .num { font-size: 28px; font-weight: bold; color: #333; }
.summary-card .label { font-size: 12px; color: #888; margin-top: 4px; }
.bogie-section { background: #fafafa; border: 1px solid #ccc; border-radius: 6px; padding: 15px 20px; margin-bottom: 25px; }
.bogie-section h3 { color: #333; margin-bottom: 10px; font-size: 15px; }
.bogie-section table { margin-bottom: 0; }
.bogie-section th { background: #eee; }
"""

JS = """
<script>
function toggle(id) {
    var el = document.getElementById(id);
    el.style.display = el.style.display === "none" ? "block" : "none";
}
function toggleAll(show) {
    var els = document.querySelectorAll(".account-section > div:nth-child(2)");
    for (var i = 0; i < els.length; i++) {
        els[i].style.display = show ? "block" : "none";
    }
}
function downloadCSV() {
    var csvRows = ['"Account","File","Service","Identifier","Dependency"'];
    var sections = document.querySelectorAll(".account-section");
    for (var i = 0; i < sections.length; i++) {
        var account = sections[i].querySelector(".account-header span").innerText.replace("Account: ", "");
        var rows = sections[i].querySelectorAll("tbody tr");
        for (var j = 0; j < rows.length; j++) {
            var cols = rows[j].querySelectorAll("td");
            var f = cols[0].innerText;
            var s = cols[1].innerText;
            var id = cols[2].innerText;
            var dep = cols[3].querySelector("select").value;
            csvRows.push('"' + account + '","' + f + '","' + s + '","' + id + '","' + dep + '"');
        }
    }
    var blob = new Blob([csvRows.join("\\n")], {type: "text/csv;charset=utf-8;"});
    var url = URL.createObjectURL(blob);
    var link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "resource_inventory.csv");
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
</script>
"""


def generate_report(data, bogie_resources=None):
    data.sort(key=lambda x: (x["type"], x["account"], x["service"], x["file"]))
    grouped = {}
    for r in data:
        grouped.setdefault(r["account"], []).append(r)

    lines = []
    lines.append("<html><head><style>" + CSS + "</style></head><body>")
    lines.append("<h2>Resource Inventory</h2>")

    # Bogiefile section at the top
    if bogie_resources:
        lines.append('<div class="bogie-section">')
        lines.append("<h3>Resources Created by This Repo (from bogiefile)</h3>")
        lines.append("<table><thead><tr>")
        lines.append("<th>Environment</th><th>Gear</th><th>Resource Type</th><th>Region(s)</th><th>AWS Account</th>")
        lines.append("</tr></thead><tbody>")
        for br in bogie_resources:
            lines.append("<tr>")
            lines.append("<td>%s</td>" % br["environment"])
            lines.append("<td>%s</td>" % br["gear"])
            lines.append("<td>%s</td>" % br["resource_type"])
            lines.append("<td>%s</td>" % br["regions"])
            lines.append("<td>%s</td>" % br["aws_account_name"])
            lines.append("</tr>")
        lines.append("</tbody></table></div>")

    # Summary cards
    total = len(data)
    acct_count = len(grouped)
    svc_count = len(set(r["service"] for r in data)) if data else 0
    file_count = len(set(r["file"] for r in data)) if data else 0
    lines.append('<div class="summary">')
    lines.append('<div class="summary-card"><div class="num">%d</div><div class="label">Total Resources</div></div>' % total)
    lines.append('<div class="summary-card"><div class="num">%d</div><div class="label">Accounts</div></div>' % acct_count)
    lines.append('<div class="summary-card"><div class="num">%d</div><div class="label">Service Types</div></div>' % svc_count)
    lines.append('<div class="summary-card"><div class="num">%d</div><div class="label">Files with Resources</div></div>' % file_count)
    lines.append("</div>")

    # Controls
    lines.append('<div class="controls">')
    lines.append('<button onclick="downloadCSV()">Download CSV</button>')
    lines.append('<button onclick="toggleAll(true)">Expand All</button>')
    lines.append('<button onclick="toggleAll(false)">Collapse All</button>')
    lines.append("</div>")

    # Grouped tables by account
    for idx, (account, resources) in enumerate(grouped.items()):
        color = resources[0]["color"]
        lines.append('<div class="account-section">')
        lines.append('<div class="account-header" style="background-color:%s;" onclick="toggle(\'grp%d\')">' % (color, idx))
        lines.append("<span>Account: %s</span>" % account)
        lines.append('<span class="badge">%d resources</span>' % len(resources))
        lines.append("</div>")
        lines.append('<div id="grp%d">' % idx)
        lines.append("<table><thead><tr>")
        lines.append("<th>File</th><th>Service</th><th>Identifier</th><th>Dependency</th>")
        lines.append("</tr></thead><tbody>")
        for r in resources:
            lines.append('<tr style="background-color:%s;">' % r["color"])
            lines.append("<td>%s</td>" % r["file"])
            lines.append("<td>%s</td>" % r["service"])
            lines.append("<td>%s</td>" % r["identifier"])
            dep_select = "<select>"
            dep_select += '<option value="Dev Team">Dev Team</option>'
            dep_select += '<option value="Infra">Infra</option>'
            dep_select += '<option value="Ignore">Ignore</option>'
            dep_select += "</select>"
            lines.append("<td>%s</td>" % dep_select)
            lines.append("</tr>")
        lines.append("</tbody></table></div></div>")

    lines.append(JS)
    lines.append("</body></html>")

    with open("aws_api_report.html", "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    results = []
    print("Scanning...")
    bogie_resources = extract_bogiefile_resources()
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "venv"}]
        for f in files:
            if not f.lower().endswith((".png", ".jpg", ".exe", ".zip")):
                results.extend(extract_resources(os.path.join(root, f)))
    if results or bogie_resources:
        generate_report(results, bogie_resources)
        print("Done. Open aws_api_report.html")
