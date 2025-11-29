"""
اسکریپت برای تحلیل endpointهای موجود در سیستم و مقایسه با کالکشن‌های Postman
"""
import json
import re
from pathlib import Path

# مسیرهای فایل‌ها
BASE_DIR = Path(__file__).parent
POSTMAN_COLLECTIONS_DIR = BASE_DIR / "postman_collections"

def extract_endpoints_from_urls():
    """استخراج تمام endpointهای موجود در سیستم از فایل‌های urls.py"""
    endpoints = set()
    
    # خواندن فایل‌های urls.py
    urls_files = {
        'reservations': BASE_DIR / 'apps' / 'reservations' / 'urls.py',
        'accounts': BASE_DIR / 'apps' / 'accounts' / 'urls.py',
        'hr': BASE_DIR / 'apps' / 'hr' / 'urls.py',
        'meals': BASE_DIR / 'apps' / 'meals' / 'urls.py',
        'reports': BASE_DIR / 'apps' / 'reports' / 'urls.py',
        'centers': BASE_DIR / 'apps' / 'centers' / 'urls.py',
    }
    
    # خواندن core/urls.py برای prefixها
    core_urls = BASE_DIR / 'core' / 'urls.py'
    prefixes = {}
    
    with open(core_urls, 'r', encoding='utf-8') as f:
        content = f.read()
        # استخراج prefixها
        for line in content.split('\n'):
            if 'path(' in line and 'include(' in line:
                match = re.search(r'path\("([^"]+)",\s*include\("([^"]+)"\)', line)
                if match:
                    prefix = match.group(1).rstrip('/')
                    # حذف api/ از prefix
                    if prefix.startswith('api/'):
                        prefix = prefix[4:]
                    app = match.group(2).split('.')[-1]
                    prefixes[app] = prefix
    
    # خواندن هر فایل urls.py
    for app_name, urls_file in urls_files.items():
        if not urls_file.exists():
            continue
            
        with open(urls_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # استخراج pathها
        pattern = r"path\('([^']+)'"
        matches = re.findall(pattern, content)
        
        for match in matches:
            # حذف پارامترهای URL مثل <int:pk>
            clean_path = re.sub(r'<[^>]+>', '', match).rstrip('/')
            if clean_path:
                # اضافه کردن prefix
                prefix = prefixes.get(app_name, '')
                if prefix:
                    full_path = f"{prefix}/{clean_path}".replace('//', '/')
                else:
                    full_path = clean_path
                endpoints.add(full_path)
    
    return endpoints

def extract_endpoints_from_postman_collections():
    """استخراج تمام endpointهای موجود در کالکشن‌های Postman"""
    endpoints = set()
    collection_files = [
        'Employee.postman_collection.json',
        'Food Admin.postman_collection.json',
        'HR Admin.postman_collection.json',
        'System Admin.postman_collection.json',
    ]
    
    for collection_file in collection_files:
        file_path = POSTMAN_COLLECTIONS_DIR / collection_file
        if not file_path.exists():
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # استخراج endpointها از items
        def extract_from_items(items):
            for item in items:
                if 'request' in item:
                    url = item['request'].get('url', {})
                    if isinstance(url, dict):
                        raw = url.get('raw', '')
                        if not raw:
                            # اگر raw وجود ندارد، از path استفاده کن
                            path_parts = url.get('path', [])
                            if path_parts:
                                raw = '{{base_url}}/' + '/'.join([p for p in path_parts if p])
                        
                        # استخراج path از URL
                        if '{{base_url}}' in raw:
                            path = raw.split('{{base_url}}')[-1]
                        else:
                            path = raw
                        
                        # حذف query parameters
                        path = path.split('?')[0]
                        # حذف trailing slash
                        path = path.rstrip('/')
                        if path.startswith('/api/'):
                            # حذف /api/ prefix
                            path = path[5:]
                        # حذف متغیرهای Postman مثل {{id}}
                        path = re.sub(r'\{\{[^}]+\}\}', '', path)
                        path = path.replace('//', '/').rstrip('/')
                        if path:
                            endpoints.add(path)
                if 'item' in item:
                    extract_from_items(item['item'])
        
        if 'item' in data:
            extract_from_items(data['item'])
    
    return endpoints

def main():
    import sys
    import io
    # تنظیم encoding برای Windows
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("=" * 80)
    print("تحلیل endpointهای سیستم و کالکشن‌های Postman")
    print("=" * 80)
    print()
    
    # استخراج endpointها
    print("در حال استخراج endpointهای سیستم...")
    system_endpoints = extract_endpoints_from_urls()
    print(f"✓ تعداد endpointهای سیستم: {len(system_endpoints)}")
    print()
    
    print("در حال استخراج endpointهای کالکشن‌های Postman...")
    postman_endpoints = extract_endpoints_from_postman_collections()
    print(f"✓ تعداد endpointهای موجود در کالکشن‌ها: {len(postman_endpoints)}")
    print()
    
    # مقایسه
    in_postman = system_endpoints & postman_endpoints
    not_in_postman = system_endpoints - postman_endpoints
    only_in_postman = postman_endpoints - system_endpoints
    
    print("=" * 80)
    print("نتایج:")
    print("=" * 80)
    print(f"✅ تعداد endpointهای موجود در کالکشن‌ها: {len(in_postman)}")
    print(f"❌ تعداد endpointهای موجود در سیستم که در کالکشن‌ها نیستند: {len(not_in_postman)}")
    print(f"⚠️  تعداد endpointهای موجود در کالکشن‌ها که در سیستم نیستند: {len(only_in_postman)}")
    print()
    
    # درصد پوشش
    if system_endpoints:
        coverage = (len(in_postman) / len(system_endpoints)) * 100
        print(f"📊 درصد پوشش: {coverage:.1f}%")
        print()
    
    # لیست endpointهای موجود در سیستم که در کالکشن‌ها نیستند
    if not_in_postman:
        print("=" * 80)
        print(f"Endpointهای موجود در سیستم که در کالکشن‌ها نیستند ({len(not_in_postman)} مورد):")
        print("=" * 80)
        for endpoint in sorted(not_in_postman):
            print(f"  - {endpoint}")
        print()
    
    # لیست endpointهای موجود در کالکشن‌ها که در سیستم نیستند
    if only_in_postman:
        print("=" * 80)
        print(f"Endpointهای موجود در کالکشن‌ها که در سیستم نیستند ({len(only_in_postman)} مورد):")
        print("=" * 80)
        for endpoint in sorted(only_in_postman):
            print(f"  - {endpoint}")
        print()
    
    # نمایش نمونه endpointهای موجود در کالکشن‌ها
    if in_postman:
        print("=" * 80)
        print(f"نمونه endpointهای موجود در کالکشن‌ها ({min(5, len(in_postman))} مورد از {len(in_postman)}):")
        print("=" * 80)
        for endpoint in sorted(list(in_postman))[:5]:
            print(f"  ✓ {endpoint}")
        if len(in_postman) > 5:
            print(f"  ... و {len(in_postman) - 5} مورد دیگر")
        print()

if __name__ == '__main__':
    main()
