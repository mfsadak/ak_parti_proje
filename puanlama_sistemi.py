#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AK Parti 81 İl Adil Puanlama Sistemi
İyileştirilmiş metodoloji ile kapsamlı performans değerlendirmesi
"""

import pandas as pd
import warnings
import os

warnings.filterwarnings('ignore')

class AKPartiPuanlamaSistemi:
    # İl kategorileri için nüfus eşikleri
    MEGA_IL_ESIK = 3000000
    BUYUK_IL_ESIK = 1500000
    ORTA_IL_ESIK = 500000
    VARSAYILAN_NUFUS = 500000
    
    # Kategori katsayıları
    KATEGORI_KATSAYILARI = {
        "Mega İl": 1.0,      # En kolay (3M+ nüfus, büyük kaynak, altyapı)
        "Büyük İl": 1.08,    # Kolay (1.5M-3M nüfus)
        "Orta İl": 1.15,     # Orta zorluk (500K-1.5M nüfus)
        "Küçük İl": 1.30     # Zor (500K'dan az nüfus, sınırlı kaynak)
    }
    
    # Puanlama ağırlıkları
    MAX_TOPLAM_PUAN = 100
    UYELIK_MAX_PUAN = 40
    DANISMA_MAX_PUAN = 30
    RAMAZAN_MAX_PUAN = 20
    BAYRAK_MAX_PUAN = 10
    def __init__(self):
        """AK Parti İyileştirilmiş Puanlama Sistemi"""
        self.veriler = {}
        self.il_kategorileri = {}
        self.kategori_katsayilar = {}
        self.sonuclar = {}
        self.nufus_bilgileri = None  # Cache için
        
        # Klasör oluştur
        os.makedirs('output_csv', exist_ok=True)
        
    def veri_yukle(self):
        """Data klasöründen CSV dosyalarını yükle"""
        try:
            print("📂 Veriler yükleniyor...")
            
            # CSV dosyalarını yükle
            self.veriler['uyelik'] = pd.read_csv('data/Üyelik.csv', encoding='utf-8')
            self.veriler['ramazan'] = pd.read_csv('data/Ramazan_Çalışmaları.csv', encoding='utf-8')
            self.veriler['danisma'] = pd.read_csv('data/Danışma_Meclisi.csv', encoding='utf-8')
            self.veriler['bayrak'] = pd.read_csv('data/Bayrak_Çalışması.csv', encoding='utf-8')
            
            # Veri temizleme
            self._veri_temizle()
            
            print("✅ Veriler başarıyla yüklendi")
            return True
            
        except Exception as e:
            print(f"❌ Veri yükleme hatası: {e}")
            return False
    
    def _veri_temizle(self):
        """Veri temizleme ve düzeltme işlemleri"""
        
        # Üyelik verisi temizleme
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
        self.veriler['uyelik']['HEDEFE ULAŞMA ORANI'] = (self.veriler['uyelik']['HEDEFE ULAŞMA ORANI']
                                                        .str.replace('%', '')
                                                        .astype(float))
        
        # Ramazan verisi temizleme
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
    
    def _nufus_verileri_yukle(self):
        """Nüfus verilerini yükle - tek seferlik cache sistemi"""
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
    
    def _danisma_puan_hesapla(self, ortalama, max_puan=15):
        """Danışma meclisi ortalama bazlı puan hesaplama - standart skala"""
        if ortalama >= 0.95:
            return max_puan
        elif ortalama >= 0.90:
            return max_puan * 0.9  # 13.5
        elif ortalama >= 0.80:
            return max_puan * 0.8  # 12
        elif ortalama >= 0.70:
            return max_puan * 0.7  # 10.5
        elif ortalama >= 0.60:
            return max_puan * 0.6  # 9
        elif ortalama >= 0.50:
            return max_puan * 0.5  # 7.5
        elif ortalama >= 0.40:
            return max_puan * 0.4  # 6
        elif ortalama >= 0.30:
            return max_puan * 0.3  # 4.5
        elif ortalama >= 0.20:
            return max_puan * 0.2  # 3
        elif ortalama >= 0.10:
            return max_puan * 0.1  # 1.5
        else:
            return 0
    
    def il_kategorileri_belirle(self):
        """İl büyüklük kategorilerini ve nüfus bazlı katsayıları belirle"""
        
        # Nüfus verilerini yükle
        nufus_dict = self._nufus_verileri_yukle()
        
        # İl kategorileri (nüfus bazlı)
        for _, row in self.veriler['uyelik'].iterrows():
            il = row['İL']
            nufus = nufus_dict.get(il, self.VARSAYILAN_NUFUS)  # Varsayılan nüfus
            
            # Nüfus bazlı kategorilendirme
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
        
        # İl kategorilerine göre performans katsayıları (nüfus bazlı adalet sistemi)
        # Küçük iller için daha yüksek katsayı (zorluklarını telafi etmek için)
        kategori_katsayilari = self.KATEGORI_KATSAYILARI
        
        # Her il için kategori katsayısını ata
        for il in self.veriler['uyelik']['İL']:
            il_kategorisi = self.il_kategorileri.get(il, {}).get('kategori', 'Orta İl')
            
            self.kategori_katsayilar[il] = {
                'grup': il_kategorisi,
                'katsayi': kategori_katsayilari.get(il_kategorisi, 1.15)
            }
        
        print("✅ İl kategorileri ve katsayılar belirlendi")
    
    def uyelik_puani_hesapla(self):
        """İyileştirilmiş Üyelik Puanlaması - 40 Puan"""
        puanlar = {}
        
        for _, row in self.veriler['uyelik'].iterrows():
            il = row['İL']
            hedefe_ulasma = row['HEDEFE ULAŞMA ORANI']
            yk_hedef = row.get('YÖNETİM KURULU YAPMASI GEREKEN ÜYE SAYISI', 0)
            yk_gerceklesen = row.get('YÖNETİM KURULU ÜYELERİ TARAFINDAN REFERANS OLUNAN YENİ ÜYE SAYISI', 0)
            
            # 1. TEMEL BAŞARI PUANI (27 puan) - Geçişken eşikler
            if hedefe_ulasma >= 100:
                temel_puan = 27      # Hedef tuttu ve üstü
            elif hedefe_ulasma >= 90:
                temel_puan = 25      # Hedefe çok yakın
            elif hedefe_ulasma >= 80:
                temel_puan = 23      # Çok iyi
            elif hedefe_ulasma >= 70:
                temel_puan = 21      # İyi
            elif hedefe_ulasma >= 60:
                temel_puan = 19      # Orta üstü
            elif hedefe_ulasma >= 50:
                temel_puan = 17      # Orta
            elif hedefe_ulasma >= 40:
                temel_puan = 15      # Orta altı
            elif hedefe_ulasma >= 30:
                temel_puan = 12      # Zayıf
            elif hedefe_ulasma >= 20:
                temel_puan = 9       # Çok zayıf
            elif hedefe_ulasma >= 15:
                temel_puan = 6       # Düşük
            elif hedefe_ulasma >= 10:
                temel_puan = 3       # Minimal
            else:
                temel_puan = 0       # Yetersiz
            
            # 2. MÜKEMMELLIK ÖDÜLÜ (8 puan) - Daha dengeli hedef üstü
            if hedefe_ulasma >= 200:
                mukemmellik_puan = 8     # Olağanüstü başarı (2x hedef)
            elif hedefe_ulasma >= 150:
                mukemmellik_puan = 6     # Süper başarı (1.5x hedef)
            elif hedefe_ulasma >= 120:
                mukemmellik_puan = 4     # Mükemmel (1.2x hedef)
            elif hedefe_ulasma >= 100:
                mukemmellik_puan = 2     # Hedef tuttu bonusu
            else:
                mukemmellik_puan = 0
            
            # 3. YÖNETİM KURULU PERFORMANSI (5 puan) - Liderlik değerlendirmesi
            if yk_hedef > 0:
                yk_basari_orani = (yk_gerceklesen / yk_hedef) * 100
                
                if yk_basari_orani >= 100:
                    yk_puan = 5
                elif yk_basari_orani >= 80:
                    yk_puan = 4
                elif yk_basari_orani >= 60:
                    yk_puan = 3
                elif yk_basari_orani >= 40:
                    yk_puan = 2
                elif yk_basari_orani >= 20:
                    yk_puan = 1
                else:
                    yk_puan = 0
            else:
                yk_basari_orani = 0
                yk_puan = 0
            
            # TOPLAM ÜYELİK PUANI
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
    
    def danisma_puani_hesapla(self):
        """İyileştirilmiş Danışma Meclisi Puanlaması - 30 Puan (İl + İlçe Ayrımı)"""
        puanlar = {}
        
        for il in self.veriler['uyelik']['İL'].unique():
            il_danisma = self.veriler['danisma'][self.veriler['danisma']['İL'] == il]
            
            if len(il_danisma) == 0:
                puanlar[il] = {'toplam_danisma': 0}
                continue
            
            # İL BAŞKANLIĞI ve İLÇELER'i ayır
            il_baskanligi = il_danisma[il_danisma['İLÇE'] == 'İL']
            ilceler = il_danisma[il_danisma['İLÇE'] != 'İL']
            
            # ===================
            # 1. İL BAŞKANLIĞI PERFORMANSI (15 puan - %50 ağırlık)
            # ===================
            if len(il_baskanligi) > 0:
                il_row = il_baskanligi.iloc[0]
                
                # İl başkanlığı aylık durumları (tüm aylar eşit ağırlık)
                il_haziran = 1 if il_row['HAZİRAN'] == 'YAPILDI' else 0
                il_temmuz = 1 if il_row['TEMMUZ'] == 'YAPILDI' else 0
                il_agustos = 1 if il_row['AĞUSTOS'] == 'YAPILDI' else (0.7 if il_row['AĞUSTOS'] == 'PLANLANDI' else 0)
                
                # İl başkanlığı basit ortalama (eşit ağırlık)
                il_ortalama = (il_haziran + il_temmuz + il_agustos) / 3
                
                # İl başkanlığı puanı (15 puan üzerinden)
                il_puan = self._danisma_puan_hesapla(il_ortalama, 15)
            else:
                il_ortalama = 0
                il_puan = 0
            
            # ===================
            # 2. İLÇE PERFORMANSI (15 puan - %50 ağırlık)
            # ===================
            if len(ilceler) > 0:
                # İlçeler için aylık oranlar
                ilce_haziran_oran = len(ilceler[ilceler['HAZİRAN'] == 'YAPILDI']) / len(ilceler)
                ilce_temmuz_oran = len(ilceler[ilceler['TEMMUZ'] == 'YAPILDI']) / len(ilceler)
                ilce_agustos_yapilan = len(ilceler[ilceler['AĞUSTOS'] == 'YAPILDI'])
                ilce_agustos_planlanan = len(ilceler[ilceler['AĞUSTOS'] == 'PLANLANDI'])
                ilce_agustos_oran = (ilce_agustos_yapilan + ilce_agustos_planlanan * 0.7) / len(ilceler)
                
                # İlçeler basit ortalama (eşit ağırlık)
                ilce_ortalama = (ilce_haziran_oran + ilce_temmuz_oran + ilce_agustos_oran) / 3
                
                # İlçeler puanı (15 puan üzerinden)
                ilce_puan = self._danisma_puan_hesapla(ilce_ortalama, 15)
            else:
                ilce_ortalama = 0
                ilce_puan = 0
            
            # ===================
            # 3. TOPLAM PUAN VE BONUS
            # ===================
            # İl başkanlığı puanı sabit (kategori katsayısı yok)
            il_final_puan = il_puan
            
            # İlçeler için kategori katsayısı bonusu
            kategori_katsayi = self.kategori_katsayilar.get(il, {}).get('katsayi', 1.0)
            if kategori_katsayi > 1.0 and ilce_ortalama >= 0.5 and len(ilceler) > 0:
                ilce_bonus = min(4, (kategori_katsayi - 1.0) * 16)
                ilce_final_puan = min(15, ilce_puan + ilce_bonus)
            else:
                ilce_bonus = 0
                ilce_final_puan = ilce_puan
            
            # Toplam puan
            final_puan = il_final_puan + ilce_final_puan
            
            puanlar[il] = {
                'il_ortalama': il_ortalama,
                'ilce_ortalama': ilce_ortalama,
                'genel_ortalama': (il_ortalama + ilce_ortalama) / 2,
                'il_puan': il_puan,
                'ilce_puan': ilce_puan,
                'il_final_puan': il_final_puan,
                'ilce_final_puan': ilce_final_puan,
                'ilce_bonus': ilce_bonus,
                'toplam_danisma': final_puan,
                
                # Detay bilgiler
                'il_sayisi': len(il_baskanligi),
                'ilce_sayisi': len(ilceler),
                'toplam_birim': len(il_danisma)
            }
        
        return puanlar
    
    def ramazan_puani_hesapla(self):
        """Nüfus Oranı Bazlı Ramazan Puanlaması - 20 Puan (Nüfus Erişim Oranı)"""
        puanlar = {}
        
        # Nüfus bilgilerini yükle
        nufus_bilgileri = self._nufus_verileri_yukle()
        
        # Tüm iller için nüfus erişim oranlarını hesapla (kategori katsayısı YOK - nüfus oranı zaten adil)
        nufus_erisim_oranlari = []
        
        for _, row in self.veriler['ramazan'].iterrows():
            if row['İL'] == 'TOPLAM':
                continue
                
            il = row['İL']
            toplam_kisi = row['TOPLAM ULAŞILAN KİŞİ']
            nufus = nufus_bilgileri.get(il, self.VARSAYILAN_NUFUS)  # Varsayılan nüfus
            
            # Nüfus erişim oranı hesapla (%) - Kategori katsayısı uygulanmıyor
            nufus_erisim_orani = (toplam_kisi / nufus) * 100 if nufus > 0 else 0
            nufus_erisim_oranlari.append(nufus_erisim_orani)
        
        # Min-Max normalizasyon için değerleri bul
        max_nufus_orani = max(nufus_erisim_oranlari) if nufus_erisim_oranlari else 1
        min_nufus_orani = min(nufus_erisim_oranlari) if nufus_erisim_oranlari else 0
        
        for _, row in self.veriler['ramazan'].iterrows():
            if row['İL'] == 'TOPLAM':
                continue
                
            il = row['İL']
            toplam_kisi = row['TOPLAM ULAŞILAN KİŞİ']
            nufus = nufus_bilgileri.get(il, 500000)
            
            # Nüfus erişim oranı hesapla (kategori katsayısı YOK)
            nufus_erisim_orani = (toplam_kisi / nufus) * 100 if nufus > 0 else 0
            
            # 1. NÜFUS ERİŞİM PUANI (15 puan) - Sadece Nüfus Oranı Bazlı
            if max_nufus_orani > min_nufus_orani:
                normalize_oran = (nufus_erisim_orani - min_nufus_orani) / (max_nufus_orani - min_nufus_orani)
            else:
                normalize_oran = 1.0
            
            erişim_puan = normalize_oran * 15
            
            # 2. AKTİVİTE ÇEŞİTLİLİĞİ (5 puan) - Daha dengeli
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
            
            # Aktivite puanlaması (daha katı)
            if aktivite_sayisi >= 8:
                aktivite_puan = 5
            elif aktivite_sayisi >= 6:
                aktivite_puan = 4
            elif aktivite_sayisi >= 4:
                aktivite_puan = 3
            elif aktivite_sayisi >= 2:
                aktivite_puan = 2
            elif aktivite_sayisi >= 1:
                aktivite_puan = 1
            else:
                aktivite_puan = 0
            
            toplam_ramazan = erişim_puan + aktivite_puan
            
            puanlar[il] = {
                'erişim_puan': erişim_puan,
                'aktivite_puan': aktivite_puan,
                'aktivite_sayisi': aktivite_sayisi,
                'toplam_ulaşilan': toplam_kisi,
                'nufus': nufus,
                'nufus_erisim_orani': nufus_erisim_orani,
                'normalize_oran': normalize_oran,
                'toplam_ramazan': toplam_ramazan
            }
        
        return puanlar
    
    def bayrak_puani_hesapla(self):
        """Nüfus Bazlı Bayrak Puanlaması - 10 Puan (Nüfus Erişim Oranı)"""
        puanlar = {}
        
        # Nüfus bilgilerini yükle
        nufus_bilgileri = self._nufus_verileri_yukle()
        
        # Tüm iller için nüfus bazlı bayrak oranlarını hesapla
        nufus_bayrak_oranlari = []
        
        for _, row in self.veriler['bayrak'].iterrows():
            il = row['İL']
            bayrak_sayisi = row['BAYRAK ADEDİ']
            nufus = nufus_bilgileri.get(il, self.VARSAYILAN_NUFUS)  # Varsayılan nüfus
            
            # Nüfus başına bayrak oranı (binde kaç)
            nufus_bayrak_orani = (bayrak_sayisi / nufus) * 1000 if nufus > 0 else 0
            nufus_bayrak_oranlari.append(nufus_bayrak_orani)
        
        # Min-Max normalizasyon için değerleri bul
        max_oran = max(nufus_bayrak_oranlari) if nufus_bayrak_oranlari else 1
        min_oran = min(nufus_bayrak_oranlari) if nufus_bayrak_oranlari else 0
        
        for _, row in self.veriler['bayrak'].iterrows():
            il = row['İL']
            bayrak_sayisi = row['BAYRAK ADEDİ']
            calisma_turu = row['YAPILAN ÇALIŞMA']
            nufus = nufus_bilgileri.get(il, 500000)
            
            # Nüfus başına bayrak oranı hesapla
            nufus_bayrak_orani = (bayrak_sayisi / nufus) * 1000 if nufus > 0 else 0
            
            # 1. NÜFUS ERİŞİM PUANI (8 puan) - Nüfus Bazlı Normalize
            if max_oran > min_oran:
                normalize_oran = (nufus_bayrak_orani - min_oran) / (max_oran - min_oran)
            else:
                normalize_oran = 1.0
            
            erisim_puan = normalize_oran * 8
            
            # 2. ÇALIŞMA TÜRÜ BONUSU (2 puan) - Kalite Odaklı
            # Çalışma türünü temizle (boşlukları kaldır)
            calisma_turu_temiz = str(calisma_turu).strip().upper()
            
            if calisma_turu_temiz == 'TOPLANTI':
                tur_bonus = 2      # Aktif katılım, etkileşim
            elif calisma_turu_temiz == 'DUYURU':
                tur_bonus = 1      # Pasif bilgilendirme
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
        """Genel puanlamayı hesapla ve nüfus bazlı adaleti uygula"""
        print("🧮 Puanlama hesaplamaları başlıyor...")
        
        # Alt puanları hesapla
        uyelik_puanlari = self.uyelik_puani_hesapla()
        danisma_puanlari = self.danisma_puani_hesapla()
        ramazan_puanlari = self.ramazan_puani_hesapla()
        bayrak_puanlari = self.bayrak_puani_hesapla()
        
        genel_sonuclar = {}
        
        for il in self.veriler['uyelik']['İL'].unique():
            # Alt puanları al
            uyelik = uyelik_puanlari.get(il, {})
            danisma = danisma_puanlari.get(il, {})
            ramazan = ramazan_puanlari.get(il, {})
            bayrak = bayrak_puanlari.get(il, {})
            
            # Ham puanlar
            uyelik_puan = uyelik.get('toplam_uyelik', 0)
            danisma_puan = danisma.get('toplam_danisma', 0)
            ramazan_puan = ramazan.get('toplam_ramazan', 0)
            bayrak_puan = bayrak.get('toplam_bayrak', 0)
            
            # Ham toplam = Final puan (genel toplamda katsayı uygulanmıyor)
            ham_toplam = uyelik_puan + danisma_puan + ramazan_puan + bayrak_puan
            final_puan = min(self.MAX_TOPLAM_PUAN, ham_toplam)  # Maksimum puan sınırı
            
            # İl kategorisi bilgisi (sadece raporlama için)
            kategori_katsayi = self.kategori_katsayilar.get(il, {}).get('katsayi', 1.0)
            
            # İl bilgileri
            il_bilgi = self.veriler['uyelik'][self.veriler['uyelik']['İL'] == il].iloc[0]
            
            genel_sonuclar[il] = {
                'il_adi': il,
                'il_kategorisi': self.il_kategorileri.get(il, {}).get('kategori', 'Bilinmiyor'),
                'kategori_grup': self.kategori_katsayilar.get(il, {}).get('grup', 'Orta İl'),
                'kategori_katsayi': kategori_katsayi,
                'nufus': self.il_kategorileri.get(il, {}).get('nufus', 0),
                'mevcut_uye': il_bilgi['MEVCUT ÜYE'],
                
                # Ham puanlar
                'uyelik_puan': uyelik_puan,
                'danisma_puan': danisma_puan,
                'ramazan_puan': ramazan_puan,
                'bayrak_puan': bayrak_puan,
                'ham_toplam': ham_toplam,
                
                # Final
                'final_puan': final_puan,
                
                # Detaylar
                'uyelik_detay': uyelik,
                'danisma_detay': danisma,
                'ramazan_detay': ramazan,
                'bayrak_detay': bayrak
            }
        
        self.sonuclar = genel_sonuclar
        print("✅ Genel puanlama hesaplandı")
        return genel_sonuclar
    
    def rapor_olustur(self):
        """Aktivite bazlı detaylı CSV raporları oluştur"""
        print("📊 Aktivite bazlı raporlar oluşturuluyor...")
        
        # Ana rapor verilerini hazırla
        rapor_data = []
        for il, veri in self.sonuclar.items():
            rapor_data.append({
                'İL': il,
                'İL_KATEGORİSİ': veri['il_kategorisi'],
                'KATEGORİ_GRUP': veri['kategori_grup'],
                'KATEGORİ_KATSAYI': veri['kategori_katsayi'],
                'NÜFUS': veri.get('nufus', 0),
                'MEVCUT_ÜYE': veri['mevcut_uye'],
                
                # Ana puanlar
                'ÜYELİK_PUANI': round(veri['uyelik_puan'], 1),
                'DANIŞMA_PUANI': round(veri['danisma_puan'], 1),
                'RAMAZAN_PUANI': round(veri['ramazan_puan'], 1),
                'BAYRAK_PUANI': round(veri['bayrak_puan'], 1),
                
                'HAM_TOPLAM': round(veri['ham_toplam'], 1),
                'FİNAL_PUAN': round(veri['final_puan'], 1),
                
                # Detayları da sakla
                'uyelik_detay': veri['uyelik_detay'],
                'danisma_detay': veri['danisma_detay'],
                'ramazan_detay': veri['ramazan_detay'],
                'bayrak_detay': veri['bayrak_detay']
            })
        
        # DataFrame oluştur ve sırala
        df_rapor = pd.DataFrame(rapor_data)
        df_rapor = df_rapor.sort_values('FİNAL_PUAN', ascending=False)
        df_rapor['GENEL_SIRALAMA'] = range(1, len(df_rapor) + 1)
        
        # Ana raporu kaydet
        ana_rapor_data = []
        for _, row in df_rapor.iterrows():
            ana_rapor_data.append({
                'İL': row['İL'],
                'İL_KATEGORİSİ': row['İL_KATEGORİSİ'],
                'NÜFUS': row['NÜFUS'],
                'MEVCUT_ÜYE': row['MEVCUT_ÜYE'],
                'ÜYELİK_PUANI': row['ÜYELİK_PUANI'],
                'DANIŞMA_PUANI': row['DANIŞMA_PUANI'],
                'RAMAZAN_PUANI': row['RAMAZAN_PUANI'],
                'BAYRAK_PUANI': row['BAYRAK_PUANI'],
                'FİNAL_PUAN': row['FİNAL_PUAN'],
                'GENEL_SIRALAMA': row['GENEL_SIRALAMA']
            })
        
        ana_df = pd.DataFrame(ana_rapor_data)
        ana_df.to_csv('output_csv/AK_Parti_Genel_Performans_Raporu.csv', 
                     index=False, encoding='utf-8-sig')
        
        # ÜYELİK AKTİVİTESİ RAPORU
        self._uyelik_raporu_olustur(df_rapor)
        
        # DANIŞMA MECLİSİ AKTİVİTESİ RAPORU
        self._danisma_raporu_olustur(df_rapor)
        
        # RAMAZAN AKTİVİTESİ RAPORU
        self._ramazan_raporu_olustur(df_rapor)
        
        # BAYRAK AKTİVİTESİ RAPORU
        self._bayrak_raporu_olustur(df_rapor)
        
        # Kapsamlı özet istatistikler oluştur
        self._ozet_istatistikler_olustur(df_rapor)
        
        print("✅ Aktivite bazlı CSV raporları oluşturuldu")
        return df_rapor
    
    def _uyelik_raporu_olustur(self, df_rapor):
        """Üyelik aktivitesi detaylı raporu"""
        uyelik_data = []
        
        for _, row in df_rapor.iterrows():
            detay = row['uyelik_detay']
            uyelik_data.append({
                'İL': row['İL'],
                'İL_KATEGORİSİ': row['İL_KATEGORİSİ'],
                'NÜFUS': row['NÜFUS'],
                'MEVCUT_ÜYE': row['MEVCUT_ÜYE'],
                'HEDEFE_ULAŞMA_ORANI': round(detay.get('hedefe_ulasma_orani', 0), 1),
                'TEMEL_PUAN': detay.get('temel_puan', 0),
                'MÜKEMMELLIK_PUAN': detay.get('mukemmellik_puan', 0),
                'YK_PUAN': detay.get('yk_puan', 0),
                'YK_BAŞARI_ORANI': round(detay.get('yk_basari_orani', 0), 1),
                'TOPLAM_ÜYELİK_PUANI': row['ÜYELİK_PUANI'],
                'GENEL_SIRALAMA': row['GENEL_SIRALAMA']
            })
        
        uyelik_df = pd.DataFrame(uyelik_data)
        uyelik_df = uyelik_df.sort_values('TOPLAM_ÜYELİK_PUANI', ascending=False)
        uyelik_df['ÜYELİK_SIRASI'] = range(1, len(uyelik_df) + 1)
        
        uyelik_df.to_csv('output_csv/Uyelik_Aktivitesi_Detay_Raporu.csv', 
                        index=False, encoding='utf-8-sig')
    
    def _danisma_raporu_olustur(self, df_rapor):
        """Danışma Meclisi aktivitesi detaylı raporu"""
        danisma_data = []
        
        for _, row in df_rapor.iterrows():
            detay = row['danisma_detay']
            danisma_data.append({
                'İL': row['İL'],
                'İL_KATEGORİSİ': row['İL_KATEGORİSİ'],
                'NÜFUS': row['NÜFUS'],
                'İL_ORTALAMA': round(detay.get('il_ortalama', 0), 3),
                'İLÇE_ORTALAMA': round(detay.get('ilce_ortalama', 0), 3),
                'GENEL_ORTALAMA': round(detay.get('genel_ortalama', 0), 3),
                'İL_PUAN': round(detay.get('il_puan', 0), 1),
                'İLÇE_PUAN': round(detay.get('ilce_puan', 0), 1),
                'İL_FINAL_PUAN': round(detay.get('il_final_puan', 0), 1),
                'İLÇE_FINAL_PUAN': round(detay.get('ilce_final_puan', 0), 1),
                'İLÇE_BONUS': round(detay.get('ilce_bonus', 0), 1),
                'İLÇE_SAYISI': detay.get('ilce_sayisi', 0),
                'TOPLAM_BİRİM': detay.get('toplam_birim', 0),
                'TOPLAM_DANIŞMA_PUANI': row['DANIŞMA_PUANI'],
                'GENEL_SIRALAMA': row['GENEL_SIRALAMA']
            })
        
        danisma_df = pd.DataFrame(danisma_data)
        danisma_df = danisma_df.sort_values('TOPLAM_DANIŞMA_PUANI', ascending=False)
        danisma_df['DANIŞMA_SIRASI'] = range(1, len(danisma_df) + 1)
        
        danisma_df.to_csv('output_csv/Danisma_Meclisi_Aktivitesi_Detay_Raporu.csv', 
                         index=False, encoding='utf-8-sig')
    
    def _ramazan_raporu_olustur(self, df_rapor):
        """Ramazan aktivitesi detaylı raporu"""
        ramazan_data = []
        
        for _, row in df_rapor.iterrows():
            detay = row['ramazan_detay']
            ramazan_data.append({
                'İL': row['İL'],
                'İL_KATEGORİSİ': row['İL_KATEGORİSİ'],
                'NÜFUS': row['NÜFUS'],
                'TOPLAM_ULAŞILAN_KİŞİ': detay.get('toplam_ulaşilan', 0),
                'NÜFUS_ERİŞİM_ORANI': round(detay.get('nufus_erisim_orani', 0), 2),
                'NORMALIZE_ORAN': round(detay.get('normalize_oran', 0), 3),
                'ERİŞİM_PUAN': round(detay.get('erişim_puan', 0), 1),
                'AKTİVİTE_SAYISI': detay.get('aktivite_sayisi', 0),
                'AKTİVİTE_PUAN': round(detay.get('aktivite_puan', 0), 1),
                'TOPLAM_RAMAZAN_PUANI': row['RAMAZAN_PUANI'],
                'GENEL_SIRALAMA': row['GENEL_SIRALAMA']
            })
        
        ramazan_df = pd.DataFrame(ramazan_data)
        ramazan_df = ramazan_df.sort_values('TOPLAM_RAMAZAN_PUANI', ascending=False)
        ramazan_df['RAMAZAN_SIRASI'] = range(1, len(ramazan_df) + 1)
        
        ramazan_df.to_csv('output_csv/Ramazan_Aktivitesi_Detay_Raporu.csv', 
                         index=False, encoding='utf-8-sig')
    
    def _bayrak_raporu_olustur(self, df_rapor):
        """Bayrak aktivitesi detaylı raporu"""
        bayrak_data = []
        
        for _, row in df_rapor.iterrows():
            detay = row['bayrak_detay']
            bayrak_data.append({
                'İL': row['İL'],
                'İL_KATEGORİSİ': row['İL_KATEGORİSİ'],
                'NÜFUS': row['NÜFUS'],
                'BAYRAK_SAYISI': detay.get('bayrak_sayisi', 0),
                'NÜFUS_BAYRAK_ORANI': round(detay.get('nufus_bayrak_orani', 0), 3),
                'NORMALIZE_ORAN': round(detay.get('normalize_oran', 0), 3),
                'ERİŞİM_PUAN': round(detay.get('erisim_puan', 0), 1),
                'ÇALIŞMA_TÜRÜ': detay.get('calisma_turu', ''),
                'TÜR_BONUS': round(detay.get('tur_bonus', 0), 1),
                'TOPLAM_BAYRAK_PUANI': row['BAYRAK_PUANI'],
                'GENEL_SIRALAMA': row['GENEL_SIRALAMA']
            })
        
        bayrak_df = pd.DataFrame(bayrak_data)
        bayrak_df = bayrak_df.sort_values('TOPLAM_BAYRAK_PUANI', ascending=False)
        bayrak_df['BAYRAK_SIRASI'] = range(1, len(bayrak_df) + 1)
        
        bayrak_df.to_csv('output_csv/Bayrak_Aktivitesi_Detay_Raporu.csv', 
                        index=False, encoding='utf-8-sig')
    
    def _ozet_istatistikler_olustur(self, df_rapor):
        """Kapsamlı özet istatistikler oluştur - Genel ve aktivite bazlı"""
        
        # GENEL PERFORMANS İSTATİSTİKLERİ
        genel_stats = {
            'Metrik': 'Genel Performans',
            'Toplam_İl_Sayısı': len(df_rapor),
            'En_Yüksek_Puan': round(df_rapor['FİNAL_PUAN'].max(), 1),
            'En_Düşük_Puan': round(df_rapor['FİNAL_PUAN'].min(), 1),
            'Ortalama_Puan': round(df_rapor['FİNAL_PUAN'].mean(), 1),
            'Medyan_Puan': round(df_rapor['FİNAL_PUAN'].median(), 1),
            'Standart_Sapma': round(df_rapor['FİNAL_PUAN'].std(), 1),
            'En_Başarılı_İl': df_rapor.loc[df_rapor['FİNAL_PUAN'].idxmax(), 'İL'],
            'En_Düşük_İl': df_rapor.loc[df_rapor['FİNAL_PUAN'].idxmin(), 'İL']
        }
        
        # ÜYELİK AKTİVİTESİ İSTATİSTİKLERİ
        uyelik_stats = {
            'Metrik': 'Üyelik Aktivitesi',
            'Toplam_İl_Sayısı': len(df_rapor),
            'En_Yüksek_Puan': round(df_rapor['ÜYELİK_PUANI'].max(), 1),
            'En_Düşük_Puan': round(df_rapor['ÜYELİK_PUANI'].min(), 1),
            'Ortalama_Puan': round(df_rapor['ÜYELİK_PUANI'].mean(), 1),
            'Medyan_Puan': round(df_rapor['ÜYELİK_PUANI'].median(), 1),
            'Standart_Sapma': round(df_rapor['ÜYELİK_PUANI'].std(), 1),
            'En_Başarılı_İl': df_rapor.loc[df_rapor['ÜYELİK_PUANI'].idxmax(), 'İL'],
            'En_Düşük_İl': df_rapor.loc[df_rapor['ÜYELİK_PUANI'].idxmin(), 'İL']
        }
        
        # DANIŞMA MECLİSİ AKTİVİTESİ İSTATİSTİKLERİ
        danisma_stats = {
            'Metrik': 'Danışma Meclisi Aktivitesi',
            'Toplam_İl_Sayısı': len(df_rapor),
            'En_Yüksek_Puan': round(df_rapor['DANIŞMA_PUANI'].max(), 1),
            'En_Düşük_Puan': round(df_rapor['DANIŞMA_PUANI'].min(), 1),
            'Ortalama_Puan': round(df_rapor['DANIŞMA_PUANI'].mean(), 1),
            'Medyan_Puan': round(df_rapor['DANIŞMA_PUANI'].median(), 1),
            'Standart_Sapma': round(df_rapor['DANIŞMA_PUANI'].std(), 1),
            'En_Başarılı_İl': df_rapor.loc[df_rapor['DANIŞMA_PUANI'].idxmax(), 'İL'],
            'En_Düşük_İl': df_rapor.loc[df_rapor['DANIŞMA_PUANI'].idxmin(), 'İL']
        }
        
        # RAMAZAN AKTİVİTESİ İSTATİSTİKLERİ
        ramazan_stats = {
            'Metrik': 'Ramazan Aktivitesi',
            'Toplam_İl_Sayısı': len(df_rapor),
            'En_Yüksek_Puan': round(df_rapor['RAMAZAN_PUANI'].max(), 1),
            'En_Düşük_Puan': round(df_rapor['RAMAZAN_PUANI'].min(), 1),
            'Ortalama_Puan': round(df_rapor['RAMAZAN_PUANI'].mean(), 1),
            'Medyan_Puan': round(df_rapor['RAMAZAN_PUANI'].median(), 1),
            'Standart_Sapma': round(df_rapor['RAMAZAN_PUANI'].std(), 1),
            'En_Başarılı_İl': df_rapor.loc[df_rapor['RAMAZAN_PUANI'].idxmax(), 'İL'],
            'En_Düşük_İl': df_rapor.loc[df_rapor['RAMAZAN_PUANI'].idxmin(), 'İL']
        }
        
        # BAYRAK AKTİVİTESİ İSTATİSTİKLERİ
        bayrak_stats = {
            'Metrik': 'Bayrak Aktivitesi',
            'Toplam_İl_Sayısı': len(df_rapor),
            'En_Yüksek_Puan': round(df_rapor['BAYRAK_PUANI'].max(), 1),
            'En_Düşük_Puan': round(df_rapor['BAYRAK_PUANI'].min(), 1),
            'Ortalama_Puan': round(df_rapor['BAYRAK_PUANI'].mean(), 1),
            'Medyan_Puan': round(df_rapor['BAYRAK_PUANI'].median(), 1),
            'Standart_Sapma': round(df_rapor['BAYRAK_PUANI'].std(), 1),
            'En_Başarılı_İl': df_rapor.loc[df_rapor['BAYRAK_PUANI'].idxmax(), 'İL'],
            'En_Düşük_İl': df_rapor.loc[df_rapor['BAYRAK_PUANI'].idxmin(), 'İL']
        }
        
        # Tüm istatistikleri birleştir
        tum_istatistikler = [genel_stats, uyelik_stats, danisma_stats, ramazan_stats, bayrak_stats]
        
        # DataFrame oluştur ve kaydet
        ozet_df = pd.DataFrame(tum_istatistikler)
        ozet_df.to_csv('output_csv/Kapsamli_Ozet_Istatistikler.csv', index=False, encoding='utf-8-sig')
        
        # İL KATEGORİLERİNE GÖRE İSTATİSTİKLER
        self._kategori_bazli_istatistikler(df_rapor)
    
    def _kategori_bazli_istatistikler(self, df_rapor):
        """İl kategorilerine göre performans istatistikleri"""
        kategori_stats = []
        
        for kategori in df_rapor['İL_KATEGORİSİ'].unique():
            kategori_df = df_rapor[df_rapor['İL_KATEGORİSİ'] == kategori]
            
            kategori_stat = {
                'İL_KATEGORİSİ': kategori,
                'İl_Sayısı': len(kategori_df),
                'Ortalama_Genel_Puan': round(kategori_df['FİNAL_PUAN'].mean(), 1),
                'Ortalama_Üyelik_Puanı': round(kategori_df['ÜYELİK_PUANI'].mean(), 1),
                'Ortalama_Danışma_Puanı': round(kategori_df['DANIŞMA_PUANI'].mean(), 1),
                'Ortalama_Ramazan_Puanı': round(kategori_df['RAMAZAN_PUANI'].mean(), 1),
                'Ortalama_Bayrak_Puanı': round(kategori_df['BAYRAK_PUANI'].mean(), 1),
                'En_Yüksek_Puan': round(kategori_df['FİNAL_PUAN'].max(), 1),
                'En_Düşük_Puan': round(kategori_df['FİNAL_PUAN'].min(), 1),
                'En_Başarılı_İl': kategori_df.loc[kategori_df['FİNAL_PUAN'].idxmax(), 'İL']
            }
            kategori_stats.append(kategori_stat)
        
        # Kategori istatistiklerini kaydet
        kategori_df = pd.DataFrame(kategori_stats)
        kategori_df = kategori_df.sort_values('Ortalama_Genel_Puan', ascending=False)
        kategori_df.to_csv('output_csv/Kategori_Bazli_Istatistikler.csv', index=False, encoding='utf-8-sig')
    
    def tam_analiz_calistir(self):
        """Tüm analizi çalıştır"""
        print("🚀 AK Parti Nüfus Bazlı İyileştirilmiş Puanlama Sistemi Başlatılıyor...")
        print("=" * 60)
        
        # Adımları sırayla çalıştır
        if not self.veri_yukle():
            return False
        
        self.il_kategorileri_belirle()
        self.genel_puanlama_hesapla()
        self.rapor_olustur()
        
        print("\n🎉 ANALİZ TAMAMLANDI!")
        print("=" * 60)
        print("📋 OLUŞTURULAN DOSYALAR:")
        print("📊 ANA RAPORLAR:")
        print("  - output_csv/AK_Parti_Genel_Performans_Raporu.csv (Ana Özet)")
        print("📈 AKTİVİTE DETAY RAPORLARI:")
        print("  - output_csv/Uyelik_Aktivitesi_Detay_Raporu.csv")
        print("  - output_csv/Danisma_Meclisi_Aktivitesi_Detay_Raporu.csv")
        print("  - output_csv/Ramazan_Aktivitesi_Detay_Raporu.csv")
        print("  - output_csv/Bayrak_Aktivitesi_Detay_Raporu.csv")
        print("📊 İSTATİSTİK RAPORLARI:")
        print("  - output_csv/Kapsamli_Ozet_Istatistikler.csv")
        print("  - output_csv/Kategori_Bazli_Istatistikler.csv")
        print("\n💡 Kapsamlı aktivite ve istatistik raporları oluşturuldu!")

# Ana çalıştırma
if __name__ == "__main__":
    puanlama = AKPartiPuanlamaSistemi()
    puanlama.tam_analiz_calistir()
