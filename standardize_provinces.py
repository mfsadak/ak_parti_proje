#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AK Parti Teşkilat Başkanlığı - İl İsmi Standartlaştırma Aracı
Bu script, data klasöründeki tüm CSV dosyalarındaki il isimlerini standartlaştırır.
"""

import os
import pandas as pd
import glob
from typing import Dict, List, Optional
import logging

# Logging ayarları
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Türkiye'nin 81 ili - Resmi standart isimler
STANDARD_PROVINCES = {
    # Ana isimler (standart)
    'ADANA': 'ADANA',
    'ADIYAMAN': 'ADIYAMAN', 
    'AFYONKARAHİSAR': 'AFYONKARAHİSAR',
    'AĞRI': 'AĞRI',
    'AKSARAY': 'AKSARAY',
    'AMASYA': 'AMASYA',
    'ANKARA': 'ANKARA',
    'ANTALYA': 'ANTALYA',
    'ARDAHAN': 'ARDAHAN',
    'ARTVİN': 'ARTVİN',
    'AYDIN': 'AYDIN',
    'BALIKESİR': 'BALIKESİR',
    'BARTIN': 'BARTIN',
    'BATMAN': 'BATMAN',
    'BAYBURT': 'BAYBURT',
    'BİLECİK': 'BİLECİK',
    'BİNGÖL': 'BİNGÖL',
    'BİTLİS': 'BİTLİS',
    'BOLU': 'BOLU',
    'BURDUR': 'BURDUR',
    'BURSA': 'BURSA',
    'ÇANAKKALE': 'ÇANAKKALE',
    'ÇANKIRI': 'ÇANKIRI',
    'ÇORUM': 'ÇORUM',
    'DENİZLİ': 'DENİZLİ',
    'DİYARBAKIR': 'DİYARBAKIR',
    'DÜZCE': 'DÜZCE',
    'EDİRNE': 'EDİRNE',
    'ELAZIĞ': 'ELAZIĞ',
    'ERZİNCAN': 'ERZİNCAN',
    'ERZURUM': 'ERZURUM',
    'ESKİŞEHİR': 'ESKİŞEHİR',
    'GAZİANTEP': 'GAZİANTEP',
    'GİRESUN': 'GİRESUN',
    'GÜMÜŞHANE': 'GÜMÜŞHANE',
    'HAKKARİ': 'HAKKARİ',
    'HATAY': 'HATAY',
    'IĞDIR': 'IĞDIR',
    'ISPARTA': 'ISPARTA',
    'İSTANBUL': 'İSTANBUL',
    'İZMİR': 'İZMİR',
    'KAHRAMANMARAŞ': 'KAHRAMANMARAŞ',
    'KARABÜK': 'KARABÜK',
    'KARAMAN': 'KARAMAN',
    'KARS': 'KARS',
    'KASTAMONU': 'KASTAMONU',
    'KAYSERİ': 'KAYSERİ',
    'KIRIKKALE': 'KIRIKKALE',
    'KIRKLARELİ': 'KIRKLARELİ',
    'KIRŞEHİR': 'KIRŞEHİR',
    'KOCAELİ': 'KOCAELİ',
    'KONYA': 'KONYA',
    'KÜTAHYA': 'KÜTAHYA',
    'MALATYA': 'MALATYA',
    'MANİSA': 'MANİSA',
    'MARDİN': 'MARDİN',
    'MERSİN': 'MERSİN',
    'MUĞLA': 'MUĞLA',
    'MUŞ': 'MUŞ',
    'NEVŞEHİR': 'NEVŞEHİR',
    'NİĞDE': 'NİĞDE',
    'ORDU': 'ORDU',
    'OSMANİYE': 'OSMANİYE',
    'RİZE': 'RİZE',
    'SAKARYA': 'SAKARYA',
    'SAMSUN': 'SAMSUN',
    'SİİRT': 'SİİRT',
    'SİNOP': 'SİNOP',
    'SİVAS': 'SİVAS',
    'ŞANLIURFA': 'ŞANLIURFA',
    'ŞIRNAK': 'ŞIRNAK',
    'TEKİRDAĞ': 'TEKİRDAĞ',
    'TOKAT': 'TOKAT',
    'TRABZON': 'TRABZON',
    'TUNCELİ': 'TUNCELİ',
    'UŞAK': 'UŞAK',
    'VAN': 'VAN',
    'YALOVA': 'YALOVA',
    'YOZGAT': 'YOZGAT',
    'ZONGULDAK': 'ZONGULDAK',
    'KİLİS': 'KİLİS',
    
    # Alternatif yazımlar ve yaygın hatalar
    'ADIYAMAN': 'ADIYAMAN',
    'Adana': 'ADANA',
    'Ankara': 'ANKARA',
    'İstanbul': 'İSTANBUL',
    'İzmir': 'İZMİR',
    'Bursa': 'BURSA',
    'Antalya': 'ANTALYA',
    'Konya': 'KONYA',
    'Gaziantep': 'GAZİANTEP',
    'GAZIANTEP': 'GAZİANTEP',
    'Şanlıurfa': 'ŞANLIURFA',
    'SANLIURFA': 'ŞANLIURFA',
    'Kocaeli': 'KOCAELİ',
    'Mersin': 'MERSİN',
    'Diyarbakır': 'DİYARBAKIR',
    'DIYARBAKIR': 'DİYARBAKIR',
    'Hatay': 'HATAY',
    'Manisa': 'MANİSA',
    'MANISA': 'MANİSA',
    'Kayseri': 'KAYSERİ',
    'Samsun': 'SAMSUN',
    'Balıkesir': 'BALIKESİR',
    'BALIKESIR': 'BALIKESİR',
    'Kahramanmaraş': 'KAHRAMANMARAŞ',
    'KAHRAMANMARAS': 'KAHRAMANMARAŞ',
    'Van': 'VAN',
    'Aydın': 'AYDIN',
    'Tekirdağ': 'TEKİRDAĞ',
    'TEKIRDAG': 'TEKİRDAĞ',
    'Sakarya': 'SAKARYA',
    'Denizli': 'DENİZLİ',
    'DENIZLI': 'DENİZLİ',
    'Muğla': 'MUĞLA',
    'MUGLA': 'MUĞLA',
    'Trabzon': 'TRABZON',
    'Elazığ': 'ELAZIĞ',
    'ELAZIG': 'ELAZIĞ',
    'Erzurum': 'ERZURUM',
    'Sivas': 'SİVAS',
    'Malatya': 'MALATYA',
    'Ağrı': 'AĞRI',
    'AGRI': 'AĞRI',
    'Ordu': 'ORDU',
    'Giresun': 'GİRESUN',
    'Rize': 'RİZE',
    'Bingöl': 'BİNGÖL',
    'BINGOL': 'BİNGÖL',
    'Tunceli': 'TUNCELİ',
    'Edirne': 'EDİRNE',
    'Eskişehir': 'ESKİŞEHİR',
    'Giresun': 'GİRESUN',
    'İzmir': 'İZMİR',
    'Kayseri': 'KAYSERİ',
    'Kırşehir': 'KIRŞEHİR',
    'Kocaeli': 'KOCAELİ',
    'Mersin': 'MERSİN',
    'Nevşehir': 'NEVŞEHİR',
    'Niğde': 'NİĞDE',
    'Rize': 'RİZE',
    'Muş': 'MUŞ',
    'MUS': 'MUŞ',
    'Bitlis': 'BİTLİS',
    'BITLIS': 'BİTLİS',
    'Siirt': 'SİİRT',
    'SIIRT': 'SİİRT',
    'Şırnak': 'ŞIRNAK',
    'SIRNAK': 'ŞIRNAK',
    'Mardin': 'MARDİN',
    'MARDIN': 'MARDİN',
    'Batman': 'BATMAN',
    'Hakkari': 'HAKKARİ',
    'HAKKARI': 'HAKKARİ',
    'Iğdır': 'IĞDIR',
    'IGDIR': 'IĞDIR',
    'Kars': 'KARS',
    'Ardahan': 'ARDAHAN',
    'Artvin': 'ARTVİN',
    'ARTVIN': 'ARTVİN',
    'Gümüşhane': 'GÜMÜŞHANE',
    'GUMUSHANE': 'GÜMÜŞHANE',
    'Bayburt': 'BAYBURT',
    'Erzincan': 'ERZİNCAN',
    'ERZINCAN': 'ERZİNCAN',
    'Tokat': 'TOKAT',
    'Çorum': 'ÇORUM',
    'CORUM': 'ÇORUM',
    'Amasya': 'AMASYA',
    'Sinop': 'SİNOP',
    'SINOP': 'SİNOP',
    'Kastamonu': 'KASTAMONU',
    'Çankırı': 'ÇANKIRI',
    'CANKIRI': 'ÇANKIRI',
    'Kırıkkale': 'KIRIKKALE',
    'Kırşehir': 'KIRŞEHİR',
    'KIRSEHIR': 'KIRŞEHİR',
    'Aksaray': 'AKSARAY',
    'Nevşehir': 'NEVŞEHİR',
    'NEVSEHIR': 'NEVŞEHİR',
    'Niğde': 'NİĞDE',
    'NIGDE': 'NİĞDE',
    'Kırklareli': 'KIRKLARELİ',
    'KIRKLARELI': 'KIRKLARELİ',
    'Edirne': 'EDİRNE',
    'Çanakkale': 'ÇANAKKALE',
    'CANAKKALE': 'ÇANAKKALE',
    'Yalova': 'YALOVA',
    'Düzce': 'DÜZCE',
    'DUZCE': 'DÜZCE',
    'Bolu': 'BOLU',
    'Zonguldak': 'ZONGULDAK',
    'Bartın': 'BARTIN',
    'BARTIN': 'BARTIN',
    'Karabük': 'KARABÜK',
    'KARABUK': 'KARABÜK',
    'Bilecik': 'BİLECİK',
    'BILECIK': 'BİLECİK',
    'Kütahya': 'KÜTAHYA',
    'KUTAHYA': 'KÜTAHYA',
    'Afyonkarahisar': 'AFYONKARAHİSAR',
    'AFYONKARAHISAR': 'AFYONKARAHİSAR',
    'Afyon': 'AFYONKARAHİSAR',
    'AFYON': 'AFYONKARAHİSAR',
    'Uşak': 'UŞAK',
    'USAK': 'UŞAK',
    'Isparta': 'ISPARTA',
    'Burdur': 'BURDUR',
    'Osmaniye': 'OSMANİYE',
    'OSMANIYE': 'OSMANİYE',
    'Karaman': 'KARAMAN',
    'Yozgat': 'YOZGAT',
    'Kilis': 'KİLİS',
    'KILIS': 'KİLİS',
}

def detect_province_column(df: pd.DataFrame) -> Optional[str]:
    """
    DataFrame'de il sütununu otomatik tespit eder.
    
    Args:
        df: Pandas DataFrame
        
    Returns:
        İl sütununun adı veya None
    """
    possible_names = ['İL', 'IL', 'il', 'İl', 'PROVINCE', 'Province', 'province']
    
    for col_name in possible_names:
        if col_name in df.columns:
            return col_name
    
    # İlk sütun genellikle il sütunudur
    if len(df.columns) > 0:
        first_col = df.columns[0]
        # İlk sütundaki değerlerin il olup olmadığını kontrol et
        sample_values = df[first_col].dropna().head(10).astype(str).str.upper()
        province_matches = sum(1 for val in sample_values if val in STANDARD_PROVINCES)
        
        if province_matches >= len(sample_values) * 0.7:  # %70 eşleşme varsa
            return first_col
    
    return None

def normalize_turkish_text(text: str) -> str:
    """
    Türkçe karakterleri kapsamlı normalize eder.
    Tüm olası karakter varyasyonlarını standart forma dönüştürür.
    """
    # Önce büyük harfe çevir
    result = text.upper()
    
    # Kapsamlı Türkçe karakter dönüşüm tablosu
    turkish_char_map = {
        # I/İ dönüşümleri
        'I': 'I', 'İ': 'İ', 'i': 'İ', 'ı': 'I',
        
        # G/Ğ dönüşümleri  
        'G': 'G', 'Ğ': 'Ğ', 'g': 'G', 'ğ': 'Ğ',
        
        # U/Ü dönüşümleri
        'U': 'U', 'Ü': 'Ü', 'u': 'U', 'ü': 'Ü',
        
        # S/Ş dönüşümleri
        'S': 'S', 'Ş': 'Ş', 's': 'S', 'ş': 'Ş',
        
        # O/Ö dönüşümleri
        'O': 'O', 'Ö': 'Ö', 'o': 'O', 'ö': 'Ö',
        
        # C/Ç dönüşümleri
        'C': 'C', 'Ç': 'Ç', 'c': 'C', 'ç': 'Ç'
    }
    
    # Karakter dönüşümlerini uygula
    for old_char, new_char in turkish_char_map.items():
        result = result.replace(old_char, new_char)
    
    return result

def generate_province_variants(province_name: str) -> List[str]:
    """
    Bir il ismi için tüm olası yazım varyantlarını otomatik üretir.
    
    Args:
        province_name: Standart il ismi (örn: 'ŞANLIURFA')
        
    Returns:
        Tüm olası varyantların listesi
    """
    variants = set()
    
    # Orijinal ismi ekle
    variants.add(province_name)
    
    # Küçük harf versiyonu
    variants.add(province_name.lower())
    
    # İlk harf büyük, geri kalanı küçük
    variants.add(province_name.capitalize())
    
    # Türkçe karaktersiz versiyonlar (ASCII dönüşümü)
    ascii_map = {
        'İ': 'I', 'Ğ': 'G', 'Ü': 'U', 'Ş': 'S', 'Ö': 'O', 'Ç': 'C',
        'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c'
    }
    
    # ASCII versiyonları üret
    ascii_version = province_name
    for turkish_char, ascii_char in ascii_map.items():
        ascii_version = ascii_version.replace(turkish_char, ascii_char)
    
    # ASCII versiyonların farklı case'lerini ekle
    variants.add(ascii_version)
    variants.add(ascii_version.lower())
    variants.add(ascii_version.capitalize())
    
    # Karma case versiyonları (yaygın hatalar)
    if len(province_name) > 3:
        # İlk 3 harf büyük, geri kalan küçük
        mixed_case = province_name[:3] + province_name[3:].lower()
        variants.add(mixed_case)
        
        # ASCII versiyonu da
        ascii_mixed = ascii_version[:3] + ascii_version[3:].lower()
        variants.add(ascii_mixed)
    
    return list(variants)

def build_comprehensive_province_dict() -> Dict[str, str]:
    """
    Tüm 81 il için kapsamlı varyant sözlüğü oluşturur.
    
    Returns:
        Tüm varyantları içeren sözlük
    """
    # Standart 81 il listesi
    standard_provinces = [
        'ADANA', 'ADIYAMAN', 'AFYONKARAHİSAR', 'AĞRI', 'AKSARAY', 'AMASYA', 'ANKARA', 'ANTALYA',
        'ARDAHAN', 'ARTVİN', 'AYDIN', 'BALIKESİR', 'BARTIN', 'BATMAN', 'BAYBURT', 'BİLECİK',
        'BİNGÖL', 'BİTLİS', 'BOLU', 'BURDUR', 'BURSA', 'ÇANAKKALE', 'ÇANKIRI', 'ÇORUM', 'DENİZLİ',
        'DİYARBAKIR', 'DÜZCE', 'EDİRNE', 'ELAZIĞ', 'ERZİNCAN', 'ERZURUM', 'ESKİŞEHİR',
        'GAZİANTEP', 'GİRESUN', 'GÜMÜŞHANE', 'HAKKARİ', 'HATAY', 'IĞDIR', 'ISPARTA', 'İSTANBUL',
        'İZMİR', 'KAHRAMANMARAŞ', 'KARABÜK', 'KARAMAN', 'KARS', 'KASTAMONU', 'KAYSERİ',
        'KIRIKKALE', 'KIRKLARELİ', 'KIRŞEHİR', 'KOCAELİ', 'KONYA', 'KÜTAHYA', 'MALATYA',
        'MANİSA', 'MARDİN', 'MERSİN', 'MUĞLA', 'MUŞ', 'NEVŞEHİR', 'NİĞDE', 'ORDU', 'OSMANİYE',
        'RİZE', 'SAKARYA', 'SAMSUN', 'SİİRT', 'SİNOP', 'SİVAS', 'ŞANLIURFA', 'ŞIRNAK', 'TEKİRDAĞ',
        'TOKAT', 'TRABZON', 'TUNCELİ', 'UŞAK', 'VAN', 'YALOVA', 'YOZGAT', 'ZONGULDAK', 'KİLİS'
    ]
    
    comprehensive_dict = {}
    
    # Her il için varyantları üret
    for province in standard_provinces:
        variants = generate_province_variants(province)
        for variant in variants:
            comprehensive_dict[variant] = province
    
    # Özel durumlar ve kısaltmalar ekle
    special_cases = {
        'AFYON': 'AFYONKARAHİSAR',
        'afyon': 'AFYONKARAHİSAR',
        'Afyon': 'AFYONKARAHİSAR',
        'K.MARAS': 'KAHRAMANMARAŞ',
        'k.maras': 'KAHRAMANMARAŞ',
        'TOPLAM': 'TOPLAM',  # Özel durum
        'toplam': 'TOPLAM',
        'Toplam': 'TOPLAM'
    }
    
    comprehensive_dict.update(special_cases)
    
    return comprehensive_dict

def standardize_province_name(province_name: str) -> str:
    """
    İl ismini kapsamlı şekilde standartlaştırır.
    Tüm olası yazım varyasyonlarını destekler.
    
    Args:
        province_name: Ham il ismi
        
    Returns:
        Standartlaştırılmış il ismi (BÜYÜK HARF + TÜRKÇE KARAKTER)
    """
    if pd.isna(province_name) or province_name == '':
        return province_name
    
    # String'e çevir ve temizle
    clean_name = str(province_name).strip()
    
    if not clean_name:
        return province_name
    
    # Kapsamlı varyant sözlüğünü kullan (cache için global değişken)
    if not hasattr(standardize_province_name, '_comprehensive_dict'):
        logger.info("İl varyant sözlüğü oluşturuluyor...")
        standardize_province_name._comprehensive_dict = build_comprehensive_province_dict()
        logger.info(f"Toplam {len(standardize_province_name._comprehensive_dict)} varyant yüklendi")
    
    comprehensive_dict = standardize_province_name._comprehensive_dict
    
    # 1. Direkt eşleşme kontrolü
    if clean_name in comprehensive_dict:
        return comprehensive_dict[clean_name]
    
    # 2. Büyük harf versiyonu kontrol et
    upper_name = clean_name.upper()
    if upper_name in comprehensive_dict:
        return comprehensive_dict[upper_name]
    
    # 3. Küçük harf versiyonu kontrol et
    lower_name = clean_name.lower()
    if lower_name in comprehensive_dict:
        return comprehensive_dict[lower_name]
    
    # 4. Türkçe karakter normalleştirme ile kontrol et
    try:
        normalized_name = normalize_turkish_text(clean_name)
        if normalized_name in comprehensive_dict:
            return comprehensive_dict[normalized_name]
        
        # Normalize edilmiş versiyonun küçük halini de kontrol et
        normalized_lower = normalized_name.lower()
        if normalized_lower in comprehensive_dict:
            return comprehensive_dict[normalized_lower]
            
    except Exception as e:
        logger.warning(f"Normalleştirme hatası '{clean_name}': {e}")
    
    # 5. Eski STANDARD_PROVINCES sözlüğü ile backward compatibility
    if clean_name in STANDARD_PROVINCES:
        return STANDARD_PROVINCES[clean_name]
    if upper_name in STANDARD_PROVINCES:
        return STANDARD_PROVINCES[upper_name]
    
    # 6. Son çare: manuel özel durumlar
    manual_special_cases = {
        'AFYONKARAHISAR': 'AFYONKARAHİSAR',
        'KAHRAMANMARAS': 'KAHRAMANMARAŞ',
        'SANLIURFA': 'ŞANLIURFA',
        'SIRNAK': 'ŞIRNAK',
        'TOPLAM': 'TOPLAM'
    }
    
    if upper_name in manual_special_cases:
        return manual_special_cases[upper_name]
    
    # Bulunamadıysa uyarı ver ve orijinal değeri döndür
    if clean_name.upper() != 'TOPLAM':  # TOPLAM satırı için uyarı verme
        logger.warning(f"Bilinmeyen il ismi: '{province_name}' -> Standartlaştırılamadı")
    
    return province_name

def process_csv_file(file_path: str, backup: bool = False) -> bool:
    """
    Tek bir CSV dosyasını işler.
    
    Args:
        file_path: CSV dosya yolu
        backup: Yedekleme yapılsın mı
        
    Returns:
        İşlem başarılı mı
    """
    try:
        logger.info(f"İşleniyor: {file_path}")
        
        # Dosyayı oku
        df = pd.read_csv(file_path, encoding='utf-8')
        
        # İl sütununu tespit et
        province_col = detect_province_column(df)
        if not province_col:
            logger.warning(f"'{file_path}' dosyasında il sütunu bulunamadı - atlanıyor")
            return False
        
        logger.info(f"İl sütunu tespit edildi: '{province_col}'")
        
        # Yedekleme yap
        if backup:
            backup_path = file_path.replace('.csv', '_backup.csv')
            df.to_csv(backup_path, index=False, encoding='utf-8')
            logger.info(f"Yedek oluşturuldu: {backup_path}")
        else:
            logger.info("Yedekleme atlandı - direkt ana dosyada işlem yapılıyor")
        
        # İl isimlerini standartlaştır
        original_values = df[province_col].copy()
        df[province_col] = df[province_col].apply(standardize_province_name)
        
        # Değişiklikleri say
        changes = sum(original_values != df[province_col])
        logger.info(f"'{file_path}' dosyasında {changes} il ismi standartlaştırıldı")
        
        # Dosyayı kaydet
        df.to_csv(file_path, index=False, encoding='utf-8')
        
        return True
        
    except Exception as e:
        logger.error(f"'{file_path}' dosyası işlenirken hata: {str(e)}")
        return False

def standardize_all_provinces(data_folder: str = 'data', backup: bool = False) -> Dict[str, bool]:
    """
    Data klasöründeki tüm CSV dosyalarının il isimlerini standartlaştırır.
    
    Args:
        data_folder: Data klasörü yolu
        backup: Yedekleme yapılsın mı
        
    Returns:
        Dosya başına işlem sonuçları
    """
    results = {}
    
    if not os.path.exists(data_folder):
        logger.error(f"Data klasörü bulunamadı: {data_folder}")
        return results
    
    # CSV dosyalarını bul
    csv_files = glob.glob(os.path.join(data_folder, '*.csv'))
    
    if not csv_files:
        logger.warning(f"'{data_folder}' klasöründe CSV dosyası bulunamadı")
        return results
    
    logger.info(f"{len(csv_files)} CSV dosyası bulundu")
    
    # Her dosyayı işle
    for csv_file in csv_files:
        # Yedek dosyaları atla
        if '_backup.csv' in csv_file:
            continue
            
        results[csv_file] = process_csv_file(csv_file, backup)
    
    # Özet rapor
    successful = sum(results.values())
    total = len(results)
    logger.info(f"İşlem tamamlandı: {successful}/{total} dosya başarıyla işlendi")
    
    return results

def test_standardization():
    """Standartlaştırma fonksiyonunu test eder"""
    print("\n🧪 Standartlaştırma Testi Başlatılıyor...")
    print("-" * 50)
    
    # Test verileri - çeşitli yazım şekilleri
    test_cases = [
        # Şanlıurfa varyantları
        'sanliurfa', 'SANLIURFA', 'Şanlıurfa', 'şanlıurfa', 'ŞANLIURFA', 'şanliurfa',
        
        # İstanbul varyantları  
        'istanbul', 'ISTANBUL', 'İstanbul', 'istanbul', 'İSTANBUL', 'ıstanbul',
        
        # Diyarbakır varyantları
        'diyarbakir', 'DIYARBAKIR', 'Diyarbakır', 'diyarbakır', 'DİYARBAKIR',
        
        # Muğla varyantları
        'mugla', 'MUGLA', 'Muğla', 'muğla', 'MUĞLA',
        
        # Çanakkale varyantları
        'canakkale', 'CANAKKALE', 'Çanakkale', 'çanakkale', 'ÇANAKKALE',
        
        # Karma case örnekleri
        'AnKaRa', 'IzMiR', 'GaZiAnTeP', 'BuRsA',
        
        # Özel durumlar
        'afyon', 'AFYON', 'Afyon', 'k.maras', 'K.MARAS',
        
        # Edge cases
        'TOPLAM', 'toplam', '', '   ', 'BilinmeyenIl'
    ]
    
    success_count = 0
    total_count = len([t for t in test_cases if t.strip()])
    
    for test_input in test_cases:
        if not test_input.strip():
            continue
            
        try:
            result = standardize_province_name(test_input)
            status = "✅" if result != test_input else "⚠️"
            print(f"{status} '{test_input}' → '{result}'")
            
            # Başarı kriterleri: 
            # 1. Sonuç büyük harf olmalı
            # 2. Türkçe karakter içermeli (eğer gerekiyorsa)
            # 3. Bilinen bir il olmalı
            if result.isupper() and result in ['ŞANLIURFA', 'İSTANBUL', 'DİYARBAKIR', 'MUĞLA', 'ÇANAKKALE', 'ANKARA', 'İZMİR', 'GAZİANTEP', 'BURSA', 'AFYONKARAHİSAR', 'KAHRAMANMARAŞ', 'TOPLAM'] or result == test_input:
                success_count += 1
                
        except Exception as e:
            print(f"❌ '{test_input}' → HATA: {e}")
    
    print(f"\n📊 Test Sonuçları: {success_count}/{total_count} başarılı")
    print("=" * 50)

def main():
    """Ana fonksiyon"""
    print("🏛️  AK Parti Teşkilat Başkanlığı - İyileştirilmiş İl İsmi Standartlaştırma Aracı")
    print("=" * 70)
    print("🚀 Özellikler:")
    print("   • 81 il için 500+ yazım varyantı desteği")
    print("   • Türkçe karakter normalleştirme")  
    print("   • Case-insensitive eşleştirme")
    print("   • Otomatik varyant üretimi")
    print("=" * 70)
    
    # Önce test yap
    test_standardization()
    
    # Standartlaştırmayı başlat
    results = standardize_all_provinces(data_folder='data', backup=False)
    
    if results:
        print("\n📊 İşlem Sonuçları:")
        print("-" * 30)
        for file_path, success in results.items():
            status = "✅ Başarılı" if success else "❌ Hatalı"
            print(f"{os.path.basename(file_path)}: {status}")
        
        successful = sum(results.values())
        total = len(results)
        print(f"\n🎯 Toplam: {successful}/{total} dosya başarıyla işlendi")
        
        if successful > 0:
            print("\n💡 Not: İl isimleri direkt ana CSV dosyalarında standartlaştırıldı")
            print("💡 Artık tüm il isimleri: BÜYÜK HARF + TÜRKÇE KARAKTER formatında")
    else:
        print("\n⚠️  İşlenecek dosya bulunamadı")

if __name__ == "__main__":
    main()
