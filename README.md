# Basics of Docker 

# Build Docker Image By Running the Following Command

$docker build -t jenkinsdemo . # -t = Tag 


# To Run Containers

$docker run -it -p 2222:8080 jenkinsdemo # -i = interactive ; -t terminal

# In host's browser type 

localhost:2222 for Jenkins Setup

# Some of the Docker Commands

docker images --> to list the images

docker ps  --> to see the running containers

docker ps -a --> to see all the containers which are exited 

docker run -it <image_tag> --> to run the image which will create containers 

docker run -it <image_tag> bash --> to run the image in bash

docker exec -it <container_tag> bash --> this is to log into the running container in bash (edited)

docker run -it -p 8080:8080 <image_tag> --> this is to run the image using the port 8080 in host(ubuntu) and 8080 in container 

DOCKER CHEATSHEET - https://github.com/wsargent/docker-cheat-sheet#dockerfile



import os
import re
import sys

COLOR_MAP = {
    "123456789012": "#F5F5F5",
    "123456789999": "#EBEBEB",
    "DATABASE": "#F9F9F9",
    "EXTERNAL/API": "#F2F2F2"
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


def extract_bogiefile_resources():
    import yaml
    resources = []
    for name in ["bogiefile", "bogiefile.yaml"]:
        if not os.path.isfile(name):
            continue
        try:
            with open(name, 'r') as f:
                data = yaml.safe_load(f)
            if not data or 'environments' not in data:
                continue
            for env in data['environments']:
                gear_raw = env.get('gear', '')
                gear_name = gear_raw.split(':')[0].strip()
                resource_type = GEAR_TO_RESOURCE.get(gear_name, gear_name)
                env_name = env.get('name', 'unknown')
                regions = [r.get('name', '') for r in env.get('regions', [])]                resources.append({
                    "environment": env_name,
                    "gear": gear_raw,
                    "resource_type": resource_type,
                    "regions": ', '.join(regions) if regions else 'N/A'
                })
        except Exception:
            pass
    return resources


def extract_resources(file_path):
    found = []
    if file_path.endswith(os.path.basename(__file__)) or file_path.endswith("aws_api_report.html"):
        return []
    arn_pattern = r"arn:aws:([a-zA-Z0-9-]+):([a-z0-9-]+):(\d{12})?:([\w\-\/:]+)"
    url_pattern = r"https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s\"']*)?"
    db_host_pattern = r'"host"\s*:\s*"([^"]+)"'
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            for m in re.finditer(arn_pattern, content):
                acc = str(m.group(3)) if m.group(3) else "N/A"
                found.append({"account": acc, "file": os.path.relpath(file_path), "service": m.group(1).upper(), "identifier": m.group(0), "type": 1, "color": COLOR_MAP.get(acc, "#FFFFFF")})
            for m in re.finditer(db_host_pattern, content, re.IGNORECASE):
                val = m.group(1)
                if val.lower() in ["localhost", "127.0.0.1", "..."]:
                    continue
                found.append({"account": "DATABASE", "file": os.path.relpath(file_path), "service": "DB_HOST", "identifier": val, "type": 2, "color": COLOR_MAP.get("DATABASE", "#FFFFFF")})
            for m in re.finditer(url_pattern, content):
                url = m.group(0)
                if any(domain.lower() in url.lower() for domain in IGNORE_DOMAINS):
                    continue
                found.append({"account": "EXTERNAL/API", "file": os.path.relpath(file_path), "service": "HTTPS/API", "identifier": url, "type": 3, "color": COLOR_MAP.get("EXTERNAL/API", "#FFFFFF")})
    except Exception:
        pass
    return found

def generate_report(data, bogie_resources=None):
    data.sort(key=lambda x: (x['type'], x['account'], x['service'], x['file']))
    grouped = {}
    for r in data:
        grouped.setdefault(r['account'], []).append(r)
    html = '<html><head><style>'
    html += 'body{font-family:sans-serif;margin:20px}'
    html += 'table{width:100%;border-collapse:collapse;margin-top:10px;margin-bottom:30px}'
    css = """
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;margin:20px;color:#333}
    table{width:100%;border-collapse:collapse;margin-top:10px;margin-bottom:30px}
    th,td{border:1px solid #ddd;padding:8px;text-align:left;font-size:12px}
    th{background:#f5f5f5;font-weight:600}
    button{cursor:pointer;padding:5px 10px;background:#555;color:white;border:none;border-radius:4px;margin-right:5px}
    button:hover{background:#333}
    .account-header{padding:10px 15px;margin-top:20px;border-radius:4px;font-size:15px;font-weight:600;cursor:pointer;display:flex;justify-content:space-between;align-items:center;border:1px solid #ddd}
    .account-header:hover{background:#e8e8e8}
    .badge{background:rgba(0,0,0,0.08);padding:2px 10px;border-radius:12px;font-size:13px}
    .summary{display:flex;gap:20px;margin-bottom:20px;flex-wrap:wrap}
    .summary-card{background:#fafafa;border:1px solid #ddd;border-radius:6px;padding:15px 20px;min-width:150px;text-align:center}
    .summary-card .num{font-size:28px;font-weight:bold;color:#333}
    .summary-card .label{font-size:12px;color:#888;margin-top:4px}
    .bogie-section{background:#fafafa;border:1px solid #ccc;border-radius:6px;padding:15px 20px;margin-bottom:25px}
    .bogie-section h3{color:#333;margin-bottom:10px;font-size:15px}
    .bogie-section table{margin-bottom:0}
    .bogie-section th{background:#eee}
    """bogie_resources:
        html += '<div class="bogie-section">'
        html += '<h3>Resources Created by This Repo (from bogiefile)</h3>'
        html += '<table><thead><tr><th>Environment</th><th>Gear</th><th>Resource Type</th><th>Region(s)</th></tr></thead><tbody>'
        for br in bogie_resources:
            html += '<tr>'
            html += '<td>' + br["environment"] + '</td>'
            html += '<td>' + br["gear"] + '</td>'
            html += '<td>' + br["resource_type"] + '</td>'
            html += '<td>' + br["regions"] + '</td>'
            html += '</tr>'
        html += '</tbody></table></div>'

    # Summary cards
    total = len(data)
    account_count = len(grouped)
    service_types = len(set(r['service'] for r in data)) if data else 0
    files_scanned = len(set(r['file'] for r in data)) if data else 0
    html += '<div class="summary">'
    html += '<div class="summary-card"><div class="num">' + str(total) + '</div><div class="label">Total Resources</div></div>'
    html += '<div class="summary-card"><div class="num">' + str(account_count) + '</div><div class="label">Accounts</div></div>'
    html += '<div class="summary-card"><div class="num">' + str(service_types) + '</div><div class="label">Service Types</div></div>'
    html += '<div class="summary-card"><div class="num">' + str(files_scanned) + '</div><div class="label">Files with Resources</div></div>'
    html += '</div>'
    html += '<div class="controls">'
    html += '<button onclick="downloadCSV()">Download CSV</button> '
    html += '<button onclick="toggleAll(true)">Expand All</button> '
    html += '<button onclick="toggleAll(false)">Collapse All</button>'
    html += '</div>'
    # Grouped tables by account
    for idx, (account, resources) in enumerate(grouped.items()):
        color = resources[0]['color']
        html += '<div class="account-section">'
        html += '<div class="account-header" style="background-color:' + color + ';" onclick="toggle(\'grp' + str(idx) + '\')">'
        html += '<span>Account: ' + account + '</span>'
        html += '<span class="badge">' + str(len(resources)) + ' resources</span>'
        html += '</div>'
        html += '<div id="grp' + str(idx) + '">'
        html += '<table><thead><tr><th>File</th><th>Service</th><th>Identifier</th><th>Dependency</th></tr></thead><tbody>'
        for r in resources:
            html += '<tr style="background-color:' + r["color"] + ';">'
            html += '<td>' + r["file"] + '</td>'
            html += '<td>' + r["service"] + '</td>'
            html += '<td>' + r["identifier"] + '</td>'
            html += '<td><select><option value="Dev Team">Dev Team</option><option value="Infra">Infra</option><option value="Ignore">Ignore</option></select></td>'
            html += '</tr>'
        html += '</tbody></table></div></div>'
    html += '<script>'
    html += 'function toggle(id){var el=document.getElementById(id);el.style.display=el.style.display==="none"?"block":"none";}'
    html += 'function toggleAll(show){document.querySelectorAll(".account-section > div:nth-child(2)").forEach(function(el){el.style.display=show?"block":"none";});}'
    html += 'function downloadCSV(){'
    html += 'var csvRows=[\'\"Account\",\"File\",\"Service\",\"Identifier\",\"Dependency\"\']; '
    html += 'document.querySelectorAll(".account-section").forEach(function(section){'
    html += 'var account=section.querySelector(".account-header span").innerText.replace("Account: ","");'
    html += 'section.querySelectorAll("tbody tr").forEach(function(row){'
    html += 'var cols=row.querySelectorAll("td");'
    html += 'var f=cols[0].innerText.replace(/"/g,\'""\'');'
    html += 'var s=cols[1].innerText.replace(/"/g,\'""\'');'
    html += 'var id=cols[2].innerText.replace(/"/g,\'""\'');'
    html += 'var dep=cols[3].querySelector("select").value;'
    html += 'csvRows.push(\'"\'+account+\'","\'+f+\'","\'+s+\'","\'+id+\'","\'+dep+\'"\');'
    html += '});});'
    html += 'var blob=new Blob([csvRows.join("\\n")],{type:"text/csv;charset=utf-8;"});'
    html += 'var url=URL.createObjectURL(blob);var link=document.createElement("a");'
    html += 'link.setAttribute("href",url);link.setAttribute("download","resource_inventory.csv");'
    html += 'link.style.visibility="hidden";document.body.appendChild(link);link.click();document.body.removeChild(link);'
    html += '}'
    html += '</script></body></html>'

    with open("aws_api_report.html", "w") as f:
        f.write(html)


if __name__ == "__main__":
    results = []
    print("Scanning...")
    bogie_resources = extract_bogiefile_resources()
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', 'venv'}]
        for f in files:
            if not f.lower().endswith(('.png', '.jpg', '.exe', '.zip')):
                results.extend(extract_resources(os.path.join(root, f)))
    if results or bogie_resources:
        generate_report(results, bogie_resources)
        print("Done. Open aws_api_report.html")











