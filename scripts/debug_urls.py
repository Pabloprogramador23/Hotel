import os
import django
from django.urls import get_resolver, reverse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hotel_hms.settings")
django.setup()

def list_urls(lis, acc=None):
    if acc is None:
        acc = []
    if not lis:
        return
    l = lis[0]
    if hasattr(l, 'url_patterns'):
        list_urls(l.url_patterns, acc + [str(l.pattern)])
    elif hasattr(l, 'pattern'):
        print(''.join(acc) + str(l.pattern), '->', l.name)
    if len(lis) > 1:
        list_urls(lis[1:], acc)

print("\n--- Listing All URLs ---")
resolver = get_resolver()
# Recursive print approach is tricky with Django's object structure, 
# let's try a simpler iteration or just check specific reverse.

try:
    url = reverse('tablet_control')
    print(f"\nSUCCESS: 'tablet_control' reverses to: {url}")
except Exception as e:
    print(f"\nERROR: Could not reverse 'tablet_control': {e}")

try:
    url = reverse('create_quick_reservation')
    print(f"SUCCESS: 'create_quick_reservation' reverses to: {url}")
except Exception as e:
    print(f"ERROR: Could not reverse 'create_quick_reservation': {e}")

print("\n--- Checking Resolver for 'reservations/' ---")
for p in resolver.url_patterns:
    print(f"Pattern: {p.pattern} - {p}")

