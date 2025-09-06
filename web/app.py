#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AK Parti Dinamik Puanlama Sistemi - Web Backend
Flask API ile Web Uyumlu Backend
"""

import os
import json
import pandas as pd
from flask import Flask, request, jsonify, render_template, send_file, session
from werkzeug.utils import secure_filename
from datetime import datetime
import tempfile
import shutil
from pathlib import Path
import sys

# Aynı klasörden sistem.py'yi import et
from sistem import DinamikPuanlamaSistemi

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-secret-key-here')

# Konfigürasyon
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Global değişkenler
current_session = {}

def allowed_file(filename):
    """Dosya uzantısı kontrolü"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_session_id():
    """Session ID al veya oluştur"""
    if 'session_id' not in session:
        session['session_id'] = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    return session['session_id']

def get_session_folder():
    """Session klasörü oluştur"""
    session_id = get_session_id()
    session_folder = os.path.join('uploads', session_id)
    os.makedirs(session_folder, exist_ok=True)
    return session_folder

@app.route('/')
def index():
    """Ana sayfa"""
    return render_template('index.html')

@app.route('/api/status')
def status():
    """API durumu"""
    return jsonify({
        'status': 'active',
        'version': '1.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """CSV dosyalarını yükle"""
    try:
        session_folder = get_session_folder()
        session_id = get_session_id()
        
        uploaded_files = []
        
        # Tüm dosyaları kontrol et
        for file_key in request.files:
            file = request.files[file_key]
            
            if file and file.filename and allowed_file(file.filename):
                # Güvenli dosya adı
                filename = secure_filename(file.filename)
                filepath = os.path.join(session_folder, filename)
                
                # Dosyayı kaydet
                file.save(filepath)
                
                # Dosya bilgilerini kaydet
                file_info = {
                    'original_name': file.filename,
                    'saved_name': filename,
                    'path': filepath,
                    'size': os.path.getsize(filepath)
                }
                uploaded_files.append(file_info)
        
        # Session'a kaydet
        if session_id not in current_session:
            current_session[session_id] = {}
        current_session[session_id]['uploaded_files'] = uploaded_files
        
        return jsonify({
            'success': True,
            'message': f'{len(uploaded_files)} dosya başarıyla yüklendi',
            'files': uploaded_files
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Dosya yükleme hatası: {str(e)}'
        }), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_data():
    """Veri analizi başlat"""
    try:
        session_id = get_session_id()
        
        if session_id not in current_session:
            return jsonify({
                'success': False,
                'message': 'Session bulunamadı. Lütfen dosyaları tekrar yükleyin.'
            }), 400
        
        # OpenAI API key al
        data = request.get_json()
        openai_api_key = data.get('openai_api_key', '')
        
        # Session folder'ı data klasörü olarak kullan
        session_folder = get_session_folder()
        
        # Sistem oluştur
        sistem = WebDinamikPuanlamaSistemi(
            openai_api_key=openai_api_key,
            data_folder=session_folder
        )
        
        # Analiz çalıştır
        result = sistem.web_analiz_calistir()
        
        # Sonuçları session'a kaydet
        current_session[session_id]['analysis_result'] = result
        
        return jsonify({
            'success': True,
            'message': 'Analiz başarıyla tamamlandı',
            'result': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Analiz hatası: {str(e)}'
        }), 500

@app.route('/api/new-activity', methods=['POST'])
def handle_new_activity():
    """Yeni aktivite işleme"""
    try:
        data = request.get_json()
        activity_name = data.get('activity_name')
        coefficient = data.get('coefficient')
        
        session_id = get_session_id()
        
        if session_id not in current_session:
            return jsonify({
                'success': False,
                'message': 'Session bulunamadı'
            }), 400
        
        # Katsayıyı kaydet
        if 'new_activities' not in current_session[session_id]:
            current_session[session_id]['new_activities'] = {}
        
        current_session[session_id]['new_activities'][activity_name] = {
            'coefficient': coefficient,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'message': f'{activity_name} aktivitesi {coefficient} katsayı ile kaydedildi'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Aktivite kaydetme hatası: {str(e)}'
        }), 500

@app.route('/api/download/<report_type>')
def download_report(report_type):
    """Rapor indirme"""
    try:
        session_id = get_session_id()
        session_folder = get_session_folder()
        
        # Rapor dosyası yolları
        report_files = {
            'general': 'Dinamik_Genel_Performans_Raporu.csv',
            'coefficients': 'Aktivite_Katsayi_Agirlik_Raporu.csv'
        }
        
        if report_type not in report_files:
            return jsonify({
                'success': False,
                'message': 'Geçersiz rapor türü'
            }), 400
        
        # Rapor dosyası yolu
        report_path = os.path.join(session_folder, 'output_csv', report_files[report_type])
        
        if not os.path.exists(report_path):
            return jsonify({
                'success': False,
                'message': 'Rapor dosyası bulunamadı. Önce analiz çalıştırın.'
            }), 404
        
        return send_file(
            report_path,
            as_attachment=True,
            download_name=report_files[report_type]
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Rapor indirme hatası: {str(e)}'
        }), 500

