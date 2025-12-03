"""
اسکریپت ساده برای تحلیل endpointهای موجود در سیستم و مقایسه با کالکشن‌های Postman
"""
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
POSTMAN_COLLECTIONS_DIR = BASE_DIR / "postman_collections"

def get_all_system_endpoints():
    """استخراج تمام endpointهای سیستم"""
    endpoints = set()
    
    # Mapping prefixها از core/urls.py
    prefix_map = {
        'reservations': 'reservations',
        'accounts': 'auth',
        'hr': 'hr',
        'meals': 'meals',
        'reports': 'reports',
        'centers': 'centers',
    }
    
    urls_files = {
        'reservations': BASE_DIR / 'apps' / 'reservations' / 'urls.py',
        'accounts': BASE_DIR / 'apps' / 'accounts' / 'urls.py',
        'hr': BASE_DIR / 'apps' / 'hr' / 'urls.py',
        'meals': BASE_DIR / 'apps' / 'meals' / 'urls.py',
        'reports': BASE_DIR / 'apps' / 'reports' / 'urls.py',
        'centers': BASE_DIR / 'apps' / 'centers' / 'urls.py',
    }
    
    for app_name, urls_file in urls_files.items():
        if not urls_file.exists():
            continue
            
        with open(urls_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        pattern = r"path\('([^']+)'"
        matches = re.findall(pattern, content)
        
        prefix = prefix_map.get(app_name, '')
        
        for match in matches:
            clean_path = re.sub(r'<[^>]+>', '', match).rstrip('/')
            if clean_path:
                if prefix:
                    full = f"{prefix}/{clean_path}".replace('//', '/')
                else:
                    full = clean_path
                endpoints.add(full)
    
    return endpoints

def get_all_postman_endpoints():
    """استخراج تمام endpointهای Postman"""
    endpoints = set()
    files = [
        'Employee.postman_collection.json',
        'Food Admin.postman_collection.json',
        'HR Admin.postman_collection.json',
        'System Admin.postman_collection.json',
    ]
    
    for fname in files:
        fpath = POSTMAN_COLLECTIONS_DIR / fname
        if not fpath.exists():
            continue
            
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        def extract(items):
            for item in items:
                if 'request' in item:
                    url = item['request'].get('url', {})
                    if isinstance(url, dict):
                        raw = url.get('raw', '')
                        if not raw:
                            parts = url.get('path', [])
                            if parts:
                                raw = '{{base_url}}/' + '/'.join([p for p in parts if p])
                        
                        if '{{base_url}}' in raw:
                            path = raw.split('{{base_url}}')[-1]
                        else:
                            path = raw
                        
                        path = path.split('?')[0].rstrip('/')
                        if path.startswith('/api/'):
                            path = path[5:]
                        path = re.sub(r'\{\{[^}]+\}\}', '', path).replace('//', '/').rstrip('/')
                        if path:
                            endpoints.add(path)
                if 'item' in item:
                    extract(item['item'])
        
        if 'item' in data:
            extract(data['item'])
    
    return endpoints

def main():
    print("=" * 80)
    print("ANALYSIS: System Endpoints vs Postman Collections")
    print("=" * 80)
    print()
    
    system = get_all_system_endpoints()
    postman = get_all_postman_endpoints()
    
    print(f"Total system endpoints: {len(system)}")
    print(f"Total postman endpoints: {len(postman)}")
    print()
    
    in_both = system & postman
    only_system = system - postman
    only_postman = postman - system
    
    print("=" * 80)
    print("RESULTS:")
    print("=" * 80)
    print(f"Endpoints in BOTH: {len(in_both)}")
    print(f"Endpoints ONLY in system (not in Postman): {len(only_system)}")
    print(f"Endpoints ONLY in Postman (not in system): {len(only_postman)}")
    print()
    
    if system:
        coverage = (len(in_both) / len(system)) * 100
        print(f"Coverage: {coverage:.1f}%")
        print()
    
    if only_system:
        print(f"Only in System ({len(only_system)}):")
        for ep in sorted(list(only_system))[:20]:
            print(f"  - {ep}")
        if len(only_system) > 20:
            print(f"  ... and {len(only_system) - 20} more")
        print()
    
    if only_postman:
        print(f"Only in Postman ({len(only_postman)}):")
        for ep in sorted(list(only_postman))[:20]:
            print(f"  - {ep}")
        if len(only_postman) > 20:
            print(f"  ... and {len(only_postman) - 20} more")
        print()

if __name__ == '__main__':
    main()



