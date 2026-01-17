#!/usr/bin/env python3
"""
Error Handler Module for Harbi Arbitrage System

Provides centralized error handling for all event_create scripts.
Returns standardized error information that can be displayed in results.html.
"""

import requests
from typing import Dict, Optional, Tuple


# Error message mappings from ERROR_MESSAGES_REFERENCE.txt
ERROR_MESSAGES = {
    # HTTP Status Codes
    400: "HATA 400: İstek formatı hatalı. API parametreleri kontrol edilmeli.",
    401: "HATA 401: Izinsiz bağlantı. API anahtarı veya kimlik bilgileri geçersiz.",
    403: "HATA 403: Erişim engellendi. Ban yemiş olabiliriz.",
    404: "HATA 404: İstenen sayfa bulunamadı. API endpoint'i değişmiş olabilir.",
    429: "HATA 429: Çok fazla istek gönderildi. Ban yemiş olabiliriz.",
    500: "HATA 500: Sitenin sunucusunda bir hata oluştu. Site tarafında sorun var.",
    502: "HATA 502: Sunucu geçidi hatası. Site geçici olarak erişilemez durumda.",
    503: "HATA 503: Servis şu anda kullanılamıyor. Site bakımda veya aşırı yüklü olabilir.",
    504: "HATA 504: Sunucu zaman aşımına uğradı. Site yanıt vermiyor.",
    
    # Network/Connection Errors
    'ConnectionError': "HATA: Siteye bağlanılamıyor. İnternet bağlantınızı kontrol edin veya site çevrimdışı olabilir.",
    'ConnectionRefusedError': "HATA: Sunucu bağlantıyı reddetti. Site erişimi engelliyor olabilir.",
    'ConnectionResetError': "HATA: Bağlantı sunucu tarafından kesildi. VPN/Proxy ayarlarını kontrol edin.",
    'Timeout': "HATA: İstek zaman aşımına uğradı (30 saniye). Site çok yavaş yanıt veriyor veya erişilemiyor.",
    'ReadTimeout': "HATA: Veri okuma zaman aşımına uğradı. Site yanıt vermiyor.",
    'ConnectTimeout': "HATA: Bağlantı kurma zaman aşımına uğradı. Site erişilemiyor.",
    'SSLError': "HATA: SSL sertifika hatası. Site güvenlik sertifikası geçersiz veya süresi dolmuş.",
    'ProxyError': "HATA: Proxy bağlantısı başarısız. VPN/Gluetun container'ı çalışıyor mu kontrol edin.",
    'TooManyRedirects': "HATA: Çok fazla yönlendirme. Site yapılandırması hatalı.",
    
    # Response/Data Errors
    'EmptyResponse': "UYARI: Site yanıt verdi ama içerik boş. Maç ya da takım verisi bulunamadı.",
    'InvalidJSON': "HATA: Geçersiz veri formatı. Site beklenmeyen bir yanıt gönderdi.",
    'JSONDecodeError': "HATA: JSON çözümleme hatası. Site'nin API yanıtı bozuk.",
    'MissingField': "HATA: Gerekli veri alanı eksik. API yapısı değişmiş olabilir.",
    'InvalidDataStructure': "HATA: Veri yapısı beklenenden farklı. API güncellenmiş olabilir, yazılım güncellemese gerekebilir.",
    'NoEventsFound': "BİLGİ: Bağlantı başarılı ama aktif maç bulunamadı (0 etkinlik).",
    'EncodingError': "HATA: Karakter kodlama hatası. Türkçe karakterler düzgün okunamıyor.",
    
    # VPN/Geoblocking Errors
    'GeoblockDetected': "HATA: Site coğrafi kısıtlama uyguluyor. VPN'i kontrol edin.",
    'VPNNotRunning': "HATA: VPN bağlantısı yok. Gluetun container'ları başlatın.",
    'WrongVPNLocation': "UYARI: Yanlış VPN konumu. Stake için Kanada, Stoiximan için Yunanistan gerekli.",
    'CloudflareChallenge': "HATA: Cloudflare koruması algılandı. Manuel tarayıcı müdahalesi gerekebilir.",
    
    # Browser Automation Errors
    'ChromeNotFound': "HATA: Chrome tarayıcı bulunamadı. Chromium kurulumu gerekli: `sudo apt install chromium-browser`",
    'ChromeDriverError': "HATA: Chrome driver hatası. Tarayıcı başlatılamadı.",
    'ElementNotFound': "HATA: Sayfa öğesi bulunamadı. Site yapısı değişmiş olabilir, yazılım güncelleme gerekli.",
    'PageLoadTimeout': "HATA: Sayfa yükleme zaman aşımı. Site çok yavaş veya erişilemiyor.",
    'StaleElementError': "HATA: Sayfa öğesi değişti. Dinamik içerik yeniden yüklendi.",
}


