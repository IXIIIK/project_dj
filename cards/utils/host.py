 # utils/host.py
def canonical_host(request):
    # учтём прокси, если используешь X-Forwarded-Host
    host = request.get_host().split(':')[0]  # без порта
    try:
        host_idna = host.encode('idna').decode('ascii')
    except Exception:
        host_idna = host
    return host_idna.lower()
