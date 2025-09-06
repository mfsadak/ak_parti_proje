#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AK Parti Dinamik Puanlama Sistemi
10'luk Önem Katsayısı Sistemi ile Esnek Aktivite Değerlendirmesi
"""

# import pandas as pd  # Geçici olarak kapatıldı
import warnings
import os
import json
from typing import Dict, List, Optional, Any
import openai
from pathlib import Path

warnings.filterwarnings('ignore')

class DinamikPuanlamaSistemi:
    # İl kategorileri için nüfus eşikleri (mevcut sistemden)
    MEGA_IL_ESIK = 3000000
    BUYUK_IL_ESIK = 1500000
    ORTA_IL_ESIK = 500000
    VARSAYILAN_NUFUS = 500000
    
    # Kategori katsayıları (mevcut sistemden)
    KATEGORI_KATSAYILARI = {
        "Mega İl": 1.0,      # En kolay (3M+ nüfus, büyük kaynak, altyapı)
        "Büyük İl": 1.08,    # Kolay (1.5M-3M nüfus)
        "Orta İl": 1.15,     # Orta zorluk (500K-1.5M nüfus)
        "Küçük İl": 1.30     # Zor (500K'dan az nüfus, sınırlı kaynak)
    }
    
    # Varsayılan aktivite önem katsayıları (10'luk sistem)
    VARSAYILAN_ONEM_KATSAYILARI = {
        'uyelik': 4.0,      # Üyelik (40 puan -> 4.0 katsayı)
        'danisma': 3.0,     # Danışma Meclisi (30 puan -> 3.0 katsayı)
        'ramazan': 2.0,     # Ramazan (20 puan -> 2.0 katsayı)
        'bayrak': 1.0       # Bayrak (10 puan -> 1.0 katsayı)
    }
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Dinamik Puanlama Sistemi"""
        self.veriler = {}
        self.il_kategorileri = {}
        self.kategori_katsayilar = {}
        self.sonuclar = {}
        self.nufus_bilgileri = None
        self.aktivite_katsayilari = self.VARSAYILAN_ONEM_KATSAYILARI.copy()
        self.hesaplama_metodlari = {}
        
        # OpenAI API ayarları
        if openai_api_key:
            openai.api_key = openai_api_key
            self.claude_api_available = True
        else:
            self.claude_api_available = False
            print("⚠️ OpenAI API key not provided. New activity analysis will be limited.")
        
        # Klasörleri oluştur
        os.makedirs('output_csv', exist_ok=True)
        os.makedirs('dynamic_configs', exist_ok=True)
        os.makedirs('dynamic_methods', exist_ok=True)
        
        # Mevcut hesaplama metodlarını yükle
        self._load_core_calculation_methods()
        
    def _load_core_calculation_methods(self):
        """Mevcut 4 aktivite için hesaplama metodlarını yükle"""
        self.hesaplama_metodlari = {
            'uyelik': self._uyelik_puani_hesapla,
            'danisma': self._danisma_puani_hesapla,
            'ramazan': self._ramazan_puani_hesapla,
            'bayrak': self._bayrak_puani_hesapla
        }
    
    def _veri_temizle(self):
        """Mevcut veri temizleme metodları (puanlama_sistemi.py'den)"""
        
        # Üyelik verisi temizleme
        if 'uyelik' in self.veriler:
            numeric_cols = ['YAPILMASI GEREKEN TOPLAM ÜYE', 'YÖNETİM KURULU YAPMASI GEREKEN ÜYE SAYISI', 
                           'YÖNETİM KURULU ÜYELERİ TARAFINDAN REFERANS OLUNAN YENİ ÜYE SAYISI',
                           'YAPILAN YENİ ÜYE SAYISI', 'SİLİNEN  ÜYE SAYISI', 'MEVCUT ÜYE']
            
            for col in numeric_cols:
                if col in self.veriler['uyelik'].columns:
                    self.veriler['uyelik'][col] = (self.veriler['uyelik'][col]
                                                 .astype(str)
                                                 .str.replace(',', '')
                                                 .str.replace('"', ''))
                    self.veriler['uyelik'][col] = pd.to_numeric(self.veriler['uyelik'][col], errors='coerce').fillna(0)
            
            # Hedefe ulaşma oranını temizle
            if 'HEDEFE ULAŞMA ORANI' in self.veriler['uyelik'].columns:
                self.veriler['uyelik']['HEDEFE ULAŞMA ORANI'] = (self.veriler['uyelik']['HEDEFE ULAŞMA ORANI']
                                                                .str.replace('%', '')
                                                                .astype(float))
        
        # Ramazan verisi temizleme
        if 'ramazan' in self.veriler:
            ramazan_cols = ['GÖNÜL SOFRASI', 'SAHUR PROGRAMI', 'İFTAR PROGRAMI', 'TOPLAM ULAŞILAN KİŞİ']
            for col in ramazan_cols:
                if col in self.veriler['ramazan'].columns:
                    self.veriler['ramazan'][col] = (self.veriler['ramazan'][col]
                                                  .astype(str)
                                                  .str.replace(',', '')
                                                  .str.replace('"', ''))
                    self.veriler['ramazan'][col] = pd.to_numeric(self.veriler['ramazan'][col], errors='coerce').fillna(0)
            
            # TOPLAM satırını çıkar
            self.veriler['ramazan'] = self.veriler['ramazan'][self.veriler['ramazan']['İL'] != 'TOPLAM'].copy()
        
        print("✅ Veri temizleme tamamlandı")
    
    def _katsayilari_yeniden_dagit(self):
        """Verisi olmayan aktivitelerin katsayılarını mevcut aktivitelere oransal dağıt"""
        
        # Verisi olan ve olmayan aktiviteleri ayır
        mevcut_aktiviteler = list(self.veriler.keys())
        eksik_aktiviteler = []
        toplam_eksik_katsayi = 0
        
        for aktivite, katsayi in self.aktivite_katsayilari.items():
            if aktivite not in mevcut_aktiviteler:
                eksik_aktiviteler.append(aktivite)
                toplam_eksik_katsayi += katsayi
        
        if not eksik_aktiviteler:
            print("✅ Tüm aktiviteler mevcut, katsayı dağıtımı gerekli değil")
            return
        
        print(f"🔄 Eksik aktiviteler tespit edildi: {', '.join(eksik_aktiviteler)}")
        print(f"📊 Dağıtılacak toplam katsayı: {toplam_eksik_katsayi}")
        
        # Mevcut aktivitelerin toplam katsayısını hesapla
        mevcut_toplam_katsayi = sum(
            katsayi for aktivite, katsayi in self.aktivite_katsayilari.items() 
            if aktivite in mevcut_aktiviteler
        )
        
        if mevcut_toplam_katsayi == 0:
            print("❌ Hiç mevcut aktivite yok, katsayı dağıtımı yapılamaz")
            return
        
        # Yeni katsayıları hesapla (oransal dağıtım)
        yeni_katsayilar = {}
        for aktivite, katsayi in self.aktivite_katsayilari.items():
            if aktivite in mevcut_aktiviteler:
                # Bu aktivitenin oranı
                oran = katsayi / mevcut_toplam_katsayi
                # Eksik katsayılardan bu orana düşen pay
                ek_katsayi = toplam_eksik_katsayi * oran
                # Yeni katsayı
                yeni_katsayi = katsayi + ek_katsayi
                yeni_katsayilar[aktivite] = yeni_katsayi
                
                print(f"🎯 {aktivite.title()}: {katsayi:.2f} → {yeni_katsayi:.2f} (oran: %{oran*100:.1f}, ek: +{ek_katsayi:.2f})")
        
        # Katsayıları güncelle
        self.aktivite_katsayilari = yeni_katsayilar
        
        # Toplam kontrolü
        yeni_toplam = sum(yeni_katsayilar.values())
        print(f"✅ Katsayı dağıtımı tamamlandı. Yeni toplam: {yeni_toplam:.2f}")
        
        # Hesaplama metodlarını da güncelle (eksik olanları çıkar)
        self.hesaplama_metodlari = {
            aktivite: metod 
            for aktivite, metod in self.hesaplama_metodlari.items() 
            if aktivite in mevcut_aktiviteler
        }
    
    def _nufus_verileri_yukle(self):
        """Nüfus verilerini yükle"""
        if self.nufus_bilgileri is not None:
            return self.nufus_bilgileri
        
        try:
            nufus_df = pd.read_csv('data/il_ilçe_nüfus.csv', encoding='utf-8')
            self.nufus_bilgileri = dict(zip(nufus_df['İL'], nufus_df['NÜFUS']))
        except Exception as e:
            print(f"⚠️ il_ilçe_nüfus.csv bulunamadı: {e}")
            print("Varsayılan nüfus değerleri kullanılıyor")
            self.nufus_bilgileri = {}
        
        return self.nufus_bilgileri
    
    def il_kategorileri_belirle(self):
        """İl kategorilerini belirle (mevcut sistemden)"""
        nufus_dict = self._nufus_verileri_yukle()
        
        # İl listesi için herhangi bir veriyi kullan
        il_listesi = []
        for veri in self.veriler.values():
            if 'İL' in veri.columns:
                il_listesi = veri['İL'].unique()
                break
        
        if not il_listesi.size:
            print("❌ İl listesi bulunamadı")
            return
        
        for il in il_listesi:
            nufus = nufus_dict.get(il, self.VARSAYILAN_NUFUS)
            
            if nufus >= self.MEGA_IL_ESIK:
                kategori = "Mega İl"
            elif nufus >= self.BUYUK_IL_ESIK:
                kategori = "Büyük İl"
            elif nufus >= self.ORTA_IL_ESIK:
                kategori = "Orta İl"
            else:
                kategori = "Küçük İl"
            
            self.il_kategorileri[il] = {
                'kategori': kategori,
                'nufus': nufus
            }
            
            self.kategori_katsayilar[il] = {
                'grup': kategori,
                'katsayi': self.KATEGORI_KATSAYILARI.get(kategori, 1.15)
            }
        
        print("✅ İl kategorileri belirlendi")
    
    # Mevcut hesaplama metodları (puanlama_sistemi.py'den uyarlanmış)
    def _danisma_puan_hesapla_base(self, ortalama, max_puan=1.0):
        """Danışma meclisi puan hesaplama (10'luk sisteme uyarlanmış)"""
        if ortalama >= 0.95:
            return max_puan
        elif ortalama >= 0.90:
            return max_puan * 0.9
        elif ortalama >= 0.80:
            return max_puan * 0.8
        elif ortalama >= 0.70:
            return max_puan * 0.7
        elif ortalama >= 0.60:
            return max_puan * 0.6
        elif ortalama >= 0.50:
            return max_puan * 0.5
        elif ortalama >= 0.40:
            return max_puan * 0.4
        elif ortalama >= 0.30:
            return max_puan * 0.3
        elif ortalama >= 0.20:
            return max_puan * 0.2
        elif ortalama >= 0.10:
            return max_puan * 0.1
        else:
            return 0
    
    def _uyelik_puani_hesapla(self):
        """Üyelik puanı hesaplama (10'luk sisteme uyarlanmış)"""
        puanlar = {}
        max_puan = self.aktivite_katsayilari.get('uyelik', 4.0) * 10  # 40 puan -> 40
        
        if 'uyelik' not in self.veriler:
            return puanlar
        
        for _, row in self.veriler['uyelik'].iterrows():
            il = row['İL']
            hedefe_ulasma = row.get('HEDEFE ULAŞMA ORANI', 0)
            yk_hedef = row.get('YÖNETİM KURULU YAPMASI GEREKEN ÜYE SAYISI', 0)
            yk_gerceklesen = row.get('YÖNETİM KURULU ÜYELERİ TARAFINDAN REFERANS OLUNAN YENİ ÜYE SAYISI', 0)
            
            # Temel başarı puanı (27/40 oranı korundu)
            temel_oran = 27/40
            if hedefe_ulasma >= 100:
                temel_puan = max_puan * temel_oran
            elif hedefe_ulasma >= 90:
                temel_puan = max_puan * temel_oran * (25/27)
            elif hedefe_ulasma >= 80:
                temel_puan = max_puan * temel_oran * (23/27)
            elif hedefe_ulasma >= 70:
                temel_puan = max_puan * temel_oran * (21/27)
            elif hedefe_ulasma >= 60:
                temel_puan = max_puan * temel_oran * (19/27)
            elif hedefe_ulasma >= 50:
                temel_puan = max_puan * temel_oran * (17/27)
            elif hedefe_ulasma >= 40:
                temel_puan = max_puan * temel_oran * (15/27)
            elif hedefe_ulasma >= 30:
                temel_puan = max_puan * temel_oran * (12/27)
            elif hedefe_ulasma >= 20:
                temel_puan = max_puan * temel_oran * (9/27)
            elif hedefe_ulasma >= 15:
                temel_puan = max_puan * temel_oran * (6/27)
            elif hedefe_ulasma >= 10:
                temel_puan = max_puan * temel_oran * (3/27)
            else:
                temel_puan = 0
            
            # Mükemmellik ödülü (8/40 oranı korundu)
            mukemmellik_oran = 8/40
            if hedefe_ulasma >= 200:
                mukemmellik_puan = max_puan * mukemmellik_oran
            elif hedefe_ulasma >= 150:
                mukemmellik_puan = max_puan * mukemmellik_oran * (6/8)
            elif hedefe_ulasma >= 120:
                mukemmellik_puan = max_puan * mukemmellik_oran * (4/8)
            elif hedefe_ulasma >= 100:
                mukemmellik_puan = max_puan * mukemmellik_oran * (2/8)
            else:
                mukemmellik_puan = 0
            
            # Yönetim kurulu performansı (5/40 oranı korundu)
            yk_oran = 5/40
            if yk_hedef > 0:
                yk_basari_orani = (yk_gerceklesen / yk_hedef) * 100
                if yk_basari_orani >= 100:
                    yk_puan = max_puan * yk_oran
                elif yk_basari_orani >= 80:
                    yk_puan = max_puan * yk_oran * (4/5)
                elif yk_basari_orani >= 60:
                    yk_puan = max_puan * yk_oran * (3/5)
                elif yk_basari_orani >= 40:
                    yk_puan = max_puan * yk_oran * (2/5)
                elif yk_basari_orani >= 20:
                    yk_puan = max_puan * yk_oran * (1/5)
                else:
                    yk_puan = 0
            else:
                yk_basari_orani = 0
                yk_puan = 0
            
            toplam_uyelik = temel_puan + mukemmellik_puan + yk_puan
            
            puanlar[il] = {
                'temel_puan': temel_puan,
                'mukemmellik_puan': mukemmellik_puan,
                'yk_puan': yk_puan,
                'yk_basari_orani': yk_basari_orani,
                'hedefe_ulasma_orani': hedefe_ulasma,
                'toplam_uyelik': toplam_uyelik
            }
        
        return puanlar
    
    def _danisma_puani_hesapla(self):
        """Danışma meclisi puanı hesaplama (10'luk sisteme uyarlanmış)"""
        puanlar = {}
        max_puan = self.aktivite_katsayilari.get('danisma', 3.0) * 10  # 30 puan -> 30
        
        if 'danisma' not in self.veriler:
            return puanlar
        
        # İl listesi al
        il_listesi = []
        for veri in self.veriler.values():
            if 'İL' in veri.columns:
                il_listesi = veri['İL'].unique()
                break
        
        for il in il_listesi:
            il_danisma = self.veriler['danisma'][self.veriler['danisma']['İL'] == il]
            
            if len(il_danisma) == 0:
                puanlar[il] = {'toplam_danisma': 0}
                continue
            
            # İl başkanlığı ve ilçeler
            il_baskanligi = il_danisma[il_danisma['İLÇE'] == 'İL']
            ilceler = il_danisma[il_danisma['İLÇE'] != 'İL']
            
            # İl başkanlığı performansı (15/30 oranı)
            il_puan_oran = 15/30
            if len(il_baskanligi) > 0:
                il_row = il_baskanligi.iloc[0]
                il_haziran = 1 if il_row.get('HAZİRAN') == 'YAPILDI' else 0
                il_temmuz = 1 if il_row.get('TEMMUZ') == 'YAPILDI' else 0
                il_agustos = 1 if il_row.get('AĞUSTOS') == 'YAPILDI' else (0.7 if il_row.get('AĞUSTOS') == 'PLANLANDI' else 0)
                
                il_ortalama = (il_haziran + il_temmuz + il_agustos) / 3
                il_puan = self._danisma_puan_hesapla_base(il_ortalama, max_puan * il_puan_oran)
            else:
                il_ortalama = 0
                il_puan = 0
            
            # İlçe performansı (15/30 oranı)
            ilce_puan_oran = 15/30
            if len(ilceler) > 0:
                ilce_haziran_oran = len(ilceler[ilceler['HAZİRAN'] == 'YAPILDI']) / len(ilceler)
                ilce_temmuz_oran = len(ilceler[ilceler['TEMMUZ'] == 'YAPILDI']) / len(ilceler)
                ilce_agustos_yapilan = len(ilceler[ilceler['AĞUSTOS'] == 'YAPILDI'])
                ilce_agustos_planlanan = len(ilceler[ilceler['AĞUSTOS'] == 'PLANLANDI'])
                ilce_agustos_oran = (ilce_agustos_yapilan + ilce_agustos_planlanan * 0.7) / len(ilceler)
                
                ilce_ortalama = (ilce_haziran_oran + ilce_temmuz_oran + ilce_agustos_oran) / 3
                ilce_puan = self._danisma_puan_hesapla_base(ilce_ortalama, max_puan * ilce_puan_oran)
                
                # Kategori katsayısı bonusu
                kategori_katsayi = self.kategori_katsayilar.get(il, {}).get('katsayi', 1.0)
                if kategori_katsayi > 1.0 and ilce_ortalama >= 0.5:
                    ilce_bonus = min(max_puan * (4/30), (kategori_katsayi - 1.0) * max_puan * (16/30))
                    ilce_final_puan = min(max_puan * ilce_puan_oran, ilce_puan + ilce_bonus)
                else:
                    ilce_bonus = 0
                    ilce_final_puan = ilce_puan
            else:
                ilce_ortalama = 0
                ilce_puan = 0
                ilce_final_puan = 0
                ilce_bonus = 0
            
            final_puan = il_puan + ilce_final_puan
            
            puanlar[il] = {
                'il_ortalama': il_ortalama,
                'ilce_ortalama': ilce_ortalama,
                'genel_ortalama': (il_ortalama + ilce_ortalama) / 2,
                'il_puan': il_puan,
                'ilce_puan': ilce_puan,
                'il_final_puan': il_puan,
                'ilce_final_puan': ilce_final_puan,
                'ilce_bonus': ilce_bonus,
                'toplam_danisma': final_puan,
                'il_sayisi': len(il_baskanligi),
                'ilce_sayisi': len(ilceler),
                'toplam_birim': len(il_danisma)
            }
        
        return puanlar
    
    def _ramazan_puani_hesapla(self):
        """Ramazan puanı hesaplama (10'luk sisteme uyarlanmış)"""
        puanlar = {}
        max_puan = self.aktivite_katsayilari.get('ramazan', 2.0) * 10  # 20 puan -> 20
        
        if 'ramazan' not in self.veriler:
            return puanlar
        
        nufus_bilgileri = self._nufus_verileri_yukle()
        
        # Nüfus erişim oranları
        nufus_erisim_oranlari = []
        for _, row in self.veriler['ramazan'].iterrows():
            if row['İL'] == 'TOPLAM':
                continue
            il = row['İL']
            toplam_kisi = row.get('TOPLAM ULAŞILAN KİŞİ', 0)
            nufus = nufus_bilgileri.get(il, self.VARSAYILAN_NUFUS)
            nufus_erisim_orani = (toplam_kisi / nufus) * 100 if nufus > 0 else 0
            nufus_erisim_oranlari.append(nufus_erisim_orani)
        
        max_nufus_orani = max(nufus_erisim_oranlari) if nufus_erisim_oranlari else 1
        min_nufus_orani = min(nufus_erisim_oranlari) if nufus_erisim_oranlari else 0
        
        for _, row in self.veriler['ramazan'].iterrows():
            if row['İL'] == 'TOPLAM':
                continue
            
            il = row['İL']
            toplam_kisi = row.get('TOPLAM ULAŞILAN KİŞİ', 0)
            nufus = nufus_bilgileri.get(il, self.VARSAYILAN_NUFUS)
            
            nufus_erisim_orani = (toplam_kisi / nufus) * 100 if nufus > 0 else 0
            
            # Nüfus erişim puanı (15/20 oranı)
            erisim_oran = 15/20
            if max_nufus_orani > min_nufus_orani:
                normalize_oran = (nufus_erisim_orani - min_nufus_orani) / (max_nufus_orani - min_nufus_orani)
            else:
                normalize_oran = 1.0
            
            erisim_puan = normalize_oran * max_puan * erisim_oran
            
            # Aktivite çeşitliliği (5/20 oranı)
            aktivite_oran = 5/20
            aktivite_sutunlari = [
                'GÖNÜL SOFRASI', 'SAHUR PROGRAMI', 'İFTAR PROGRAMI', 
                'ÇAT KAPI ZİYARET', 'YARDIM DAĞITIMI', 
                'ŞEHİT GAZİ AİLELERİ, STK, ESNAF, KIRAATHANE, YAŞLI, HASTA, ENGELLİ ZİYARETLERİ',
                'CAMİ ÇALIŞMALARI', 'MAHALLE / KÖY, TAZİYE, MEZARLIK ZİYARETLERİ',
                'ÜYE ARAMA VE MESAJ ÇALIŞMALARI'
            ]
            
            aktivite_sayisi = 0
            for sutun in aktivite_sutunlari:
                if sutun in row and pd.notna(row[sutun]) and row[sutun] != '' and row[sutun] != 0:
                    aktivite_sayisi += 1
            
            if aktivite_sayisi >= 8:
                aktivite_puan = max_puan * aktivite_oran
            elif aktivite_sayisi >= 6:
                aktivite_puan = max_puan * aktivite_oran * (4/5)
            elif aktivite_sayisi >= 4:
                aktivite_puan = max_puan * aktivite_oran * (3/5)
            elif aktivite_sayisi >= 2:
                aktivite_puan = max_puan * aktivite_oran * (2/5)
            elif aktivite_sayisi >= 1:
                aktivite_puan = max_puan * aktivite_oran * (1/5)
            else:
                aktivite_puan = 0
            
            toplam_ramazan = erisim_puan + aktivite_puan
            
            puanlar[il] = {
                'erişim_puan': erisim_puan,
                'aktivite_puan': aktivite_puan,
                'aktivite_sayisi': aktivite_sayisi,
                'toplam_ulaşilan': toplam_kisi,
                'nufus': nufus,
                'nufus_erisim_orani': nufus_erisim_orani,
                'normalize_oran': normalize_oran,
                'toplam_ramazan': toplam_ramazan
            }
        
        return puanlar
    
    def _bayrak_puani_hesapla(self):
        """Bayrak puanı hesaplama (10'luk sisteme uyarlanmış)"""
        puanlar = {}
        max_puan = self.aktivite_katsayilari.get('bayrak', 1.0) * 10  # 10 puan -> 10
        
        if 'bayrak' not in self.veriler:
            return puanlar
        
        nufus_bilgileri = self._nufus_verileri_yukle()
        
        # Nüfus bayrak oranları
        nufus_bayrak_oranlari = []
        for _, row in self.veriler['bayrak'].iterrows():
            il = row['İL']
            bayrak_sayisi = row.get('BAYRAK ADEDİ', 0)
            nufus = nufus_bilgileri.get(il, self.VARSAYILAN_NUFUS)
            nufus_bayrak_orani = (bayrak_sayisi / nufus) * 1000 if nufus > 0 else 0
            nufus_bayrak_oranlari.append(nufus_bayrak_orani)
        
        max_oran = max(nufus_bayrak_oranlari) if nufus_bayrak_oranlari else 1
        min_oran = min(nufus_bayrak_oranlari) if nufus_bayrak_oranlari else 0
        
        for _, row in self.veriler['bayrak'].iterrows():
            il = row['İL']
            bayrak_sayisi = row.get('BAYRAK ADEDİ', 0)
            calisma_turu = row.get('YAPILAN ÇALIŞMA', '')
            nufus = nufus_bilgileri.get(il, self.VARSAYILAN_NUFUS)
            
            nufus_bayrak_orani = (bayrak_sayisi / nufus) * 1000 if nufus > 0 else 0
            
            # Nüfus erişim puanı (8/10 oranı)
            erisim_oran = 8/10
            if max_oran > min_oran:
                normalize_oran = (nufus_bayrak_orani - min_oran) / (max_oran - min_oran)
            else:
                normalize_oran = 1.0
            
            erisim_puan = normalize_oran * max_puan * erisim_oran
            
            # Çalışma türü bonusu (2/10 oranı)
            bonus_oran = 2/10
            calisma_turu_temiz = str(calisma_turu).strip().upper()
            
            if calisma_turu_temiz == 'TOPLANTI':
                tur_bonus = max_puan * bonus_oran
            elif calisma_turu_temiz == 'DUYURU':
                tur_bonus = max_puan * bonus_oran * (1/2)
            else:
                tur_bonus = 0
            
            toplam_bayrak = erisim_puan + tur_bonus
            
            puanlar[il] = {
                'erisim_puan': erisim_puan,
                'tur_bonus': tur_bonus,
                'bayrak_sayisi': bayrak_sayisi,
                'nufus': nufus,
                'nufus_bayrak_orani': nufus_bayrak_orani,
                'normalize_oran': normalize_oran,
                'calisma_turu': calisma_turu_temiz,
                'toplam_bayrak': toplam_bayrak
            }
        
        return puanlar
    
    def genel_puanlama_hesapla(self):
        """Tüm aktiviteler için genel puanlamayı hesapla - Yüzdelik Ağırlık Sistemi"""
        print("🧮 Dinamik puanlama hesaplamaları başlıyor...")
        
        # Tüm aktiviteler için puanları hesapla (sadece verisi olanlar)
        aktivite_puanlari = {}
        for aktivite, hesaplama_metodu in self.hesaplama_metodlari.items():
            # Verisi olmayan aktiviteleri pas geç
            if aktivite not in self.veriler:
                print(f"⏭️ {aktivite.title()} aktivitesi pas geçildi (veri yok)")
                continue
                
            try:
                aktivite_puanlari[aktivite] = hesaplama_metodu()
                print(f"✅ {aktivite.title()} aktivitesi hesaplandı")
            except Exception as e:
                print(f"❌ {aktivite.title()} aktivitesi hesaplanamadı: {e}")
                aktivite_puanlari[aktivite] = {}
        
        # Toplam katsayıyı hesapla
        toplam_katsayi = sum(self.aktivite_katsayilari.values())
        print(f"📊 Toplam katsayı: {toplam_katsayi}")
        
        # Her aktivitenin yüzdelik ağırlığını hesapla
        aktivite_agirlikları = {}
        for aktivite, katsayi in self.aktivite_katsayilari.items():
            agirlik = (katsayi / toplam_katsayi) * 100
            aktivite_agirlikları[aktivite] = agirlik
            print(f"🎯 {aktivite.title()}: {katsayi} katsayı = %{agirlik:.2f} ağırlık")
        
        # İl listesi al
        il_listesi = set()
        for puanlar in aktivite_puanlari.values():
            il_listesi.update(puanlar.keys())
        
        genel_sonuclar = {}
        
        for il in il_listesi:
            # Her aktiviteden ağırlıklı puanları hesapla
            toplam_puan = 0
            aktivite_detaylari = {}
            
            for aktivite, puanlar in aktivite_puanlari.items():
                if il in puanlar:
                    # Ham aktivite puanını al
                    ham_aktivite_puan = puanlar[il].get(f'toplam_{aktivite}', 0)
                    
                    # Aktivite katsayısına göre maksimum puanı hesapla
                    aktivite_katsayi = self.aktivite_katsayilari.get(aktivite, 1.0)
                    max_aktivite_puan = aktivite_katsayi * 10
                    
                    # Ham puanı 0-1 arasında normalize et
                    if max_aktivite_puan > 0:
                        normalize_puan = min(ham_aktivite_puan / max_aktivite_puan, 1.0)
                    else:
                        normalize_puan = 0
                    
                    # Yüzdelik ağırlığa göre final puanı hesapla
                    aktivite_agirlik = aktivite_agirlikları.get(aktivite, 0)
                    final_aktivite_puan = normalize_puan * aktivite_agirlik
                    
                    toplam_puan += final_aktivite_puan
                    aktivite_detaylari[f'{aktivite}_ham_puan'] = ham_aktivite_puan
                    aktivite_detaylari[f'{aktivite}_normalize_puan'] = normalize_puan
                    aktivite_detaylari[f'{aktivite}_agirlik'] = aktivite_agirlik
                    aktivite_detaylari[f'{aktivite}_final_puan'] = final_aktivite_puan
                    aktivite_detaylari[f'{aktivite}_detay'] = puanlar[il]
                else:
                    aktivite_agirlik = aktivite_agirlikları.get(aktivite, 0)
                    aktivite_detaylari[f'{aktivite}_ham_puan'] = 0
                    aktivite_detaylari[f'{aktivite}_normalize_puan'] = 0
                    aktivite_detaylari[f'{aktivite}_agirlik'] = aktivite_agirlik
                    aktivite_detaylari[f'{aktivite}_final_puan'] = 0
                    aktivite_detaylari[f'{aktivite}_detay'] = {}
            
            # İl bilgileri
            il_kategori = self.il_kategorileri.get(il, {})
            kategori_katsayi = self.kategori_katsayilar.get(il, {})
            
            genel_sonuclar[il] = {
                'il_adi': il,
                'il_kategorisi': il_kategori.get('kategori', 'Bilinmiyor'),
                'kategori_grup': kategori_katsayi.get('grup', 'Orta İl'),
                'kategori_katsayi': kategori_katsayi.get('katsayi', 1.0),
                'nufus': il_kategori.get('nufus', 0),
                'toplam_puan': toplam_puan,  # Bu artık 100 üzerinden
                'toplam_katsayi': toplam_katsayi,
                **aktivite_detaylari
            }
        
        self.sonuclar = genel_sonuclar
        print("✅ Yüzdelik ağırlık sistemiyle dinamik genel puanlama hesaplandı")
        return genel_sonuclar
    
    def rapor_olustur(self):
        """Dinamik raporları oluştur - Yüzdelik Ağırlık Sistemi"""
        print("📊 Dinamik raporlar oluşturuluyor...")
        
        # Toplam katsayıyı hesapla
        toplam_katsayi = sum(self.aktivite_katsayilari.values())
        
        # Ana rapor verilerini hazırla
        rapor_data = []
        for il, veri in self.sonuclar.items():
            rapor_row = {
                'İL': il,
                'İL_KATEGORİSİ': veri['il_kategorisi'],
                'KATEGORİ_GRUP': veri['kategori_grup'],
                'KATEGORİ_KATSAYI': veri['kategori_katsayi'],
                'NÜFUS': veri.get('nufus', 0),
                'TOPLAM_PUAN': round(veri['toplam_puan'], 2),  # 100 üzerinden
                'TOPLAM_KATSAYI': veri.get('toplam_katsayi', toplam_katsayi)
            }
            
            # Her aktivite için detaylı puanları ekle
            for aktivite in self.hesaplama_metodlari.keys():
                ham_key = f'{aktivite}_ham_puan'
                final_key = f'{aktivite}_final_puan'
                agirlik_key = f'{aktivite}_agirlik'
                
                # Ham puan
                if ham_key in veri:
                    rapor_row[f'{aktivite.upper()}_HAM_PUAN'] = round(veri[ham_key], 1)
                else:
                    rapor_row[f'{aktivite.upper()}_HAM_PUAN'] = 0
                
                # Final puan (ağırlıklı)
                if final_key in veri:
                    rapor_row[f'{aktivite.upper()}_FINAL_PUAN'] = round(veri[final_key], 2)
                else:
                    rapor_row[f'{aktivite.upper()}_FINAL_PUAN'] = 0
                
                # Ağırlık yüzdesi
                if agirlik_key in veri:
                    rapor_row[f'{aktivite.upper()}_AGIRLIK'] = round(veri[agirlik_key], 2)
                else:
                    katsayi = self.aktivite_katsayilari.get(aktivite, 0)
                    agirlik = (katsayi / toplam_katsayi) * 100 if toplam_katsayi > 0 else 0
                    rapor_row[f'{aktivite.upper()}_AGIRLIK'] = round(agirlik, 2)
            
            rapor_data.append(rapor_row)
        
        # DataFrame oluştur ve sırala
        df_rapor = pd.DataFrame(rapor_data)
        df_rapor = df_rapor.sort_values('TOPLAM_PUAN', ascending=False)
        df_rapor['GENEL_SIRALAMA'] = range(1, len(df_rapor) + 1)
        
        # Ana raporu kaydet
        df_rapor.to_csv('output_csv/Dinamik_Genel_Performans_Raporu.csv', 
                       index=False, encoding='utf-8-sig')
        
        # Aktivite katsayıları ve ağırlıkları raporunu oluştur
        katsayi_data = []
        for aktivite, katsayi in self.aktivite_katsayilari.items():
            agirlik = (katsayi / toplam_katsayi) * 100 if toplam_katsayi > 0 else 0
            katsayi_data.append({
                'AKTİVİTE': aktivite.title(),
                'ÖNEM_KATSAYISI': katsayi,
                'YÜZDE_AĞIRLIK': round(agirlik, 2),
                'MAKSIMUM_HAM_PUAN': katsayi * 10,
                'SİSTEMDE_MEVCUT': aktivite in self.veriler
            })
        
        katsayi_df = pd.DataFrame(katsayi_data)
        katsayi_df = katsayi_df.sort_values('ÖNEM_KATSAYISI', ascending=False)
        
        # Toplam bilgilerini ekle
        toplam_row = {
            'AKTİVİTE': 'TOPLAM',
            'ÖNEM_KATSAYISI': toplam_katsayi,
            'YÜZDE_AĞIRLIK': 100.0,
            'MAKSIMUM_HAM_PUAN': toplam_katsayi * 10,
            'SİSTEMDE_MEVCUT': True
        }
        katsayi_df = pd.concat([katsayi_df, pd.DataFrame([toplam_row])], ignore_index=True)
        
        katsayi_df.to_csv('output_csv/Aktivite_Katsayi_Agirlik_Raporu.csv', 
                         index=False, encoding='utf-8-sig')
        
        print("✅ Yüzdelik ağırlık sistemiyle dinamik raporlar oluşturuldu")
        print(f"📊 Toplam {len(self.aktivite_katsayilari)} aktivite, {toplam_katsayi} toplam katsayı")
        return df_rapor