def get_error_message(error: Exception, status_code: Optional[int] = None) -> Tuple[str, str]:
    """
    Convert an exception to a user-friendly Turkish error message.
    
    Args:
        error: The exception that occurred
        status_code: HTTP status code (if applicable)
    
    Returns:
        Tuple of (error_type, error_message)
        error_type: Technical error name for logging
        error_message: User-friendly Turkish message for display
    """
    
    # Check for HTTP status code first
    if status_code is not None:
        error_type = f"HTTP_{status_code}"
        error_message = ERROR_MESSAGES.get(status_code, f"HATA {status_code}: Bilinmeyen sunucu hatası.")
        return (error_type, error_message)
    
    # Check for specific exception types
    error_type = type(error).__name__
    
    # Handle requests exceptions
    if isinstance(error, requests.exceptions.ConnectionError):
        return ('ConnectionError', ERROR_MESSAGES['ConnectionError'])
    elif isinstance(error, requests.exceptions.Timeout):
        return ('Timeout', ERROR_MESSAGES['Timeout'])
    elif isinstance(error, requests.exceptions.ReadTimeout):
        return ('ReadTimeout', ERROR_MESSAGES['ReadTimeout'])
    elif isinstance(error, requests.exceptions.ConnectTimeout):
        return ('ConnectTimeout', ERROR_MESSAGES['ConnectTimeout'])
    elif isinstance(error, requests.exceptions.ProxyError):
        return ('ProxyError', ERROR_MESSAGES['ProxyError'])
    elif isinstance(error, requests.exceptions.SSLError):
        return ('SSLError', ERROR_MESSAGES['SSLError'])
    elif isinstance(error, requests.exceptions.TooManyRedirects):
        return ('TooManyRedirects', ERROR_MESSAGES['TooManyRedirects'])
    
    # Handle JSON errors
    elif 'JSONDecodeError' in error_type:
        return ('JSONDecodeError', ERROR_MESSAGES['JSONDecodeError'])
    
    # Handle other known error types
    elif error_type in ERROR_MESSAGES:
        return (error_type, ERROR_MESSAGES[error_type])
    
    # Generic error message for unknown errors
    else:
        return (error_type, f"HATA: Beklenmeyen hata - {str(error)[:100]}")


def handle_request_error(site_name: str, error: Exception, status_code: Optional[int] = None) -> Dict:
    """
    Handle a request error and return standardized error information.
    
    Args:
        site_name: Name of the site (e.g., "Oddswar", "Roobet")
        error: The exception that occurred
        status_code: HTTP status code (if applicable)
    
    Returns:
        Dict with error information for arb_create.py
    """
    error_type, error_message = get_error_message(error, status_code)
    
    return {
        'site': site_name,
        'error': True,
        'error_type': error_type,
        'error_message': error_message,
        'technical_error': str(error)  # For logging/debugging
    }


def is_ban_indicator(error_type: str, status_code: Optional[int] = None) -> bool:
    """
    Check if the error indicates a possible IP ban or bot detection.
    
    Args:
        error_type: The error type string
        status_code: HTTP status code (if applicable)
    
    Returns:
        True if this error suggests IP ban, False otherwise
    """
    # High probability ban indicators
    if status_code in [403, 429]:
        return True
    if error_type and error_type in ['CloudflareChallenge', 'ConnectionRefusedError', 'ConnectionResetError']:
        return True
    
    return False


# Success response template
def success_response(site_name: str) -> Dict:
    """
    Return a success response template.
    
    Args:
        site_name: Name of the site
    
    Returns:
        Dict with success flag
    """
    return {
        'site': site_name,
        'error': False
    }