@app.route('/api/session-info')
def session_info():
    """Session bilgileri"""
    try:
        session_id = get_session_id()
        
        info = {
            'session_id': session_id,
            'has_data': session_id in current_session,
            'uploaded_files': [],
            'new_activities': {},
            'analysis_completed': False
        }
        
        if session_id in current_session:
            session_data = current_session[session_id]
            info['uploaded_files'] = session_data.get('uploaded_files', [])
            info['new_activities'] = session_data.get('new_activities', {})
            info['analysis_completed'] = 'analysis_result' in session_data
        
        return jsonify(info)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Session bilgisi alınamadı: {str(e)}'
        }), 500

class WebDinamikPuanlamaSistemi(DinamikPuanlamaSistemi):
    """Web uyumlu dinamik puanlama sistemi"""
    
    def __init__(self, openai_api_key: str = None, data_folder: str = None):
        # Parent class'ı initialize et
        super().__init__(openai_api_key)
        
        # Data klasörünü güncelle
        if data_folder:
            self.data_folder = data_folder
        else:
            self.data_folder = 'uploads'
    
    def web_dinamik_veri_yukle(self):
        """Web uyumlu veri yükleme"""
        try:
            print("📂 Web veri yükleme başlıyor...")
            
            # Data klasöründeki tüm CSV dosyalarını bul
            data_path = Path(self.data_folder)
            if not data_path.exists():
                return False
            
            csv_files = list(data_path.glob('*.csv'))
            
            # Bilinen dosyalar
            known_mappings = {
                'üyelik': ['uyelik', 'üyelik', 'membership'],
                'danışma_meclisi': ['danisma', 'danışma', 'danisma_meclisi', 'council'],
                'ramazan_çalışmaları': ['ramazan', 'ramazan_calismalari', 'ramadan'],
                'bayrak_çalışması': ['bayrak', 'bayrak_calismasi', 'flag']
            }
            
            loaded_activities = []
            
            for csv_file in csv_files:
                file_stem = csv_file.stem.lower()
                
                # Dosya adını aktivite adına çevir
                aktivite_adi = None
                for original_name, variations in known_mappings.items():
                    if any(var in file_stem for var in variations):
                        aktivite_adi = variations[0]  # İlk variation'ı kullan
                        break
                
                # Eğer bilinen bir aktivite değilse, dosya adını temizle
                if not aktivite_adi:
                    aktivite_adi = file_stem.replace(' ', '_').replace('ç', 'c').replace('ğ', 'g').replace('ı', 'i').replace('ö', 'o').replace('ş', 's').replace('ü', 'u')
                
                try:
                    df = pd.read_csv(csv_file, encoding='utf-8')
                    self.veriler[aktivite_adi] = df
                    loaded_activities.append(aktivite_adi)
                    print(f"✅ {aktivite_adi.title()} verisi yüklendi: {csv_file.name}")
                except Exception as e:
                    print(f"❌ {csv_file.name} verisi yüklenemedi: {e}")
            
            # Veri temizleme
            self._veri_temizle()
            
            # Eksik aktivitelerin katsayılarını yeniden dağıt
            self._katsayilari_yeniden_dagit()
            
            print(f"✅ {len(loaded_activities)} aktivite verisi yüklendi: {', '.join(loaded_activities)}")
            return len(loaded_activities) > 0
            
        except Exception as e:
            print(f"❌ Web veri yükleme hatası: {e}")
            return False
    
    def web_analiz_calistir(self):
        """Web uyumlu analiz"""
        try:
            print("🚀 Web Dinamik Analiz Başlatılıyor...")
            
            # Veri yükleme
            if not self.web_dinamik_veri_yukle():
                return {
                    'success': False,
                    'message': 'Veri yüklenemedi'
                }
            
            # Analiz adımları
            self.il_kategorileri_belirle()
            sonuclar = self.genel_puanlama_hesapla()
            
            # Raporları oluştur (session klasörüne)
            output_folder = os.path.join(self.data_folder, 'output_csv')
            os.makedirs(output_folder, exist_ok=True)
            
            # Geçici olarak çıktı klasörünü değiştir
            original_cwd = os.getcwd()
            os.chdir(self.data_folder)
            
            try:
                self.rapor_olustur()
            finally:
                os.chdir(original_cwd)
            
            # Sonuç özeti
            toplam_katsayi = sum(self.aktivite_katsayilari.values())
            aktivite_agirlikları = {}
            for aktivite, katsayi in self.aktivite_katsayilari.items():
                agirlik = (katsayi / toplam_katsayi) * 100
                aktivite_agirlikları[aktivite] = {
                    'coefficient': katsayi,
                    'weight_percentage': round(agirlik, 2)
                }
            
            return {
                'success': True,
                'message': 'Analiz başarıyla tamamlandı',
                'summary': {
                    'total_provinces': len(sonuclar),
                    'total_activities': len(self.aktivite_katsayilari),
                    'total_coefficient': toplam_katsayi,
                    'activity_weights': aktivite_agirlikları
                },
                'top_provinces': self._get_top_provinces(sonuclar, 10)
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Analiz hatası: {str(e)}'
            }
    
    def _get_top_provinces(self, sonuclar, limit=10):
        """En iyi illeri al"""
        sorted_provinces = sorted(
            sonuclar.items(),
            key=lambda x: x[1]['toplam_puan'],
            reverse=True
        )[:limit]
        
        return [
            {
                'province': il,
                'total_score': round(veri['toplam_puan'], 2),
                'category': veri['il_kategorisi'],
                'population': veri['nufus']
            }
            for il, veri in sorted_provinces
        ]

if __name__ == '__main__':
    # Production server for Render.com
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
