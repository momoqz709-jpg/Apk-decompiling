# analyze_crypto_logic.py - Intelligent Crypto Logic Extraction
import os
import re
import json
from pathlib import Path
from datetime import datetime

class CryptoLogicAnalyzer:
    def __init__(self, jadx_output_dir="jadx-output"):
        self.jadx_dir = jadx_output_dir
        self.findings = []
        
    def search_pattern(self, pattern, description, category="crypto"):
        print(f"🔍 Searching for {description}...")
        
        for root, dirs, files in os.walk(self.jadx_dir):
            for file in files:
                if file.endswith('.java'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                            for match in matches:
                                start = max(0, match.start() - 500)
                                end = min(len(content), match.end() + 500)
                                context = content[start:end]
                                
                                class_match = re.search(r'class\s+(\w+)', content[:match.start()])
                                method_match = re.search(r'(?:public|private|protected)?\s*(?:static\s+)?\w+\s+(\w+)\s*\([^)]*\)\s*\{[^}]*' + re.escape(match.group(0)), content[:match.end()])
                                
                                class_name = class_match.group(1) if class_match else "Unknown"
                                method_name = method_match.group(1) if method_match else "Unknown"
                                
                                self.findings.append({
                                    'category': category,
                                    'description': description,
                                    'file': file_path.replace(self.jadx_dir + '/', ''),
                                    'class': class_name,
                                    'method': method_name,
                                    'match': match.group(0),
                                    'context': context.strip()
                                })
                    except Exception as e:
                        continue
    
    def analyze_all(self):
        print("="*60)
        print("🔐 CRYPTO LOGIC ANALYSIS")
        print("="*60)
        
        self.search_pattern(
            r'System\.currentTimeMillis\(\)',
            "Timestamp Generation (System.currentTimeMillis)",
            "timestamp"
        )
        
        self.search_pattern(
            r'UUID\.randomUUID\(\)',
            "UUID Generation",
            "uuid"
        )
        
        self.search_pattern(
            r'SecureRandom',
            "SecureRandom (Cryptographic Nonce)",
            "nonce"
        )
        
        self.search_pattern(
            r'MessageDigest\.getInstance\(["\']([^"\']+)["\']\)',
            "Hash Algorithm (MessageDigest)",
            "hash"
        )
        
        self.search_pattern(
            r'Mac\.getInstance\(["\']([^"\']+)["\']\)',
            "HMAC Algorithm (Signature)",
            "hmac"
        )
        
        self.search_pattern(
            r'SecretKeySpec',
            "Encryption Key (SecretKeySpec)",
            "key"
        )
        
        self.search_pattern(
            r'Base64\.(encode|decode)',
            "Base64 Encoding/Decoding",
            "encoding"
        )
        
        self.search_pattern(
            r'["\']?(nonce|timestamp|digest|signature|request_id|device_id)["\']?\s*[:=]',
            "Dynamic Parameter Names",
            "parameter"
        )
        
        self.search_pattern(
            r'addInterceptor|Interceptor\.intercept',
            "Network Interceptor (Header Injection)",
            "interceptor"
        )
        
        self.search_pattern(
            r'Retrofit\.Builder|OkHttpClient\.Builder',
            "Network Client Configuration",
            "network"
        )
        
        print(f"\n✅ Analysis complete! Found {len(self.findings)} relevant code sections.\n")
    
    def generate_report(self, traffic_params=None, output_file="crypto_logic_report.md"):
        md = []
        md.append("# 🔐 Dynamic Parameter Generation Logic Report")
        md.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        md.append("---\n")
        
        md.append("## 📊 Analysis Summary\n")
        categories = {}
        for finding in self.findings:
            cat = finding['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        md.append("| Category | Count |")
        md.append("|----------|-------|")
        for cat, count in sorted(categories.items()):
            md.append(f"| {cat.upper()} | {count} |")
        md.append("")
        
        if traffic_params:
            md.append("\n## 📡 Captured Traffic Parameters\n")
            md.append(f"**Login URL:** `{traffic_params.get('url', 'N/A')}`\n")
            
            if traffic_params.get('dynamic_params'):
                md.append("### Detected Dynamic Values\n")
                md.append("| Location | Name | Type | Value |")
                md.append("|----------|------|------|-------|")
                for dp in traffic_params['dynamic_params']:
                    value_preview = str(dp['value'])[:40] + "..." if len(str(dp['value'])) > 40 else str(dp['value'])
                    md.append(f"| {dp['location']} | `{dp['name']}` | {dp['type']} | `{value_preview}` |")
                md.append("")
        
        md.append("\n## 🔍 Detailed Code Analysis\n")
        
        categories_order = ['timestamp', 'uuid', 'nonce', 'hash', 'hmac', 'key', 'encoding', 'parameter', 'interceptor', 'network']
        
        for category in categories_order:
            category_findings = [f for f in self.findings if f['category'] == category]
            if not category_findings:
                continue
            
            md.append(f"\n### {category.upper()} Generation\n")
            
            files = {}
            for finding in category_findings:
                file = finding['file']
                if file not in files:
                    files[file] = []
                files[file].append(finding)
            
            for file, findings in files.items():
                md.append(f"\n#### 📄 `{file}`\n")
                
                for i, finding in enumerate(findings, 1):
                    md.append(f"**Finding {i}: {finding['description']}**\n")
                    md.append(f"- **Class:** `{finding['class']}`")
                    md.append(f"- **Method:** `{finding['method']}`\n")
                    md.append("```java")
                    md.append(finding['context'])
                    md.append("```\n")
        
        md.append("\n## 💡 Recommendations\n")
        md.append("Based on the analysis, here's how to replicate the dynamic parameters:\n")
        
        if any(f['category'] == 'timestamp' for f in self.findings):
            md.append("### Timestamps")
            md.append("```python")
            md.append("import time")
            md.append("timestamp = int(time.time() * 1000)  # milliseconds")
            md.append("```\n")
        
        if any(f['category'] == 'uuid' for f in self.findings):
            md.append("### UUIDs")
            md.append("```python")
            md.append("import uuid")
            md.append("request_id = str(uuid.uuid4())")
            md.append("```\n")
        
        if any(f['category'] == 'nonce' for f in self.findings):
            md.append("### Nonces (Random Strings)")
            md.append("```python")
            md.append("import secrets")
            md.append("nonce = secrets.token_urlsafe(16)")
            md.append("```\n")
        
        if any(f['category'] == 'hmac' for f in self.findings):
            md.append("### HMAC Signatures")
            md.append("```python")
            md.append("import hmac")
            md.append("import hashlib")
            md.append("# Replace with actual key and message from the app")
            md.append("secret_key = b'YOUR_SECRET_KEY'")
            md.append("message = b'YOUR_MESSAGE'")
            md.append("signature = hmac.new(secret_key, message, hashlib.sha256).hexdigest()")
            md.append("```\n")
        
        if any(f['category'] == 'hash' for f in self.findings):
            md.append("### Hash Digests")
            md.append("```python")
            md.append("import hashlib")
            md.append("# Replace with actual data")
            md.append("data = b'YOUR_DATA'")
            md.append("digest = hashlib.sha256(data).hexdigest()")
            md.append("```\n")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md))
        
        print(f"✅ Report generated: {output_file}")
        
        json_output = {
            'timestamp': datetime.now().isoformat(),
            'findings': self.findings,
            'summary': categories
        }
        
        with open('crypto_logic.json', 'w', encoding='utf-8') as f:
            json.dump(json_output, f, indent=2, ensure_ascii=False)
        
        print(f"✅ JSON export: crypto_logic.json")

def main():
    jadx_dir = "jadx-output"
    
    if not os.path.exists(jadx_dir):
        print(f"❌ {jadx_dir} not found! Run JADX first.")
        return
    
    analyzer = CryptoLogicAnalyzer(jadx_dir)
    analyzer.analyze_all()
    
    traffic_params = None
    if os.path.exists('login_params.json'):
        with open('login_params.json', 'r', encoding='utf-8') as f:
            traffic_params = json.load(f)
    
    analyzer.generate_report(traffic_params, "crypto_logic_report.md")
    
    print("\n" + "="*60)
    print("📊 FINAL SUMMARY")
    print("="*60)
    print(f"Total findings: {len(analyzer.findings)}")
    print(f"Report: crypto_logic_report.md")
    print(f"JSON: crypto_logic.json")
    print("="*60)

if __name__ == "__main__":
    main()
