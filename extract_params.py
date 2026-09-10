# extract_params.py - Intelligent Dynamic Parameter Extraction
import json
import re
import os
from datetime import datetime
from urllib.parse import urlparse, parse_qs

def load_har(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def identify_login_request(har_data):
    keywords = ['login', 'auth', 'token', 'signin', 'session', 'credential']
    
    for entry in har_data['log']['entries']:
        url = entry['request']['url'].lower()
        if any(keyword in url for keyword in keywords):
            return entry
    
    for entry in har_data['log']['entries']:
        if entry['request']['method'] == 'POST':
            post_data = entry['request'].get('postData', {}).get('text', '').lower()
            if 'password' in post_data or 'username' in post_data:
                return entry
    
    return None

def detect_dynamic_value(value):
    if not isinstance(value, str):
        return None
    
    if re.match(r'^\d{10,13}$', value):
        return "Timestamp"
    
    if re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', value, re.I):
        return "UUID"
    
    if re.match(r'^[a-f0-9]{32}$', value, re.I):
        return "MD5 Hash"
    if re.match(r'^[a-f0-9]{40}$', value, re.I):
        return "SHA1 Hash"
    if re.match(r'^[a-f0-9]{64}$', value, re.I):
        return "SHA256 Hash"
    
    if re.match(r'^[A-Za-z0-9+/=]{20,}$', value):
        return "Base64/Encoded"
    
    if value.count('.') == 2 and len(value) > 50:
        return "JWT Token"
    
    if re.match(r'^[a-zA-Z0-9]{16,}$', value) and not value.islower() and not value.isupper():
        return "Nonce/Random String"
    
    return None

def extract_parameters(entry):
    result = {
        'url': entry['request']['url'],
        'method': entry['request']['method'],
        'headers': {},
        'query_params': {},
        'body_params': {},
        'dynamic_params': []
    }
    
    for header in entry['request']['headers']:
        name = header['name']
        value = header['value']
        result['headers'][name] = value
        
        dyn_type = detect_dynamic_value(value)
        if dyn_type:
            result['dynamic_params'].append({
                'location': 'Header',
                'name': name,
                'value': value,
                'type': dyn_type
            })
    
    parsed = urlparse(entry['request']['url'])
    query_params = parse_qs(parsed.query)
    for key, values in query_params.items():
        value = values[0] if len(values) == 1 else values
        result['query_params'][key] = value
        
        dyn_type = detect_dynamic_value(str(value))
        if dyn_type:
            result['dynamic_params'].append({
                'location': 'Query',
                'name': key,
                'value': value,
                'type': dyn_type
            })
    
    post_data = entry['request'].get('postData', {})
    if post_data:
        if 'text' in post_data:
            try:
                body_json = json.loads(post_data['text'])
                result['body_params'] = body_json
                
                def find_dynamic(obj, path=""):
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            find_dynamic(v, f"{path}.{k}" if path else k)
                    elif isinstance(obj, list):
                        for i, v in enumerate(obj):
                            find_dynamic(v, f"{path}[{i}]")
                    else:
                        dyn_type = detect_dynamic_value(str(obj))
                        if dyn_type:
                            result['dynamic_params'].append({
                                'location': 'Body',
                                'name': path,
                                'value': obj,
                                'type': dyn_type
                            })
                
                find_dynamic(body_json)
            except json.JSONDecodeError:
                result['body_params'] = {'raw': post_data['text']}
    
    return result

def generate_markdown_report(params, output_file):
    md = []
    md.append("# 🔐 Login Flow - Dynamic Parameter Extraction Report\n")
    md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    md.append("---\n")
    
    md.append("## 📡 Request Overview\n")
    md.append(f"- **URL:** `{params['url']}`")
    md.append(f"- **Method:** `{params['method']}`\n")
    
    if params['dynamic_params']:
        md.append("## 🎯 Dynamic Parameters (Auto-Detected)\n")
        md.append("| Location | Name | Type | Value |")
        md.append("|----------|------|------|-------|")
        for dp in params['dynamic_params']:
            value_preview = str(dp['value'])[:50] + "..." if len(str(dp['value'])) > 50 else str(dp['value'])
            md.append(f"| {dp['location']} | `{dp['name']}` | **{dp['type']}** | `{value_preview}` |")
        md.append("")
    else:
        md.append("## ℹ️ No obvious dynamic parameters detected\n")
        md.append("_The request may use static parameters or the dynamic generation logic is not pattern-based._\n")
    
    md.append("## 📋 Full Headers\n")
    md.append("```")
    for name, value in params['headers'].items():
        md.append(f"{name}: {value}")
    md.append("```\n")
    
    if params['query_params']:
        md.append("## 🔗 Query Parameters (URL)\n")
        md.append("```json")
        md.append(json.dumps(params['query_params'], indent=2))
        md.append("```\n")
    
    if params['body_params']:
        md.append("## 📦 Request Body\n")
        md.append("```json")
        md.append(json.dumps(params['body_params'], indent=2))
        md.append("```\n")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    
    print(f"✅ Report generated: {output_file}")

def main():
    har_file = "traffic.har"
    
    if not os.path.exists(har_file):
        print(f"❌ {har_file} not found!")
        return
    
    print("🔍 Loading HAR file...")
    har_data = load_har(har_file)
    
    print("🔍 Identifying login request...")
    login_entry = identify_login_request(har_data)
    
    if not login_entry:
        print("❌ Could not find login request in traffic!")
        return
    
    print(f"✅ Found login request: {login_entry['request']['url']}")
    
    print("🔍 Extracting all parameters...")
    params = extract_parameters(login_entry)
    
    print("📝 Generating Markdown report...")
    generate_markdown_report(params, "login_params_report.md")
    
    with open("login_params.json", 'w', encoding='utf-8') as f:
        json.dump(params, f, indent=2, ensure_ascii=False)
    print("✅ JSON export: login_params.json")
    
    print("\n" + "="*60)
    print("📊 EXTRACTION SUMMARY")
    print("="*60)
    print(f"Total Headers: {len(params['headers'])}")
    print(f"Total Query Params: {len(params['query_params'])}")
    print(f"Total Body Params: {len(params['body_params']) if isinstance(params['body_params'], dict) else 1}")
    print(f"Dynamic Parameters Found: {len(params['dynamic_params'])}")
    
    if params['dynamic_params']:
        print("\n🎯 DYNAMIC PARAMETERS:")
        for dp in params['dynamic_params']:
            print(f"  - {dp['location']}: {dp['name']} ({dp['type']})")
    
    print("="*60)

if __name__ == "__main__":
    main()
